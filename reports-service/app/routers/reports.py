"""
Reports API Router.

Provides endpoints for retrieving prosthesis usage reports from OLAP database.
All data is pre-aggregated by ETL process - no complex computations at runtime.
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models import (
    CurrentUser,
    ReportsListResponse,
    ReportDetailResponse,
    UserSummaryResponse,
    UserReportsList,
    DailyReport,
    UserSummary,
    ReportSummary,
    ErrorResponse,
)
from app.auth.jwt_handler import get_current_user
from app.services.clickhouse_service import get_clickhouse_service, ClickHouseService
from app.services.cache_service import get_cache_service, CacheService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


@router.get(
    "",
    response_model=ReportsListResponse,
    summary="Get list of available reports",
    description="""
    Returns a list of available daily reports for the authenticated user.

    Reports are pre-aggregated by the ETL pipeline and retrieved directly from
    the OLAP database without additional computation.

    **Security:** User can only access their own reports.
    **Caching:** Results are cached for 5 minutes.
    """,
)
async def get_reports_list(
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = Query(30, ge=1, le=100, description="Maximum reports to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    clickhouse: ClickHouseService = Depends(get_clickhouse_service),
    cache: CacheService = Depends(get_cache_service),
) -> ReportsListResponse:
    """Get list of available reports for the current user."""

    user_id = current_user.user_id
    logger.info(f"Fetching reports list for user: {user_id}")

    # Try cache first (only for default pagination)
    if limit == 30 and offset == 0:
        cached = cache.get_reports_list(user_id)
        if cached:
            logger.debug(f"Returning cached reports list for user: {user_id}")
            return ReportsListResponse(
                data=UserReportsList(
                    user_id=cached["user_id"],
                    customer_name=cached["customer_name"],
                    prosthesis_model=cached["prosthesis_model"],
                    total_reports=cached["total_reports"],
                    date_range=cached["date_range"],
                    reports=[ReportSummary(**r) for r in cached["reports"]],
                )
            )

    # Query ClickHouse
    try:
        data = clickhouse.get_reports_list(user_id, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"ClickHouse error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No reports found for user {user_id}"
        )

    # Cache if default pagination
    if limit == 30 and offset == 0:
        cache.set_reports_list(user_id, data)

    return ReportsListResponse(
        data=UserReportsList(
            user_id=data["user_id"],
            customer_name=data["customer_name"],
            prosthesis_model=data["prosthesis_model"],
            total_reports=data["total_reports"],
            date_range=data["date_range"],
            reports=[ReportSummary(**r) for r in data["reports"]],
        )
    )


@router.get(
    "/summary",
    response_model=UserSummaryResponse,
    summary="Get user summary",
    description="""
    Returns an overall summary of prosthesis usage across all time.

    Includes total movements, success rates, and activity statistics.

    **Security:** User can only access their own summary.
    **Caching:** Results are cached for 5 minutes.
    """,
)
async def get_user_summary(
    current_user: CurrentUser = Depends(get_current_user),
    clickhouse: ClickHouseService = Depends(get_clickhouse_service),
    cache: CacheService = Depends(get_cache_service),
) -> UserSummaryResponse:
    """Get overall summary for the current user."""

    user_id = current_user.user_id
    logger.info(f"Fetching user summary for: {user_id}")

    # Try cache first
    cached = cache.get_user_summary(user_id)
    if cached:
        logger.debug(f"Returning cached summary for user: {user_id}")
        return UserSummaryResponse(data=UserSummary(**cached))

    # Query ClickHouse
    try:
        data = clickhouse.get_user_summary(user_id)
    except Exception as e:
        logger.error(f"ClickHouse error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for user {user_id}"
        )

    # Cache result
    cache.set_user_summary(user_id, data)

    return UserSummaryResponse(data=UserSummary(**data))


@router.get(
    "/{report_date}",
    response_model=ReportDetailResponse,
    summary="Get daily report",
    description="""
    Returns a detailed daily report for a specific date.

    Includes hourly breakdown of prosthesis usage metrics.

    **Security:** User can only access their own reports.
    **Caching:** Results are cached for 5 minutes.
    """,
)
async def get_daily_report(
    report_date: date,
    current_user: CurrentUser = Depends(get_current_user),
    include_hourly: bool = Query(True, description="Include hourly breakdown"),
    clickhouse: ClickHouseService = Depends(get_clickhouse_service),
    cache: CacheService = Depends(get_cache_service),
) -> ReportDetailResponse:
    """Get detailed daily report for a specific date."""

    user_id = current_user.user_id
    logger.info(f"Fetching daily report for user: {user_id}, date: {report_date}")

    # Try cache first
    cached = cache.get_daily_report(user_id, report_date)
    if cached:
        logger.debug(f"Returning cached daily report for user: {user_id}, date: {report_date}")
        return ReportDetailResponse(data=DailyReport(**cached))

    # Query ClickHouse
    try:
        data = clickhouse.get_daily_report(user_id, report_date, include_hourly=include_hourly)
    except Exception as e:
        logger.error(f"ClickHouse error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for user {user_id} on {report_date}"
        )

    # Cache result
    cache.set_daily_report(user_id, report_date, data)

    return ReportDetailResponse(data=DailyReport(**data))


@router.delete(
    "/cache",
    summary="Clear user cache",
    description="Clears all cached reports for the current user.",
)
async def clear_cache(
    current_user: CurrentUser = Depends(get_current_user),
    cache: CacheService = Depends(get_cache_service),
) -> dict:
    """Clear cached reports for the current user."""

    user_id = current_user.user_id
    deleted = cache.invalidate_user_cache(user_id)
    logger.info(f"Cleared {deleted} cache entries for user: {user_id}")

    return {"success": True, "message": f"Cleared {deleted} cache entries"}
