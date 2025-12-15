"""
FastAPI dependencies for authentication and authorization.
"""
import logging
from typing import Optional
from fastapi import Header, HTTPException, Depends, status

from ..services.auth_service import get_auth_service, AuthService
from ..models.auth import AuthenticatedUser

logger = logging.getLogger(__name__)


async def get_auth() -> AuthService:
    """Get the auth service."""
    return get_auth_service()


async def get_current_user(
    authorization: Optional[str] = Header(default=None, description="JWT Bearer token"),
    auth_service: AuthService = Depends(get_auth)
) -> AuthenticatedUser:
    """
    Dependency to get the current authenticated user from JWT token.
    Raises HTTPException if authentication fails.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    success, user, error = await auth_service.authenticate(authorization)
    
    if not success or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(default=None, description="JWT Bearer token"),
    auth_service: AuthService = Depends(get_auth)
) -> Optional[AuthenticatedUser]:
    """
    Dependency to optionally get the current authenticated user.
    Returns None if no token provided, raises HTTPException if token is invalid.
    """
    if not authorization:
        return None
    
    success, user, error = await auth_service.authenticate(authorization)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def require_admin(
    user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Dependency to require admin access.
    """
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return user


def require_groups(*groups: str):
    """
    Factory for dependency that requires specific group membership.
    """
    async def check_groups(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.has_any_group(list(groups)) and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required group membership: {list(groups)}"
            )
        return user
    return check_groups


def require_roles(*roles: str):
    """
    Factory for dependency that requires specific roles.
    """
    async def check_roles(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.has_any_role(list(roles)) and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {list(roles)}"
            )
        return user
    return check_roles
