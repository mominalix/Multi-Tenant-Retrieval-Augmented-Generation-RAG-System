"""
Authentication and tenant-related Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


# User schemas
class UserCreate(BaseModel):
    """Schema for creating new user"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: str = Field(default="user")


class OrganizationSignup(BaseModel):
    """Schema for organization signup (creates tenant and admin user)"""
    # Organization (Tenant) Information
    organization_name: str = Field(..., min_length=2, max_length=255, description="Organization name")
    subdomain: Optional[str] = Field(None, pattern=r"^[a-z0-9-]+$", max_length=63, description="Optional subdomain for organization")
    
    # Admin User Information
    admin_email: EmailStr = Field(..., description="Admin user email")
    admin_username: str = Field(..., min_length=3, max_length=50, description="Admin username")
    admin_password: str = Field(..., min_length=8, description="Admin password")
    
    # Optional Configuration
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_model: str = Field(default="gpt-3.5-turbo", description="LLM model")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    tenant_identifier: Optional[str] = None  # subdomain or tenant_id


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    email: str
    username: str
    role: str
    is_active: bool
    email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    tenant_id: UUID
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    tenant: "TenantResponse"


class OrganizationSignupResponse(BaseModel):
    """Schema for organization signup response"""
    message: str
    tenant: "TenantResponse"
    admin_user: UserResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Tenant schemas
class TenantCreate(BaseModel):
    """Schema for creating new tenant"""
    name: str = Field(..., min_length=2, max_length=255)
    subdomain: Optional[str] = Field(None, pattern=r"^[a-z0-9-]+$", max_length=63)
    llm_provider: str = Field(default="openai")
    llm_model: str = Field(default="gpy-4.1-nano")


class TenantUpdate(BaseModel):
    """Schema for updating tenant"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    subdomain: Optional[str] = Field(None, pattern=r"^[a-z0-9-]+$", max_length=63)
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    max_documents: Optional[int] = Field(None, gt=0)
    max_queries_per_day: Optional[int] = Field(None, gt=0)


class TenantResponse(BaseModel):
    """Schema for tenant response"""
    id: UUID
    name: str
    subdomain: Optional[str]
    llm_provider: str
    llm_model: str
    embedding_model: str
    max_documents: int
    max_queries_per_day: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TenantStats(BaseModel):
    """Schema for tenant statistics"""
    tenant_id: UUID
    tenant_name: str
    user_count: int
    document_count: int
    processed_document_count: int
    created_at: datetime
    is_active: bool
    configuration: Dict[str, Any]


# Update TokenResponse to avoid circular import
TokenResponse.model_rebuild()