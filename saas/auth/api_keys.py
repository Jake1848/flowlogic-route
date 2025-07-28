import hashlib
import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
import logging

from ..database.models import APIKey, User
from ..database.database import get_db

logger = logging.getLogger(__name__)


class APIKeyManager:
    """API key generation and management for FlowLogic RouteAI"""
    
    def __init__(self):
        self.key_prefix = "fl_live_"  # Production prefix
        self.test_prefix = "fl_test_"  # Test/development prefix
        self.key_length = 32  # Length of the random part
    
    def generate_api_key(self, is_test: bool = False) -> tuple[str, str, str]:
        """
        Generate a new API key
        
        Returns:
            tuple: (full_key, key_hash, key_prefix)
        """
        # Choose prefix based on environment
        prefix = self.test_prefix if is_test else self.key_prefix
        
        # Generate random key part
        alphabet = string.ascii_letters + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(self.key_length))
        
        # Combine prefix and random part
        full_key = f"{prefix}{random_part}"
        
        # Create hash for storage (using SHA-256)
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        # Create display prefix (first 10 characters)
        key_prefix = full_key[:10] + "..."
        
        return full_key, key_hash, key_prefix
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_api_key(
        self,
        db: Session,
        user_id: str,
        name: str,
        allowed_ips: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        rate_limit_override: Optional[int] = None,
        is_test: bool = False
    ) -> Dict[str, Any]:
        """Create a new API key for a user"""
        try:
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check existing API key count (limit to 10 per user)
            existing_keys = db.query(APIKey).filter(
                and_(APIKey.user_id == user_id, APIKey.is_active == True)
            ).count()
            
            if existing_keys >= 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum number of API keys reached (10)"
                )
            
            # Generate new API key
            full_key, key_hash, key_prefix = self.generate_api_key(is_test)
            
            # Calculate expiration date
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            
            # Create API key record
            api_key = APIKey(
                user_id=user_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
                allowed_ips=allowed_ips,
                rate_limit_override=rate_limit_override,
                expires_at=expires_at
            )
            
            db.add(api_key)
            db.commit()
            db.refresh(api_key)
            
            logger.info(f"API key created for user {user_id}: {name}")
            
            return {
                "id": str(api_key.id),
                "key": full_key,  # Only returned on creation
                "name": name,
                "prefix": key_prefix,
                "created_at": api_key.created_at,
                "expires_at": api_key.expires_at,
                "allowed_ips": api_key.allowed_ips,
                "rate_limit_override": api_key.rate_limit_override
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )
    
    async def validate_api_key(self, db: Session, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return user information"""
        try:
            # Hash the provided key
            key_hash = self.hash_api_key(api_key)
            
            # Find the API key in database
            api_key_record = db.query(APIKey).filter(
                and_(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True
                )
            ).first()
            
            if not api_key_record:
                logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
                return None
            
            # Check expiration
            if api_key_record.expires_at and api_key_record.expires_at < datetime.now(timezone.utc):
                logger.warning(f"Expired API key used: {api_key_record.key_prefix}")
                return None
            
            # Get associated user
            user = db.query(User).filter(User.id == api_key_record.user_id).first()
            if not user or not user.is_active:
                logger.warning(f"API key for inactive user: {api_key_record.key_prefix}")
                return None
            
            # Update usage tracking
            api_key_record.last_used = datetime.now(timezone.utc)
            api_key_record.usage_count += 1
            db.commit()
            
            return {
                "api_key_id": str(api_key_record.id),
                "user_id": str(user.id),
                "user_email": user.email,
                "firebase_uid": user.firebase_uid,
                "is_admin": user.is_admin,
                "subscription_tier": user.subscription.tier if user.subscription else "free",
                "rate_limit_override": api_key_record.rate_limit_override,
                "allowed_ips": api_key_record.allowed_ips
            }
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None
    
    async def list_api_keys(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """List all API keys for a user"""
        try:
            api_keys = db.query(APIKey).filter(APIKey.user_id == user_id).order_by(
                APIKey.created_at.desc()
            ).all()
            
            return [
                {
                    "id": str(key.id),
                    "name": key.name,
                    "prefix": key.key_prefix,
                    "is_active": key.is_active,
                    "created_at": key.created_at,
                    "last_used": key.last_used,
                    "usage_count": key.usage_count,
                    "expires_at": key.expires_at,
                    "allowed_ips": key.allowed_ips,
                    "rate_limit_override": key.rate_limit_override
                }
                for key in api_keys
            ]
            
        except Exception as e:
            logger.error(f"Failed to list API keys for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve API keys"
            )
    
    async def revoke_api_key(self, db: Session, user_id: str, api_key_id: str) -> bool:
        """Revoke (deactivate) an API key"""
        try:
            api_key = db.query(APIKey).filter(
                and_(
                    APIKey.id == api_key_id,
                    APIKey.user_id == user_id
                )
            ).first()
            
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
            api_key.is_active = False
            db.commit()
            
            logger.info(f"API key revoked: {api_key.key_prefix} for user {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to revoke API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke API key"
            )
    
    async def update_api_key(
        self,
        db: Session,
        user_id: str,
        api_key_id: str,
        name: Optional[str] = None,
        allowed_ips: Optional[List[str]] = None,
        rate_limit_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an API key's properties"""
        try:
            api_key = db.query(APIKey).filter(
                and_(
                    APIKey.id == api_key_id,
                    APIKey.user_id == user_id
                )
            ).first()
            
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
            # Update properties
            if name is not None:
                api_key.name = name
            if allowed_ips is not None:
                api_key.allowed_ips = allowed_ips
            if rate_limit_override is not None:
                api_key.rate_limit_override = rate_limit_override
            
            db.commit()
            db.refresh(api_key)
            
            logger.info(f"API key updated: {api_key.key_prefix} for user {user_id}")
            
            return {
                "id": str(api_key.id),
                "name": api_key.name,
                "prefix": api_key.key_prefix,
                "is_active": api_key.is_active,
                "created_at": api_key.created_at,
                "last_used": api_key.last_used,
                "usage_count": api_key.usage_count,
                "expires_at": api_key.expires_at,
                "allowed_ips": api_key.allowed_ips,
                "rate_limit_override": api_key.rate_limit_override
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update API key"
            )
    
    async def cleanup_expired_keys(self, db: Session) -> int:
        """Clean up expired API keys (soft delete)"""
        try:
            now = datetime.now(timezone.utc)
            
            # Find expired keys
            expired_keys = db.query(APIKey).filter(
                and_(
                    APIKey.expires_at < now,
                    APIKey.is_active == True
                )
            ).all()
            
            # Deactivate expired keys
            for key in expired_keys:
                key.is_active = False
            
            db.commit()
            
            logger.info(f"Cleaned up {len(expired_keys)} expired API keys")
            return len(expired_keys)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup expired API keys: {e}")
            return 0


# Global API key manager instance
api_key_manager = APIKeyManager()


# Utility functions
async def create_api_key(
    db: Session,
    user_id: str,
    name: str,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function to create API key"""
    return await api_key_manager.create_api_key(db, user_id, name, **kwargs)


async def validate_api_key(db: Session, api_key: str) -> Optional[Dict[str, Any]]:
    """Convenience function to validate API key"""
    return await api_key_manager.validate_api_key(db, api_key)