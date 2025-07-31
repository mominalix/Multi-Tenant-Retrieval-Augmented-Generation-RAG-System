"""
Tenant-related database models
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base


class Tenant(Base):
    """
    Tenant model for multi-tenant isolation
    Each tenant represents an organization/company using the RAG system
    """
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    subdomain = Column(String(63), unique=True, nullable=True, index=True)
    
    # Configuration
    llm_provider = Column(String(50), default="openai")
    llm_model = Column(String(100), default="gpt-3.5-turbo")
    embedding_model = Column(String(100), default="sentence-transformers/all-MiniLM-L6-v2")
    max_documents = Column(Integer, default=1000)
    max_queries_per_day = Column(Integer, default=10000)
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}')>"


class TenantUser(Base):
    """
    User model with tenant association
    Supports multi-tenant authentication and role-based access
    """
    __tablename__ = "tenant_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # User Information
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Role and Permissions
    role = Column(String(50), default="user")  # admin, user, viewer
    permissions = Column(Text)  # JSON string of permissions
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TenantUser(id={self.id}, email='{self.email}', tenant_id={self.tenant_id})>"