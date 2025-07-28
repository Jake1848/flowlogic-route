from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from ..auth.firebase_auth import firebase_auth
from ..auth.api_keys import api_key_manager
from ..database.database import get_db
from ..database.models import User, Subscription
from .rate_limiting import rate_limiter, usage_limiter, create_rate_limit_response, create_usage_limit_response

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class AuthContext:
    """Authentication context for requests"""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        firebase_uid: Optional[str] = None,
        api_key_id: Optional[str] = None,
        is_admin: bool = False,
        subscription_tier: str = "free",
        auth_method: str = "api_key"
    ):
        self.user_id = user_id
        self.email = email
        self.firebase_uid = firebase_uid
        self.api_key_id = api_key_id
        self.is_admin = is_admin
        self.subscription_tier = subscription_tier
        self.auth_method = auth_method


async def authenticate_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AuthContext:
    """
    Authenticate incoming request using either Firebase token or API key
    
    Priority order:
    1. API Key in Authorization header (Bearer api_key)
    2. API Key in X-API-Key header
    3. Firebase ID token in Authorization header (Bearer token)
    """
    
    # Extract authentication tokens
    auth_header = request.headers.get("authorization")
    api_key_header = request.headers.get("x-api-key")
    
    # Try API key authentication first
    api_key = None
    if credentials and credentials.credentials.startswith("fl_"):
        api_key = credentials.credentials
    elif api_key_header:
        api_key = api_key_header
    elif auth_header and auth_header.startswith("Bearer fl_"):
        api_key = auth_header.replace("Bearer ", "")
    
    if api_key:
        return await authenticate_with_api_key(request, api_key, db)
    
    # Try Firebase token authentication
    if credentials and not credentials.credentials.startswith("fl_"):
        return await authenticate_with_firebase(request, credentials.credentials, db)
    
    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either API key or Firebase token."
    )


async def authenticate_with_api_key(
    request: Request,
    api_key: str,
    db: Session
) -> AuthContext:
    """Authenticate using API key"""
    try:
        # Validate API key
        key_info = await api_key_manager.validate_api_key(db, api_key)
        
        if not key_info:
            logger.warning(f"Invalid API key from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check IP restrictions
        allowed_ips = key_info.get("allowed_ips")
        if allowed_ips and request.client.host not in allowed_ips:
            logger.warning(f"API key used from unauthorized IP: {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP address not authorized for this API key"
            )
        
        # Check rate limits
        identifier = f"api_key:{key_info['api_key_id']}"
        rate_limit_override = key_info.get("rate_limit_override")
        
        allowed, rate_info = await rate_limiter.check_rate_limit(
            identifier=identifier,
            tier=key_info["subscription_tier"],
            override=rate_limit_override
        )
        
        if not allowed:
            raise create_rate_limit_response(rate_info)
        
        # Add rate limit headers to response
        request.state.rate_limit_info = rate_info
        
        return AuthContext(
            user_id=key_info["user_id"],
            email=key_info["user_email"],
            firebase_uid=key_info["firebase_uid"],
            api_key_id=key_info["api_key_id"],
            is_admin=key_info["is_admin"],
            subscription_tier=key_info["subscription_tier"],
            auth_method="api_key"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


async def authenticate_with_firebase(
    request: Request,
    id_token: str,
    db: Session
) -> AuthContext:
    """Authenticate using Firebase ID token"""
    try:
        # Verify Firebase token
        user_claims = await firebase_auth.verify_token(id_token)
        
        # Find user in database
        user = db.query(User).filter(
            User.firebase_uid == user_claims["uid"]
        ).first()
        
        if not user:
            # Auto-create user if not exists (first-time login)
            user = await create_user_from_firebase(db, user_claims)
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        # Get subscription tier
        subscription_tier = "free"
        if user.subscription:
            subscription_tier = user.subscription.tier
        
        # Check rate limits for Firebase auth
        identifier = f"user:{user.id}"
        allowed, rate_info = await rate_limiter.check_rate_limit(
            identifier=identifier,
            tier=subscription_tier
        )
        
        if not allowed:
            raise create_rate_limit_response(rate_info)
        
        request.state.rate_limit_info = rate_info
        
        return AuthContext(
            user_id=str(user.id),
            email=user.email,
            firebase_uid=user.firebase_uid,
            is_admin=user.is_admin,
            subscription_tier=subscription_tier,
            auth_method="firebase"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Firebase authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


async def create_user_from_firebase(
    db: Session,
    user_claims: Dict[str, Any]
) -> User:
    """Create new user from Firebase claims"""
    try:
        # Create user
        user = User(
            firebase_uid=user_claims["uid"],
            email=user_claims["email"],
            display_name=user_claims.get("name"),
            email_verified=user_claims.get("email_verified", False),
            phone_number=user_claims.get("phone_number")
        )
        
        db.add(user)
        db.flush()  # Get user ID
        
        # Create default subscription
        subscription = Subscription(
            user_id=user.id,
            tier="free",
            status="active",
            monthly_route_limit=10  # Free tier limit
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(user)
        
        logger.info(f"New user created from Firebase: {user.email}")
        return user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user from Firebase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


async def require_admin(auth_context: AuthContext = Depends(authenticate_request)) -> AuthContext:
    """Dependency that requires admin privileges"""
    if not auth_context.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return auth_context


async def check_usage_limits(
    auth_context: AuthContext = Depends(authenticate_request),
    db: Session = Depends(get_db)
) -> AuthContext:
    """Dependency that checks usage limits before allowing route generation"""
    try:
        # Get user subscription
        user = db.query(User).filter(User.id == auth_context.user_id).first()
        
        if not user or not user.subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User subscription not found"
            )
        
        subscription = user.subscription
        
        # Check monthly usage limits
        allowed, usage_info = await usage_limiter.check_usage_limit(
            user_id=auth_context.user_id,
            subscription_tier=subscription.tier,
            monthly_limit=subscription.monthly_route_limit
        )
        
        if not allowed:
            raise create_usage_limit_response(usage_info)
        
        # Store usage info in request state
        if hasattr(auth_context, 'request'):
            auth_context.request.state.usage_info = usage_info
        
        return auth_context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Usage limit check failed: {e}")
        # Allow request on error to prevent service disruption
        return auth_context


def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for forwarded headers (proxy/load balancer)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Get user agent from request"""
    return request.headers.get("user-agent", "unknown")


# Optional authentication (for public endpoints)
async def optional_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[AuthContext]:
    """Optional authentication - returns None if no auth provided"""
    if not credentials and not request.headers.get("x-api-key"):
        return None
    
    try:
        return await authenticate_request(request, credentials, db)
    except HTTPException:
        return None


# Dependency for protected routes
async def require_auth(
    auth_context: AuthContext = Depends(authenticate_request)
) -> AuthContext:
    """Dependency that requires authentication"""
    return auth_context


# Dependency for route generation (with usage limits)
async def require_route_auth(
    auth_context: AuthContext = Depends(check_usage_limits)
) -> AuthContext:
    """Dependency for route generation endpoints with usage checks"""
    return auth_context