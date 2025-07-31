"""
FastAPI dependencies for authentication, tenant validation, and service injection
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tenant import TenantUser, Tenant
from app.services.auth_service import AuthService
from app.services.tenant_service import TenantService
from app.services.document_service import DocumentService
from app.services.vector_service import QdrantVectorService
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService

# Security scheme for JWT authentication
security = HTTPBearer(auto_error=False)


# Service dependencies (singletons)
def get_auth_service() -> AuthService:
    """Get authentication service instance"""
    return AuthService()


def get_tenant_service() -> TenantService:
    """Get tenant service instance"""
    return TenantService()


def get_document_service() -> DocumentService:
    """Get document service instance"""
    return DocumentService()


def get_vector_service() -> QdrantVectorService:
    """Get vector service instance"""
    return QdrantVectorService()


def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    return LLMService()


def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance"""
    return EmbeddingService()


# Authentication dependencies
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> TenantUser:
    """
    Get current authenticated user from JWT token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = auth_service.get_user_by_token(db, credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: TenantUser = Depends(get_current_user)
) -> TenantUser:
    """
    Get current active user (additional validation)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_tenant(
    current_user: TenantUser = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> Tenant:
    """
    Get current user's tenant with validation
    """
    tenant = tenant_service.get_tenant_by_id(db, str(current_user.tenant_id))
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is not active"
        )
    
    return tenant


# Tenant resolution dependencies
async def resolve_tenant_from_header(
    x_tenant_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> Optional[Tenant]:
    """
    Resolve tenant from X-Tenant-ID header (for public endpoints)
    """
    if not x_tenant_id:
        return None
    
    tenant = tenant_service.get_tenant_by_identifier(db, x_tenant_id)
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or inactive tenant"
        )
    
    return tenant


async def resolve_tenant_from_subdomain(
    request: Request,
    db: Session = Depends(get_db),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> Optional[Tenant]:
    """
    Resolve tenant from subdomain (for multi-tenant URLs)
    """
    host = request.headers.get("host", "")
    
    # Extract subdomain from host
    # Format: subdomain.yourdomain.com
    parts = host.split(".")
    if len(parts) < 3:
        return None
    
    subdomain = parts[0]
    tenant = tenant_service.get_tenant_by_subdomain(db, subdomain)
    
    if not tenant or not tenant.is_active:
        return None
    
    return tenant


# Role-based access dependencies
def require_admin_role(
    current_user: TenantUser = Depends(get_current_active_user)
) -> TenantUser:
    """
    Require admin role for endpoint access
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user


def require_user_or_admin_role(
    current_user: TenantUser = Depends(get_current_active_user)
) -> TenantUser:
    """
    Require user or admin role for endpoint access
    """
    if current_user.role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User or admin role required"
        )
    return current_user


# Tenant isolation validation
async def validate_tenant_access(
    resource_tenant_id: str,
    current_user: TenantUser = Depends(get_current_active_user),
    tenant_service: TenantService = Depends(get_tenant_service),
    db: Session = Depends(get_db)
) -> bool:
    """
    Validate that current user has access to resource from specific tenant
    """
    tenant_service.ensure_tenant_isolation(
        db, 
        str(current_user.tenant_id), 
        resource_tenant_id
    )
    return True


# Common type annotations for dependency injection
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
TenantServiceDep = Annotated[TenantService, Depends(get_tenant_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
VectorServiceDep = Annotated[QdrantVectorService, Depends(get_vector_service)]
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
EmbeddingServiceDep = Annotated[EmbeddingService, Depends(get_embedding_service)]

CurrentUserDep = Annotated[TenantUser, Depends(get_current_active_user)]
CurrentTenantDep = Annotated[Tenant, Depends(get_current_tenant)]
AdminUserDep = Annotated[TenantUser, Depends(require_admin_role)]
DatabaseDep = Annotated[Session, Depends(get_db)]