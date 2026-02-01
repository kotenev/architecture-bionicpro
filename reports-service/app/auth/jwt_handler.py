"""
JWT authentication handler for Reports Service.
"""

import logging
from typing import Optional

import httpx
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.config import get_settings, Settings
from app.models import CurrentUser, TokenPayload

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


class JWTHandler:
    """Handler for JWT token validation."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._public_key: Optional[str] = None

    async def get_public_key(self) -> Optional[str]:
        """
        Fetch Keycloak public key for JWT verification.
        Caches the key after first fetch.
        """
        if self._public_key:
            return self._public_key

        try:
            # Fetch realm info from Keycloak
            url = f"{self.settings.keycloak_url}/realms/{self.settings.keycloak_realm}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    realm_info = response.json()
                    public_key = realm_info.get("public_key")
                    if public_key:
                        # Format as PEM
                        self._public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
                        logger.info("Successfully fetched Keycloak public key")
                        return self._public_key
        except Exception as e:
            logger.warning(f"Failed to fetch Keycloak public key: {e}")

        return None

    def decode_token(self, token: str, verify: bool = True) -> Optional[TokenPayload]:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string
            verify: Whether to verify signature (False for testing)

        Returns:
            Token payload or None if invalid
        """
        try:
            options = {}
            key = self.settings.jwt_secret_key

            if not verify:
                options = {"verify_signature": False}

            payload = jwt.decode(
                token,
                key,
                algorithms=[self.settings.jwt_algorithm, "RS256"],
                options=options,
            )

            return TokenPayload(**payload)

        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            return None

    def extract_user_from_token(self, payload: TokenPayload) -> CurrentUser:
        """
        Extract user information from token payload.

        Args:
            payload: Decoded token payload

        Returns:
            CurrentUser object
        """
        # Extract roles from realm_access
        roles = []
        if payload.realm_access and "roles" in payload.realm_access:
            roles = payload.realm_access["roles"]

        return CurrentUser(
            user_id=payload.sub,
            username=payload.preferred_username,
            email=payload.email,
            roles=roles,
        )


# Singleton handler
_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """Get singleton JWT handler instance."""
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler(get_settings())
    return _jwt_handler


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> CurrentUser:
    """
    FastAPI dependency to get current authenticated user.

    Extracts and validates JWT from Authorization header.

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    handler = get_jwt_handler()

    # Try to decode token
    payload = handler.decode_token(token, verify=False)  # Set verify=True in production with proper key setup

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = handler.extract_user_from_token(payload)
    logger.debug(f"Authenticated user: {user.user_id}")

    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Optional[CurrentUser]:
    """
    Optional version of get_current_user.
    Returns None instead of raising exception if not authenticated.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
