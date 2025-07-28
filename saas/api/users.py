from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
import logging

from ..database.database import get_db
from ..database.models import User, APIKey
from ..middleware.auth_middleware import require_auth, AuthContext
from ..auth.api_keys import api_key_manager
from ..services.usage_service import usage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


# Pydantic models
class UserProfile(BaseModel):
    id: str
    email: EmailStr
    display_name: Optional[str]
    company_name: Optional[str]
    phone_number: Optional[str]
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    company_name: Optional[str] = None
    phone_number: Optional[str] = None


class CreateAPIKeyRequest(BaseModel):
    name: str
    allowed_ips: Optional[List[str]] = None
    expires_in_days: Optional[int] = None
    rate_limit_override: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: str
    key: Optional[str]  # Only returned on creation
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]
    usage_count: int
    expires_at: Optional[datetime]
    allowed_ips: Optional[List[str]]
    rate_limit_override: Optional[int]


class UpdateAPIKeyRequest(BaseModel):
    name: Optional[str] = None
    allowed_ips: Optional[List[str]] = None
    rate_limit_override: Optional[int] = None


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    try:
        user = db.query(User).filter(User.id == auth.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfile(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            company_name=user.company_name,
            phone_number=user.phone_number,
            email_verified=user.email_verified,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    request: UpdateProfileRequest,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    try:
        user = db.query(User).filter(User.id == auth.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        if request.display_name is not None:
            user.display_name = request.display_name
        if request.company_name is not None:
            user.company_name = request.company_name
        if request.phone_number is not None:
            user.phone_number = request.phone_number
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"User profile updated: {user.email}")
        
        return UserProfile(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            company_name=user.company_name,
            phone_number=user.phone_number,
            email_verified=user.email_verified,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def get_api_keys(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all API keys for the current user"""
    try:
        api_keys = await api_key_manager.list_api_keys(db, auth.user_id)
        
        return [
            APIKeyResponse(
                id=key["id"],
                key=None,  # Never return the actual key
                name=key["name"],
                prefix=key["prefix"],
                is_active=key["is_active"],
                created_at=key["created_at"],
                last_used=key["last_used"],
                usage_count=key["usage_count"],
                expires_at=key["expires_at"],
                allowed_ips=key["allowed_ips"],
                rate_limit_override=key["rate_limit_override"]
            )
            for key in api_keys
        ]
        
    except Exception as e:
        logger.error(f"Failed to get API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys"
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    try:
        api_key_data = await api_key_manager.create_api_key(
            db=db,
            user_id=auth.user_id,
            name=request.name,
            allowed_ips=request.allowed_ips,
            expires_in_days=request.expires_in_days,
            rate_limit_override=request.rate_limit_override
        )
        
        return APIKeyResponse(
            id=api_key_data["id"],
            key=api_key_data["key"],  # Only returned on creation
            name=api_key_data["name"],
            prefix=api_key_data["prefix"],
            is_active=True,
            created_at=api_key_data["created_at"],
            last_used=None,
            usage_count=0,
            expires_at=api_key_data["expires_at"],
            allowed_ips=api_key_data["allowed_ips"],
            rate_limit_override=api_key_data["rate_limit_override"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.put("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: str,
    request: UpdateAPIKeyRequest,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update an API key"""
    try:
        api_key_data = await api_key_manager.update_api_key(
            db=db,
            user_id=auth.user_id,
            api_key_id=api_key_id,
            name=request.name,
            allowed_ips=request.allowed_ips,
            rate_limit_override=request.rate_limit_override
        )
        
        return APIKeyResponse(
            id=api_key_data["id"],
            key=None,
            name=api_key_data["name"],
            prefix=api_key_data["prefix"],
            is_active=api_key_data["is_active"],
            created_at=api_key_data["created_at"],
            last_used=api_key_data["last_used"],
            usage_count=api_key_data["usage_count"],
            expires_at=api_key_data["expires_at"],
            allowed_ips=api_key_data["allowed_ips"],
            rate_limit_override=api_key_data["rate_limit_override"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API key"
        )


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Revoke (deactivate) an API key"""
    try:
        success = await api_key_manager.revoke_api_key(db, auth.user_id, api_key_id)
        
        if success:
            return {"success": True, "message": "API key revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke API key"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


@router.get("/usage/current")
async def get_current_usage(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current month usage for the user"""
    try:
        usage_limits = await usage_service.check_usage_limits(db, auth.user_id)
        return usage_limits
        
    except Exception as e:
        logger.error(f"Failed to get current usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve current usage"
        )


@router.get("/usage/history")
async def get_usage_history(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
    months: int = 6
):
    """Get usage history for the user"""
    try:
        history = await usage_service.get_usage_history(db, auth.user_id, months)
        return {"usage_history": history}
        
    except Exception as e:
        logger.error(f"Failed to get usage history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage history"
        )


@router.get("/usage/logs")
async def get_route_logs(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    success_only: bool = False
):
    """Get route generation logs for the user"""
    try:
        logs = await usage_service.get_route_logs(
            db, auth.user_id, limit, offset, success_only
        )
        return {"route_logs": logs}
        
    except Exception as e:
        logger.error(f"Failed to get route logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve route logs"
        )


@router.get("/statistics")
async def get_user_statistics(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get comprehensive user statistics"""
    try:
        stats = await usage_service.get_user_stats(db, auth.user_id)
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get user statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.delete("/account")
async def delete_user_account(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete user account (requires confirmation)"""
    try:
        # In a real implementation, this would:
        # 1. Cancel Stripe subscription
        # 2. Delete user data (GDPR compliance)
        # 3. Revoke all API keys
        # 4. Delete Firebase account
        
        # For now, just deactivate the account
        user = db.query(User).filter(User.id == auth.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Deactivate user
        user.is_active = False
        
        # Revoke all API keys
        api_keys = db.query(APIKey).filter(APIKey.user_id == auth.user_id).all()
        for api_key in api_keys:
            api_key.is_active = False
        
        db.commit()
        
        logger.info(f"User account deactivated: {user.email}")
        
        return {"success": True, "message": "Account deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )