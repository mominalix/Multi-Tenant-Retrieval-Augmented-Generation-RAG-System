"""
Tenant information API routes
"""
import logging
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.auth import TenantResponse, TenantStats
from app.dependencies import (
    CurrentUserDep, CurrentTenantDep, DatabaseDep, TenantServiceDep
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenant", tags=["Tenant Info"])


@router.get("/info", response_model=TenantResponse)
async def get_current_tenant_info(
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep
):
    """
    Get current tenant information
    """
    return current_tenant


@router.get("/stats", response_model=TenantStats)
async def get_current_tenant_stats(
    current_user: CurrentUserDep,
    current_tenant: CurrentTenantDep,
    db: DatabaseDep,
    tenant_service: TenantServiceDep
):
    """
    Get statistics for current tenant
    """
    try:
        stats = tenant_service.get_tenant_stats(db, str(current_tenant.id))
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get tenant stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant statistics"
        )