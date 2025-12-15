"""
JWT Authentication service integrating with dsp_ai_jwt.
"""
import logging
from typing import Optional, Tuple
import httpx
import jwt
from datetime import datetime, timezone

from ..config import Settings, get_settings
from ..models.auth import JWTClaims, AuthenticatedUser, TokenValidationResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Service for JWT authentication and authorization."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for JWT service communication."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.settings.jwt_service_url,
                timeout=30.0
            )
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    def decode_token_local(self, token: str, verify: bool = True) -> Tuple[bool, Optional[JWTClaims], Optional[str]]:
        """
        Decode and validate JWT token locally.
        
        Args:
            token: JWT token string
            verify: Whether to verify signature
            
        Returns:
            Tuple of (success, claims, error_message)
        """
        try:
            options = {"verify_signature": verify}
            if not verify:
                options["verify_exp"] = False
            
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                options=options
            )
            
            # Convert timestamps to datetime
            claims_data = dict(payload)
            if "iat" in claims_data and isinstance(claims_data["iat"], (int, float)):
                claims_data["iat"] = datetime.fromtimestamp(claims_data["iat"], tz=timezone.utc)
            if "exp" in claims_data and isinstance(claims_data["exp"], (int, float)):
                claims_data["exp"] = datetime.fromtimestamp(claims_data["exp"], tz=timezone.utc)
            if "nbf" in claims_data and isinstance(claims_data["nbf"], (int, float)):
                claims_data["nbf"] = datetime.fromtimestamp(claims_data["nbf"], tz=timezone.utc)
            
            # Extract known claims and put rest in extra
            known_fields = set(JWTClaims.model_fields.keys()) - {"extra"}
            extra = {k: v for k, v in claims_data.items() if k not in known_fields}
            claims_data["extra"] = extra
            
            claims = JWTClaims(**claims_data)
            return True, claims, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return False, None, f"Token decode error: {str(e)}"
    
    async def validate_token_remote(self, token: str) -> TokenValidationResponse:
        """
        Validate JWT token using the remote JWT service.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenValidationResponse with validation results
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/validate",
                json={"token": token}
            )
            data = response.json()
            
            if data.get("valid"):
                # Decode to get full claims
                success, claims, error = self.decode_token_local(token, verify=False)
                return TokenValidationResponse(
                    valid=True,
                    expired=data.get("expired", False),
                    signature_verified=data.get("signature_verified", True),
                    claims=claims,
                    error=None
                )
            else:
                return TokenValidationResponse(
                    valid=False,
                    expired=data.get("expired", False),
                    signature_verified=data.get("signature_verified", False),
                    claims=None,
                    error=data.get("error", "Validation failed")
                )
                
        except httpx.RequestError as e:
            logger.warning(f"Remote validation failed, falling back to local: {e}")
            # Fall back to local validation
            success, claims, error = self.decode_token_local(token)
            return TokenValidationResponse(
                valid=success,
                expired=False,
                signature_verified=success,
                claims=claims,
                error=error
            )
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return TokenValidationResponse(
                valid=False,
                expired=False,
                signature_verified=False,
                claims=None,
                error=str(e)
            )
    
    async def authenticate(self, token: str) -> Tuple[bool, Optional[AuthenticatedUser], Optional[str]]:
        """
        Authenticate a request using JWT token.
        
        Args:
            token: JWT token (with or without "Bearer " prefix)
            
        Returns:
            Tuple of (success, authenticated_user, error_message)
        """
        # Remove Bearer prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # First try local validation
        success, claims, error = self.decode_token_local(token)
        
        if not success:
            # Try remote validation as fallback
            validation = await self.validate_token_remote(token)
            if validation.valid and validation.claims:
                success = True
                claims = validation.claims
                error = None
            else:
                return False, None, validation.error or error
        
        if not claims:
            return False, None, "No claims extracted from token"
        
        # Build authenticated user
        user = AuthenticatedUser(
            user_id=claims.sub,
            groups=claims.groups,
            roles=claims.roles,
            permissions={
                "providers": claims.provider_permissions,
                "endpoints": claims.endpoint_permissions,
                "models": claims.models,
            },
            claims=claims
        )
        
        return True, user, None
    
    def check_access(
        self,
        user: AuthenticatedUser,
        required_groups: Optional[list] = None,
        required_roles: Optional[list] = None,
        require_admin: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has required access.
        
        Args:
            user: Authenticated user
            required_groups: List of groups (any match)
            required_roles: List of roles (any match)
            require_admin: Whether admin access is required
            
        Returns:
            Tuple of (has_access, error_message)
        """
        if require_admin and not user.is_admin():
            return False, "Administrator access required"
        
        if required_groups and not user.has_any_group(required_groups):
            return False, f"Required group membership: {required_groups}"
        
        if required_roles and not user.has_any_role(required_roles):
            return False, f"Required role: {required_roles}"
        
        return True, None


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the auth service singleton."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
