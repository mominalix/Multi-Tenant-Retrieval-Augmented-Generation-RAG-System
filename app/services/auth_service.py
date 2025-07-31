"""
Authentication service for multi-tenant JWT authentication
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from app.models.tenant import Tenant, TenantUser
from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Authentication service handling JWT tokens and multi-tenant user management
    """
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expire_minutes = settings.jwt_expire_minutes
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        role: str,
        permissions: Optional[list] = None
    ) -> str:
        """
        Create JWT access token with tenant context
        """
        if permissions is None:
            permissions = []
            
        # Token payload with tenant context
        payload = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "email": email,
            "role": role,
            "permissions": permissions,
            "exp": datetime.utcnow() + timedelta(minutes=self.expire_minutes),
            "iat": datetime.utcnow(),
            "iss": settings.app_name,
            "type": "access_token"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token
        Returns token payload if valid
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("type") != "access_token":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    def authenticate_user(
        self, 
        db: Session, 
        email: str, 
        password: str,
        tenant_identifier: Optional[str] = None
    ) -> Optional[TenantUser]:
        """
        Authenticate user with email/password and optional tenant context
        """
        # Base query for user
        query = db.query(TenantUser).filter(TenantUser.email == email)
        
        # If tenant identifier provided, filter by tenant
        if tenant_identifier:
            query = query.join(Tenant).filter(
                and_(
                    Tenant.is_active == True,
                    # Support both subdomain and tenant ID
                    or_(
                        Tenant.subdomain == tenant_identifier,
                        Tenant.id == tenant_identifier
                    )
                )
            )
        
        user = query.first()
        
        if not user:
            return None
            
        if not self.verify_password(password, user.hashed_password):
            return None
            
        if not user.is_active:
            return None
            
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    def create_user(
        self,
        db: Session,
        tenant_id: str,
        email: str,
        username: str,
        password: str,
        role: str = "user"
    ) -> TenantUser:
        """
        Create new user in tenant
        """
        # Check if user already exists in this tenant
        existing_user = db.query(TenantUser).filter(
            and_(
                TenantUser.email == email,
                TenantUser.tenant_id == tenant_id
            )
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists in this tenant"
            )
        
        # Create new user
        hashed_password = self.hash_password(password)
        user = TenantUser(
            tenant_id=tenant_id,
            email=email,
            username=username,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
            email_verified=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_user_by_token(self, db: Session, token: str) -> TenantUser:
        """
        Get user from JWT token
        """
        payload = self.decode_token(token)
        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")
        
        if not user_id or not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = db.query(TenantUser).filter(
            and_(
                TenantUser.id == user_id,
                TenantUser.tenant_id == tenant_id,
                TenantUser.is_active == True
            )
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
    
    def validate_tenant_access(
        self, 
        db: Session, 
        token: str, 
        required_tenant_id: str
    ) -> bool:
        """
        Validate that token has access to specific tenant
        """
        payload = self.decode_token(token)
        token_tenant_id = payload.get("tenant_id")
        
        if token_tenant_id != required_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        
        return True
    
    def check_permission(
        self, 
        token: str, 
        required_permission: str
    ) -> bool:
        """
        Check if user has specific permission
        """
        payload = self.decode_token(token)
        permissions = payload.get("permissions", [])
        role = payload.get("role", "user")
        
        # Admin role has all permissions
        if role == "admin":
            return True
        
        return required_permission in permissions