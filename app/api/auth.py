"""
Authentication and user management API routes
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    TenantCreate, TenantResponse, TenantUpdate, TenantStats
)
from app.dependencies import (
    get_db, get_auth_service, get_tenant_service,
    get_current_active_user, require_admin_role,
    CurrentUserDep, AdminUserDep, DatabaseDep,
    AuthServiceDep, TenantServiceDep
)
from app.models.tenant import TenantUser, Tenant
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    tenant_id: str,
    db: DatabaseDep,
    auth_service: AuthServiceDep,
    tenant_service: TenantServiceDep
):
    """
    Register a new user in a specific tenant
    """
    try:
        # Validate tenant exists and is active
        tenant = tenant_service.get_tenant_by_id(db, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Create user
        user = auth_service.create_user(
            db=db,
            tenant_id=tenant_id,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            role=user_data.role
        )
        
        logger.info(f"User registered: {user.email} in tenant {tenant_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: DatabaseDep,
    auth_service: AuthServiceDep
):
    """
    Authenticate user and return JWT token with tenant context
    """
    try:
        # Authenticate user
        user = auth_service.authenticate_user(
            db=db,
            email=login_data.email,
            password=login_data.password,
            tenant_identifier=login_data.tenant_identifier
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Get user permissions (could be extended based on role)
        permissions = []
        if user.role == "admin":
            permissions = ["read", "write", "delete", "manage"]
        elif user.role == "user":
            permissions = ["read", "write"]
        else:
            permissions = ["read"]
        
        # Create access token
        access_token = auth_service.create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            role=user.role,
            permissions=permissions
        )
        
        # Get tenant info for response
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        
        logger.info(f"User logged in: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
            user=UserResponse.model_validate(user),
            tenant=TenantResponse.model_validate(tenant)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUserDep
):
    """
    Get current authenticated user information
    """
    return current_user


@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    admin_user: AdminUserDep,
    db: DatabaseDep,
    tenant_service: TenantServiceDep
):
    """
    Create a new tenant (admin only)
    """
    try:
        tenant = tenant_service.create_tenant(
            db=db,
            name=tenant_data.name,
            subdomain=tenant_data.subdomain,
            llm_provider=tenant_data.llm_provider,
            llm_model=tenant_data.llm_model
        )
        
        logger.info(f"Tenant created: {tenant.name} by {admin_user.email}")
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tenant creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant creation failed"
        )


@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(
    admin_user: AdminUserDep,
    db: DatabaseDep,
    tenant_service: TenantServiceDep,
    skip: int = 0,
    limit: int = 100
):
    """
    List all tenants (admin only)
    """
    tenants = tenant_service.list_tenants(db, skip=skip, limit=limit)
    return tenants


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    admin_user: AdminUserDep,
    db: DatabaseDep,
    tenant_service: TenantServiceDep
):
    """
    Get tenant by ID (admin only)
    """
    tenant = tenant_service.get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return tenant


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    admin_user: AdminUserDep,
    db: DatabaseDep,
    tenant_service: TenantServiceDep
):
    """
    Update tenant configuration (admin only)
    """
    try:
        # Convert to dict and remove None values
        update_data = {
            k: v for k, v in tenant_update.dict().items() 
            if v is not None
        }
        
        tenant = tenant_service.update_tenant(
            db=db,
            tenant_id=tenant_id,
            updates=update_data
        )
        
        logger.info(f"Tenant updated: {tenant_id} by {admin_user.email}")
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tenant update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant update failed"
        )


@router.delete("/tenants/{tenant_id}")
async def deactivate_tenant(
    tenant_id: str,
    admin_user: AdminUserDep,
    db: DatabaseDep,
    tenant_service: TenantServiceDep
):
    """
    Deactivate tenant (admin only)
    """
    try:
        success = tenant_service.deactivate_tenant(db, tenant_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        logger.warning(f"Tenant deactivated: {tenant_id} by {admin_user.email}")
        return {"message": "Tenant deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tenant deactivation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant deactivation failed"
        )


@router.get("/tenants/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_stats(
    tenant_id: str,
    admin_user: AdminUserDep,
    db: DatabaseDep,
    tenant_service: TenantServiceDep
):
    """
    Get tenant statistics (admin only)
    """
    try:
        stats = tenant_service.get_tenant_stats(db, tenant_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant statistics"
        )


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    current_user: CurrentUserDep,
    db: DatabaseDep,
    auth_service: AuthServiceDep
):
    """
    Refresh JWT token for current user
    """
    try:
        # Get user permissions
        permissions = []
        if current_user.role == "admin":
            permissions = ["read", "write", "delete", "manage"]
        elif current_user.role == "user":
            permissions = ["read", "write"]
        else:
            permissions = ["read"]
        
        # Create new access token
        access_token = auth_service.create_access_token(
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            email=current_user.email,
            role=current_user.role,
            permissions=permissions
        )
        
        # Get tenant info
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
            user=UserResponse.model_validate(current_user),
            tenant=TenantResponse.model_validate(tenant)
        )
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )