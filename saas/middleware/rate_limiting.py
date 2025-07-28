import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import redis
from fastapi import HTTPException, Request, status
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter with sliding window algorithm"""
    
    def __init__(self):
        self.redis_client = self._init_redis()
        
        # Default rate limits per tier (requests per minute)
        self.default_limits = {
            "free": 10,          # 10 requests per minute
            "starter": 60,       # 60 requests per minute  
            "professional": 300, # 300 requests per minute
            "enterprise": 1000,  # 1000 requests per minute
            "admin": 10000       # 10000 requests per minute
        }
        
        # Window duration in seconds
        self.window_duration = 60  # 1 minute
    
    def _init_redis(self) -> redis.Redis:
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            client.ping()
            logger.info("Redis connection established for rate limiting")
            return client
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Fallback to in-memory rate limiting for development
            logger.warning("Using in-memory rate limiting (not recommended for production)")
            return None
    
    def get_rate_limit(self, tier: str, override: Optional[int] = None) -> int:
        """Get rate limit for a tier"""
        if override:
            return override
        return self.default_limits.get(tier, self.default_limits["free"])
    
    async def check_rate_limit(
        self,
        identifier: str,
        tier: str,
        override: Optional[int] = None,
        window_duration: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (user_id, api_key, ip_address)
            tier: Subscription tier
            override: Custom rate limit override
            window_duration: Custom window duration in seconds
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        limit = self.get_rate_limit(tier, override)
        window = window_duration or self.window_duration
        
        if not self.redis_client:
            # Fallback to in-memory rate limiting
            return await self._memory_rate_limit(identifier, limit, window)
        
        try:
            return await self._redis_rate_limit(identifier, limit, window)
        except Exception as e:
            logger.error(f"Redis rate limiting failed: {e}")
            # Fallback to allowing request
            return True, {"limit": limit, "remaining": limit, "reset_time": time.time() + window}
    
    async def _redis_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Redis-based sliding window rate limiting"""
        now = time.time()
        pipeline = self.redis_client.pipeline()
        
        # Key for this identifier
        key = f"rate_limit:{identifier}"
        
        # Remove expired entries (older than window)
        pipeline.zremrangebyscore(key, 0, now - window)
        
        # Count current requests in window
        pipeline.zcard(key)
        
        # Add current request
        pipeline.zadd(key, {str(now): now})
        
        # Set expiration on key
        pipeline.expire(key, window + 1)
        
        # Execute pipeline
        results = pipeline.execute()
        current_count = results[1]
        
        # Calculate remaining requests and reset time
        remaining = max(0, limit - current_count - 1)  # -1 for current request
        reset_time = now + window
        
        # Check if limit exceeded
        allowed = current_count < limit
        
        rate_info = {
            "limit": limit,
            "remaining": remaining,
            "reset_time": reset_time,
            "window_duration": window
        }
        
        if not allowed:
            # Remove the request we just added since it's not allowed
            self.redis_client.zrem(key, str(now))
            logger.warning(f"Rate limit exceeded for {identifier}: {current_count}/{limit}")
        
        return allowed, rate_info
    
    # Fallback in-memory rate limiting (for development/testing)
    _memory_store = {}
    
    async def _memory_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """In-memory rate limiting fallback"""
        now = time.time()
        
        if identifier not in self._memory_store:
            self._memory_store[identifier] = []
        
        # Clean old entries
        requests = self._memory_store[identifier]
        self._memory_store[identifier] = [req_time for req_time in requests if req_time > now - window]
        
        current_count = len(self._memory_store[identifier])
        allowed = current_count < limit
        
        if allowed:
            self._memory_store[identifier].append(now)
            remaining = limit - current_count - 1
        else:
            remaining = 0
        
        rate_info = {
            "limit": limit,
            "remaining": remaining,
            "reset_time": now + window,
            "window_duration": window
        }
        
        return allowed, rate_info
    
    async def get_rate_limit_status(self, identifier: str) -> Dict[str, Any]:
        """Get current rate limit status for an identifier"""
        if not self.redis_client:
            return {"error": "Rate limiting not available"}
        
        try:
            key = f"rate_limit:{identifier}"
            now = time.time()
            
            # Get current count
            current_count = self.redis_client.zcount(key, now - self.window_duration, now)
            
            return {
                "identifier": identifier,
                "current_requests": current_count,
                "window_duration": self.window_duration,
                "last_request": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {"error": "Failed to get rate limit status"}
    
    async def reset_rate_limit(self, identifier: str) -> bool:
        """Reset rate limit for an identifier (admin function)"""
        if not self.redis_client:
            return False
        
        try:
            key = f"rate_limit:{identifier}"
            self.redis_client.delete(key)
            logger.info(f"Rate limit reset for {identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False


class UsageLimiter:
    """Usage-based limiting for subscription tiers"""
    
    def __init__(self):
        self.redis_client = self._init_redis()
        # Cache usage data for performance
        self.cache_duration = 300  # 5 minutes
    
    def _init_redis(self) -> redis.Redis:
        """Initialize Redis connection for usage caching"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")  # Different DB
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Redis for usage caching: {e}")
            return None
    
    async def check_usage_limit(
        self,
        user_id: str,
        subscription_tier: str,
        monthly_limit: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if user is within monthly usage limits"""
        try:
            # Check cached usage first
            cached_usage = await self._get_cached_usage(user_id)
            
            if cached_usage:
                current_usage = cached_usage["routes_used"]
            else:
                # Fallback to database query (would be implemented in service layer)
                current_usage = await self._get_current_usage_from_db(user_id)
                await self._cache_usage(user_id, current_usage, monthly_limit)
            
            remaining = max(0, monthly_limit - current_usage)
            allowed = current_usage < monthly_limit
            
            usage_info = {
                "tier": subscription_tier,
                "current_usage": current_usage,
                "monthly_limit": monthly_limit,
                "remaining": remaining,
                "usage_percentage": (current_usage / monthly_limit * 100) if monthly_limit > 0 else 0
            }
            
            return allowed, usage_info
            
        except Exception as e:
            logger.error(f"Failed to check usage limit for user {user_id}: {e}")
            # Allow request on error to prevent service disruption
            return True, {"error": "Usage check failed"}
    
    async def increment_usage(self, user_id: str) -> bool:
        """Increment usage counter for a user"""
        try:
            if not self.redis_client:
                return True
            
            # Increment cached usage
            key = f"usage:{user_id}"
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                data["routes_used"] += 1
                self.redis_client.setex(key, self.cache_duration, json.dumps(data))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to increment usage for user {user_id}: {e}")
            return False
    
    async def _get_cached_usage(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached usage data"""
        if not self.redis_client:
            return None
        
        try:
            key = f"usage:{user_id}"
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached usage: {e}")
            return None
    
    async def _cache_usage(self, user_id: str, routes_used: int, monthly_limit: int):
        """Cache usage data"""
        if not self.redis_client:
            return
        
        try:
            key = f"usage:{user_id}"
            data = {
                "routes_used": routes_used,
                "monthly_limit": monthly_limit,
                "last_updated": time.time()
            }
            
            self.redis_client.setex(key, self.cache_duration, json.dumps(data))
            
        except Exception as e:
            logger.error(f"Failed to cache usage: {e}")
    
    async def _get_current_usage_from_db(self, user_id: str) -> int:
        """Get current month usage from database (placeholder)"""
        # This would be implemented in the service layer
        # For now, return 0 as fallback
        return 0


# Global instances
rate_limiter = RateLimiter()
usage_limiter = UsageLimiter()


# Utility functions for FastAPI middleware
async def check_rate_limit(
    identifier: str,
    tier: str,
    override: Optional[int] = None
) -> Tuple[bool, Dict[str, Any]]:
    """Convenience function to check rate limit"""
    return await rate_limiter.check_rate_limit(identifier, tier, override)


async def check_usage_limit(
    user_id: str,
    tier: str,
    monthly_limit: int
) -> Tuple[bool, Dict[str, Any]]:
    """Convenience function to check usage limit"""
    return await usage_limiter.check_usage_limit(user_id, tier, monthly_limit)


def create_rate_limit_response(rate_info: Dict[str, Any]) -> HTTPException:
    """Create standardized rate limit response"""
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "limit": rate_info.get("limit"),
            "remaining": rate_info.get("remaining", 0),
            "reset_time": rate_info.get("reset_time"),
            "retry_after": max(1, int(rate_info.get("reset_time", time.time()) - time.time()))
        },
        headers={
            "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
            "X-RateLimit-Remaining": str(rate_info.get("remaining", 0)),
            "X-RateLimit-Reset": str(int(rate_info.get("reset_time", time.time()))),
            "Retry-After": str(max(1, int(rate_info.get("reset_time", time.time()) - time.time())))
        }
    )


def create_usage_limit_response(usage_info: Dict[str, Any]) -> HTTPException:
    """Create standardized usage limit response"""
    return HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "error": "Monthly usage limit exceeded",
            "tier": usage_info.get("tier"),
            "current_usage": usage_info.get("current_usage"),
            "monthly_limit": usage_info.get("monthly_limit"),
            "upgrade_url": "/billing/upgrade"
        },
        headers={
            "X-Usage-Limit": str(usage_info.get("monthly_limit", 0)),
            "X-Usage-Current": str(usage_info.get("current_usage", 0)),
            "X-Usage-Remaining": str(usage_info.get("remaining", 0))
        }
    )