"""
Authentication models for JWT integration.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class JWTClaims(BaseModel):
    """JWT claims extracted from token."""
    sub: str = Field(..., description="Subject (user ID)")
    iat: Optional[datetime] = Field(default=None, description="Issued at")
    exp: Optional[datetime] = Field(default=None, description="Expiration time")
    nbf: Optional[datetime] = Field(default=None, description="Not before")
    jti: Optional[str] = Field(default=None, description="JWT ID")
    
    # Custom claims from dsp_ai_jwt
    groups: List[str] = Field(default_factory=list, description="User groups")
    roles: List[str] = Field(default_factory=list, description="User roles")
    email: Optional[str] = Field(default=None, description="User email")
    
    # API key claims
    provider_permissions: List[str] = Field(default_factory=list, description="Allowed providers")
    endpoint_permissions: List[str] = Field(default_factory=list, description="Allowed endpoints")
    models: List[str] = Field(default_factory=list, description="Allowed models")
    rate_limit: Optional[int] = Field(default=None, description="Rate limit per minute")
    tier: Optional[str] = Field(default=None, description="User tier")
    
    # Metadata filter for RAG
    metadata_filter: Dict[str, Any] = Field(default_factory=dict, description="Metadata filter for documents")
    
    # Additional claims
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional claims")
    
    class Config:
        extra = "allow"


class TokenValidationRequest(BaseModel):
    """Request to validate a JWT token."""
    token: str = Field(..., description="JWT token to validate")
    skip_verification: bool = Field(default=False, description="Skip signature verification")
    secret: Optional[str] = Field(default=None, description="Custom secret for verification")


class TokenValidationResponse(BaseModel):
    """Response from token validation."""
    valid: bool = Field(..., description="Whether token is valid")
    expired: bool = Field(default=False, description="Whether token is expired")
    signature_verified: bool = Field(default=False, description="Whether signature was verified")
    claims: Optional[JWTClaims] = Field(default=None, description="Extracted claims")
    error: Optional[str] = Field(default=None, description="Error message")


class AuthenticatedUser(BaseModel):
    """Authenticated user context."""
    user_id: str = Field(..., description="User ID from JWT sub claim")
    groups: List[str] = Field(default_factory=list, description="User groups")
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: Dict[str, List[str]] = Field(default_factory=dict, description="User permissions")
    claims: JWTClaims = Field(..., description="Full JWT claims")
    
    def has_group(self, group: str) -> bool:
        """Check if user has a specific group."""
        return group in self.groups
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_group(self, groups: List[str]) -> bool:
        """Check if user has any of the specified groups."""
        return any(g in self.groups for g in groups)
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(r in self.roles for r in roles)
    
    def is_admin(self) -> bool:
        """Check if user is an administrator."""
        return self.has_any_group(["administrators", "admins"]) or self.has_role("admin")
