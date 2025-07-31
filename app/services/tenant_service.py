"""
Tenant service for multi-tenant isolation and management
"""
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from app.models.tenant import Tenant, TenantUser
from app.models.document import Document


class TenantService:
    """
    Service for managing tenant operations and ensuring data isolation
    """
    
    def __init__(self):
        pass
    
    def create_tenant(
        self,
        db: Session,
        name: str,
        subdomain: Optional[str] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-3.5-turbo"
    ) -> Tenant:
        """
        Create a new tenant with configuration
        """
        # Validate subdomain uniqueness if provided
        if subdomain:
            existing = db.query(Tenant).filter(
                Tenant.subdomain == subdomain
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subdomain already exists"
                )
        
        # Create tenant
        tenant = Tenant(
            name=name,
            subdomain=subdomain,
            llm_provider=llm_provider,
            llm_model=llm_model,
            is_active=True
        )
        
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        
        return tenant
    
    def get_tenant_by_id(self, db: Session, tenant_id: str) -> Optional[Tenant]:
        """
        Get tenant by ID with validation
        """
        tenant = db.query(Tenant).filter(
            and_(
                Tenant.id == tenant_id,
                Tenant.is_active == True
            )
        ).first()
        
        return tenant
    
    def get_tenant_by_subdomain(self, db: Session, subdomain: str) -> Optional[Tenant]:
        """
        Get tenant by subdomain
        """
        tenant = db.query(Tenant).filter(
            and_(
                Tenant.subdomain == subdomain,
                Tenant.is_active == True
            )
        ).first()
        
        return tenant
    
    def get_tenant_by_identifier(
        self, 
        db: Session, 
        identifier: str
    ) -> Optional[Tenant]:
        """
        Get tenant by ID or subdomain (flexible lookup)
        """
        # Try by UUID first
        try:
            tenant_uuid = uuid.UUID(identifier)
            return self.get_tenant_by_id(db, str(tenant_uuid))
        except ValueError:
            # If not a valid UUID, try subdomain
            return self.get_tenant_by_subdomain(db, identifier)
    
    def list_tenants(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[Tenant]:
        """
        List all tenants with pagination
        """
        query = db.query(Tenant)
        
        if active_only:
            query = query.filter(Tenant.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    def update_tenant(
        self,
        db: Session,
        tenant_id: str,
        updates: Dict[str, Any]
    ) -> Tenant:
        """
        Update tenant configuration
        """
        tenant = self.get_tenant_by_id(db, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Update allowed fields
        allowed_fields = {
            'name', 'subdomain', 'llm_provider', 'llm_model',
            'embedding_model', 'max_documents', 'max_queries_per_day'
        }
        
        for field, value in updates.items():
            if field in allowed_fields and hasattr(tenant, field):
                setattr(tenant, field, value)
        
        db.commit()
        db.refresh(tenant)
        
        return tenant
    
    def deactivate_tenant(self, db: Session, tenant_id: str) -> bool:
        """
        Deactivate tenant (soft delete)
        """
        tenant = self.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return False
        
        tenant.is_active = False
        db.commit()
        
        return True
    
    def get_tenant_stats(self, db: Session, tenant_id: str) -> Dict[str, Any]:
        """
        Get tenant statistics
        """
        tenant = self.get_tenant_by_id(db, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Count users
        user_count = db.query(TenantUser).filter(
            and_(
                TenantUser.tenant_id == tenant_id,
                TenantUser.is_active == True
            )
        ).count()
        
        # Count documents
        doc_count = db.query(Document).filter(
            Document.tenant_id == tenant_id
        ).count()
        
        # Count processed documents
        processed_doc_count = db.query(Document).filter(
            and_(
                Document.tenant_id == tenant_id,
                Document.status == "processed"
            )
        ).count()
        
        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "user_count": user_count,
            "document_count": doc_count,
            "processed_document_count": processed_doc_count,
            "created_at": tenant.created_at,
            "is_active": tenant.is_active,
            "configuration": {
                "llm_provider": tenant.llm_provider,
                "llm_model": tenant.llm_model,
                "embedding_model": tenant.embedding_model,
                "max_documents": tenant.max_documents,
                "max_queries_per_day": tenant.max_queries_per_day
            }
        }
    
    def validate_tenant_quota(
        self, 
        db: Session, 
        tenant_id: str, 
        quota_type: str,
        current_count: Optional[int] = None
    ) -> bool:
        """
        Validate tenant quotas (documents, queries, etc.)
        """
        tenant = self.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return False
        
        if quota_type == "documents":
            if current_count is None:
                current_count = db.query(Document).filter(
                    Document.tenant_id == tenant_id
                ).count()
            return current_count < tenant.max_documents
        
        # Add more quota types as needed
        return True
    
    def ensure_tenant_isolation(
        self, 
        db: Session, 
        user_tenant_id: str, 
        resource_tenant_id: str
    ) -> bool:
        """
        Ensure user can only access resources from their tenant
        """
        if user_tenant_id != resource_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: resource belongs to different tenant"
            )
        return True