import os
import secrets
import hashlib
import base64
import json
import time
from functools import wraps
from flask import Flask, request, jsonify, redirect, make_response
import redis
import requests
from cryptography.fernet import Fernet

app = Flask(__name__)

# Configuration
KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'http://keycloak:8080')
KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM', 'reports-realm')
CLIENT_ID = os.getenv('CLIENT_ID', 'reports-frontend')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:8000/auth/callback')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
SESSION_COOKIE_NAME = 'BIONICPRO_SESSION'
SESSION_LIFETIME = 3600  # 1 hour - longer than access_token (2 min)
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())

# Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Encryption for refresh tokens
fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)


def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge."""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    return code_verifier, code_challenge


def generate_session_id():
    """Generate a secure session ID."""
    return secrets.token_urlsafe(32)


def encrypt_token(token):
    """Encrypt a token for secure storage."""
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token):
    """Decrypt a stored token."""
    return fernet.decrypt(encrypted_token.encode()).decode()


def get_session_data(session_id):
    """Get session data from Redis."""
    data = redis_client.get(f"session:{session_id}")
    if data:
        return json.loads(data)
    return None


def save_session_data(session_id, data, ttl=SESSION_LIFETIME):
    """Save session data to Redis."""
    redis_client.setex(f"session:{session_id}", ttl, json.dumps(data))


def delete_session(session_id):
    """Delete a session from Redis."""
    redis_client.delete(f"session:{session_id}")


def create_session_cookie(response, session_id):
    """Create HTTP-only, Secure session cookie."""
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        httponly=True,
        secure=os.getenv('SECURE_COOKIES', 'false').lower() == 'true',
        samesite='Lax',
        max_age=SESSION_LIFETIME
    )
    return response


def get_keycloak_openid_config():
    """Get Keycloak OpenID configuration."""
    url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"
    response = requests.get(url)
    return response.json()


def exchange_code_for_tokens(code, code_verifier):
    """Exchange authorization code for tokens using PKCE."""
    config = get_keycloak_openid_config()
    token_endpoint = config['token_endpoint']

    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier
    }

    response = requests.post(token_endpoint, data=data)
    if response.status_code == 200:
        return response.json()
    return None


def refresh_access_token(refresh_token):
    """Refresh access token using refresh token."""
    config = get_keycloak_openid_config()
    token_endpoint = config['token_endpoint']

    data = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'refresh_token': refresh_token
    }

    response = requests.post(token_endpoint, data=data)
    if response.status_code == 200:
        return response.json()
    return None


def rotate_session(old_session_id, session_data):
    """Rotate session ID to prevent session fixation attacks."""
    new_session_id = generate_session_id()

    # Delete old session
    delete_session(old_session_id)

    # Save data with new session ID
    save_session_data(new_session_id, session_data)

    return new_session_id


def require_session(f):
    """Decorator to require valid session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_id:
            return jsonify({'error': 'No session'}), 401

        session_data = get_session_data(session_id)
        if not session_data:
            return jsonify({'error': 'Invalid session'}), 401

        # Check if access token needs refresh
        if session_data.get('access_token_expires_at', 0) < time.time():
            try:
                refresh_token = decrypt_token(session_data['encrypted_refresh_token'])
                tokens = refresh_access_token(refresh_token)

                if tokens:
                    session_data['access_token'] = tokens['access_token']
                    session_data['access_token_expires_at'] = time.time() + tokens.get('expires_in', 120)

                    if 'refresh_token' in tokens:
                        session_data['encrypted_refresh_token'] = encrypt_token(tokens['refresh_token'])
                else:
                    # Refresh failed, session is invalid
                    delete_session(session_id)
                    return jsonify({'error': 'Session expired'}), 401
            except Exception as e:
                delete_session(session_id)
                return jsonify({'error': 'Session expired'}), 401

        # Session rotation for session fixation prevention
        new_session_id = rotate_session(session_id, session_data)

        # Store session data in request context
        request.session_data = session_data
        request.new_session_id = new_session_id

        return f(*args, **kwargs)
    return decorated_function


@app.route('/auth/login', methods=['GET'])
def login():
    """Initiate OAuth2 PKCE login flow."""
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(32)

    # Store PKCE verifier and state temporarily
    redis_client.setex(f"pkce:{state}", 300, code_verifier)

    config = get_keycloak_openid_config()
    auth_endpoint = config['authorization_endpoint']

    auth_url = (
        f"{auth_endpoint}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid profile email&"
        f"state={state}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256"
    )

    return redirect(auth_url)


@app.route('/auth/callback', methods=['GET'])
def callback():
    """Handle OAuth2 callback and exchange code for tokens."""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    if error:
        return redirect(f"{FRONTEND_URL}?error={error}")

    if not code or not state:
        return redirect(f"{FRONTEND_URL}?error=missing_params")

    # Retrieve PKCE verifier
    code_verifier = redis_client.get(f"pkce:{state}")
    redis_client.delete(f"pkce:{state}")

    if not code_verifier:
        return redirect(f"{FRONTEND_URL}?error=invalid_state")

    # Exchange code for tokens
    tokens = exchange_code_for_tokens(code, code_verifier)

    if not tokens:
        return redirect(f"{FRONTEND_URL}?error=token_exchange_failed")

    # Create session
    session_id = generate_session_id()
    session_data = {
        'access_token': tokens['access_token'],
        'access_token_expires_at': time.time() + tokens.get('expires_in', 120),
        'encrypted_refresh_token': encrypt_token(tokens['refresh_token']),
        'id_token': tokens.get('id_token'),
        'created_at': time.time()
    }

    save_session_data(session_id, session_data)

    # Create response with session cookie
    response = make_response(redirect(FRONTEND_URL))
    create_session_cookie(response, session_id)

    return response


@app.route('/auth/logout', methods=['POST'])
def logout():
    """Logout and invalidate session."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_id:
        session_data = get_session_data(session_id)

        if session_data:
            # Logout from Keycloak
            try:
                config = get_keycloak_openid_config()
                logout_endpoint = config.get('end_session_endpoint')

                if logout_endpoint and session_data.get('id_token'):
                    requests.get(
                        logout_endpoint,
                        params={'id_token_hint': session_data['id_token']}
                    )
            except Exception:
                pass

        delete_session(session_id)

    response = make_response(jsonify({'status': 'logged_out'}))
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.route('/auth/session', methods=['GET'])
@require_session
def get_session():
    """Get current session info (without exposing tokens)."""
    session_data = request.session_data
    new_session_id = request.new_session_id

    # Decode ID token to get user info (without exposing actual tokens)
    user_info = {}
    if session_data.get('id_token'):
        try:
            # Decode JWT payload (without verification - just for display)
            payload = session_data['id_token'].split('.')[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            user_info = json.loads(base64.urlsafe_b64decode(payload))
        except Exception:
            pass

    response = make_response(jsonify({
        'authenticated': True,
        'user': {
            'sub': user_info.get('sub'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'preferred_username': user_info.get('preferred_username'),
            'given_name': user_info.get('given_name'),
            'family_name': user_info.get('family_name')
        }
    }))

    # Update session cookie with rotated session ID
    create_session_cookie(response, new_session_id)

    return response


@app.route('/api/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@require_session
def api_proxy(path):
    """Proxy API requests with access token injection."""
    session_data = request.session_data
    new_session_id = request.new_session_id
    access_token = session_data['access_token']

    # Build target URL (configure API_GATEWAY_URL as needed)
    api_gateway_url = os.getenv('API_GATEWAY_URL', 'http://api-gateway:8080')
    target_url = f"{api_gateway_url}/{path}"

    # Forward request with access token
    headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'cookie']}
    headers['Authorization'] = f'Bearer {access_token}'

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            timeout=30
        )

        response = make_response(resp.content, resp.status_code)

        # Copy response headers except those that might conflict
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        for key, value in resp.headers.items():
            if key.lower() not in excluded_headers:
                response.headers[key] = value

        # Update session cookie with rotated session ID
        create_session_cookie(response, new_session_id)

        return response
    except requests.exceptions.RequestException as e:
        response = make_response(jsonify({'error': 'API request failed'}), 502)
        create_session_cookie(response, new_session_id)
        return response


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        redis_client.ping()
        redis_status = 'healthy'
    except Exception:
        redis_status = 'unhealthy'

    return jsonify({
        'status': 'healthy',
        'redis': redis_status
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=os.getenv('DEBUG', 'false').lower() == 'true')
