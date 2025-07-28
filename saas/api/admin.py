from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from pydantic import BaseModel
import logging

from ..database.database import get_db
from ..database.models import (
    User, Subscription, APIKey, RouteLog, UsageRecord, WebhookLog, AdminMetrics,
    SubscriptionTier, SubscriptionStatus, SUBSCRIPTION_TIERS
)
from ..middleware.auth_middleware import require_admin, AuthContext
from ..services.usage_service import usage_service
from ..billing.stripe_service import stripe_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic models for responses
class UserSummary(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    firebase_uid: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    subscription_tier: str
    subscription_status: str
    monthly_route_limit: int
    total_api_keys: int


class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    new_users_today: int
    total_routes_generated: int
    routes_today: int
    revenue_metrics: Dict[str, Any]
    subscription_breakdown: Dict[str, int]
    usage_stats: Dict[str, Any]


class SystemHealth(BaseModel):
    database_status: str
    redis_status: str
    stripe_status: str
    total_errors: int
    last_error_time: Optional[datetime]


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard statistics"""
    try:
        # Time ranges
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # User statistics
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        new_users_today = db.query(User).filter(User.created_at >= today_start).count()
        
        # Route generation statistics
        total_routes = db.query(func.sum(RouteLog.addresses_count)).scalar() or 0
        routes_today = db.query(func.sum(RouteLog.addresses_count)).filter(
            RouteLog.created_at >= today_start
        ).scalar() or 0
        
        # Subscription breakdown
        subscription_breakdown = {}
        for tier in SubscriptionTier:
            count = db.query(Subscription).filter(Subscription.tier == tier).count()
            subscription_breakdown[tier] = count
        
        # Usage statistics for current month
        monthly_usage = db.query(
            func.sum(UsageRecord.routes_generated).label("total_routes"),
            func.sum(UsageRecord.total_stops_processed).label("total_stops"),
            func.sum(UsageRecord.total_miles_calculated).label("total_miles"),
            func.sum(UsageRecord.api_calls_made).label("total_api_calls")
        ).filter(
            and_(
                UsageRecord.year == now.year,
                UsageRecord.month == now.month
            )
        ).first()
        
        usage_stats = {
            "monthly_routes": int(monthly_usage.total_routes or 0),
            "monthly_stops": int(monthly_usage.total_stops or 0),
            "monthly_miles": float(monthly_usage.total_miles or 0),
            "monthly_api_calls": int(monthly_usage.total_api_calls or 0)
        }
        
        # Revenue metrics (placeholder - would integrate with Stripe)
        revenue_metrics = {
            "monthly_recurring_revenue": 0,  # Calculate from Stripe
            "annual_recurring_revenue": 0,
            "average_revenue_per_user": 0,
            "churn_rate": 0
        }
        
        return DashboardStats(
            total_users=total_users,
            active_users=active_users,
            new_users_today=new_users_today,
            total_routes_generated=total_routes,
            routes_today=routes_today,
            revenue_metrics=revenue_metrics,
            subscription_breakdown=subscription_breakdown,
            usage_stats=usage_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )


@router.get("/users", response_model=List[UserSummary])
async def get_users(
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get paginated list of users with filtering"""
    try:
        offset = (page - 1) * limit
        
        # Build query
        query = db.query(User).join(Subscription, User.id == Subscription.user_id)
        
        # Apply filters
        if search:
            query = query.filter(
                User.email.ilike(f"%{search}%") |
                User.display_name.ilike(f"%{search}%")
            )
        
        if tier:
            query = query.filter(Subscription.tier == tier)
        
        if status:
            if status == "active":
                query = query.filter(User.is_active == True)
            elif status == "inactive":
                query = query.filter(User.is_active == False)
        
        # Get users with pagination
        users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
        
        # Convert to response model
        user_summaries = []
        for user in users:
            # Count API keys
            api_key_count = db.query(APIKey).filter(
                and_(APIKey.user_id == user.id, APIKey.is_active == True)
            ).count()
            
            subscription = user.subscription
            user_summaries.append(UserSummary(
                id=str(user.id),
                email=user.email,
                display_name=user.display_name,
                firebase_uid=user.firebase_uid,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
                subscription_tier=subscription.tier if subscription else "free",
                subscription_status=subscription.status if subscription else "active",
                monthly_route_limit=subscription.monthly_route_limit if subscription else 0,
                total_api_keys=api_key_count
            ))
        
        return user_summaries
        
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/users/{user_id}/details")
async def get_user_details(
    user_id: str,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user statistics
        user_stats = await usage_service.get_user_stats(db, user_id)
        
        # Get API keys
        api_keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()
        api_key_info = [
            {
                "id": str(key.id),
                "name": key.name,
                "prefix": key.key_prefix,
                "is_active": key.is_active,
                "created_at": key.created_at,
                "last_used": key.last_used,
                "usage_count": key.usage_count
            }
            for key in api_keys
        ]
        
        # Get recent route logs
        recent_logs = await usage_service.get_route_logs(db, user_id, limit=10)
        
        # Get subscription details
        subscription_details = {}
        if user.subscription:
            try:
                subscription_details = await stripe_service.get_subscription_details(db, user_id)
            except Exception as e:
                logger.warning(f"Failed to get subscription details: {e}")
                subscription_details = {"error": "Failed to load subscription details"}
        
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "firebase_uid": user.firebase_uid,
                "company_name": user.company_name,
                "phone_number": user.phone_number,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "email_verified": user.email_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login": user.last_login
            },
            "subscription": subscription_details,
            "statistics": user_stats,
            "api_keys": api_key_info,
            "recent_activity": recent_logs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details"
        )


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user active status"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = is_active
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"User {user.email} status updated to {'active' if is_active else 'inactive'} by admin {auth.email}")
        
        return {"success": True, "message": f"User {'activated' if is_active else 'deactivated'} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update user status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )


@router.get("/system/health", response_model=SystemHealth)
async def get_system_health(
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system health status"""
    try:
        # Check database status
        try:
            db.execute("SELECT 1")
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"
        
        # Check Redis status (rate limiting)
        redis_status = "unknown"
        try:
            from ..middleware.rate_limiting import rate_limiter
            if rate_limiter.redis_client:
                rate_limiter.redis_client.ping()
                redis_status = "healthy"
            else:
                redis_status = "not_configured"
        except Exception:
            redis_status = "unhealthy"
        
        # Check Stripe status
        stripe_status = "unknown"
        try:
            import stripe
            stripe.Customer.list(limit=1)
            stripe_status = "healthy"
        except Exception:
            stripe_status = "unhealthy"
        
        # Get recent errors
        recent_errors = db.query(RouteLog).filter(
            and_(
                RouteLog.success == False,
                RouteLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
            )
        ).count()
        
        last_error = db.query(RouteLog).filter(
            RouteLog.success == False
        ).order_by(desc(RouteLog.created_at)).first()
        
        last_error_time = last_error.created_at if last_error else None
        
        return SystemHealth(
            database_status=database_status,
            redis_status=redis_status,
            stripe_status=stripe_status,
            total_errors=recent_errors,
            last_error_time=last_error_time
        )
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health"
        )


@router.get("/usage/overview")
async def get_usage_overview(
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get usage overview for the last N days"""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Daily usage statistics
        daily_stats = db.query(
            func.date(RouteLog.created_at).label("date"),
            func.count(RouteLog.id).label("total_requests"),
            func.sum(RouteLog.addresses_count).label("total_addresses"),
            func.count(RouteLog.id).filter(RouteLog.success == True).label("successful_requests"),
            func.avg(RouteLog.processing_time_ms).label("avg_processing_time")
        ).filter(
            RouteLog.created_at >= start_date
        ).group_by(
            func.date(RouteLog.created_at)
        ).order_by(desc("date")).all()
        
        # Top users by usage
        top_users = db.query(
            User.email,
            func.count(RouteLog.id).label("request_count"),
            func.sum(RouteLog.addresses_count).label("total_addresses")
        ).join(
            RouteLog, User.id == RouteLog.user_id
        ).filter(
            RouteLog.created_at >= start_date
        ).group_by(
            User.id, User.email
        ).order_by(
            desc("request_count")
        ).limit(10).all()
        
        # Error analysis
        error_stats = db.query(
            RouteLog.error_message,
            func.count(RouteLog.id).label("error_count")
        ).filter(
            and_(
                RouteLog.created_at >= start_date,
                RouteLog.success == False,
                RouteLog.error_message.isnot(None)
            )
        ).group_by(
            RouteLog.error_message
        ).order_by(
            desc("error_count")
        ).limit(10).all()
        
        return {
            "period_days": days,
            "daily_statistics": [
                {
                    "date": stat.date.isoformat(),
                    "total_requests": stat.total_requests,
                    "total_addresses": stat.total_addresses or 0,
                    "successful_requests": stat.successful_requests,
                    "success_rate": (stat.successful_requests / stat.total_requests * 100) if stat.total_requests > 0 else 0,
                    "avg_processing_time_ms": float(stat.avg_processing_time or 0)
                }
                for stat in daily_stats
            ],
            "top_users": [
                {
                    "email": user.email,
                    "request_count": user.request_count,
                    "total_addresses": user.total_addresses or 0
                }
                for user in top_users
            ],
            "common_errors": [
                {
                    "error_message": error.error_message,
                    "count": error.error_count
                }
                for error in error_stats
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage overview"
        )


@router.get("/webhooks/status")
async def get_webhook_status(
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=168)
):
    """Get webhook processing status"""
    try:
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Webhook statistics
        webhook_stats = db.query(
            func.count(WebhookLog.id).label("total_webhooks"),
            func.count(WebhookLog.id).filter(WebhookLog.processed == True).label("processed_webhooks"),
            func.count(WebhookLog.id).filter(WebhookLog.processed == False).label("failed_webhooks")
        ).filter(
            WebhookLog.created_at >= start_time
        ).first()
        
        # Recent webhook events
        recent_webhooks = db.query(WebhookLog).filter(
            WebhookLog.created_at >= start_time
        ).order_by(desc(WebhookLog.created_at)).limit(20).all()
        
        # Failed webhooks that need attention
        failed_webhooks = db.query(WebhookLog).filter(
            and_(
                WebhookLog.created_at >= start_time,
                WebhookLog.processed == False,
                WebhookLog.processing_attempts > 0
            )
        ).order_by(desc(WebhookLog.created_at)).limit(10).all()
        
        return {
            "period_hours": hours,
            "statistics": {
                "total_webhooks": webhook_stats.total_webhooks,
                "processed_webhooks": webhook_stats.processed_webhooks,
                "failed_webhooks": webhook_stats.failed_webhooks,
                "success_rate": (webhook_stats.processed_webhooks / webhook_stats.total_webhooks * 100) if webhook_stats.total_webhooks > 0 else 0
            },
            "recent_events": [
                {
                    "id": str(webhook.id),
                    "stripe_event_id": webhook.stripe_event_id,
                    "event_type": webhook.event_type,
                    "processed": webhook.processed,
                    "processing_attempts": webhook.processing_attempts,
                    "created_at": webhook.created_at,
                    "processed_at": webhook.processed_at,
                    "last_error": webhook.last_error
                }
                for webhook in recent_webhooks
            ],
            "failed_events": [
                {
                    "id": str(webhook.id),
                    "stripe_event_id": webhook.stripe_event_id,
                    "event_type": webhook.event_type,
                    "processing_attempts": webhook.processing_attempts,
                    "last_error": webhook.last_error,
                    "created_at": webhook.created_at
                }
                for webhook in failed_webhooks
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve webhook status"
        )


@router.post("/webhooks/{webhook_id}/retry")
async def retry_webhook(
    webhook_id: str,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retry a failed webhook"""
    try:
        webhook = db.query(WebhookLog).filter(WebhookLog.id == webhook_id).first()
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        # Reset webhook for retry
        webhook.processed = False
        webhook.processing_attempts = 0
        webhook.last_error = None
        webhook.processed_at = None
        
        db.commit()
        
        logger.info(f"Webhook {webhook_id} reset for retry by admin {auth.email}")
        
        return {"success": True, "message": "Webhook reset for retry"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to retry webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry webhook"
        )