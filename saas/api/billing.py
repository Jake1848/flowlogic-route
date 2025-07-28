from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from ..database.database import get_db
from ..database.models import SubscriptionTier, SUBSCRIPTION_TIERS
from ..middleware.auth_middleware import require_auth, AuthContext
from ..billing.stripe_service import stripe_service
from ..services.usage_service import usage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# Pydantic models
class CheckoutRequest(BaseModel):
    tier: SubscriptionTier
    success_url: str
    cancel_url: str
    trial_days: Optional[int] = None


class SubscriptionDetails(BaseModel):
    tier: str
    status: str
    monthly_route_limit: int
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    trial_start: Optional[str]
    trial_end: Optional[str]
    canceled_at: Optional[str]
    tier_info: Dict[str, Any]


class UsageInfo(BaseModel):
    routes_used: int
    routes_limit: int
    usage_percentage: float
    remaining_routes: int
    period_start: Optional[str]
    period_end: Optional[str]


@router.get("/plans")
async def get_pricing_plans():
    """Get available subscription plans"""
    plans = []
    
    for tier, info in SUBSCRIPTION_TIERS.items():
        plan = {
            "tier": tier,
            "name": info["name"],
            "price": info["price"],
            "monthly_route_limit": info["monthly_route_limit"],
            "features": info["features"],
            "popular": tier == SubscriptionTier.PROFESSIONAL  # Mark Professional as popular
        }
        plans.append(plan)
    
    return {"plans": plans}


@router.get("/subscription")
async def get_subscription(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current subscription details"""
    try:
        subscription_details = await stripe_service.get_subscription_details(db, auth.user_id)
        return subscription_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscription for user {auth.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription details"
        )


@router.get("/usage")
async def get_usage_info(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current usage information"""
    try:
        usage_info = await stripe_service.get_usage_and_billing(db, auth.user_id)
        return usage_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get usage info for user {auth.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage information"
        )


@router.post("/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for subscription upgrade"""
    try:
        # Validate tier
        if request.tier not in SUBSCRIPTION_TIERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {request.tier}"
            )
        
        # Create checkout session
        session_data = await stripe_service.create_checkout_session(
            db=db,
            user_id=auth.user_id,
            tier=request.tier,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            trial_days=request.trial_days
        )
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/portal")
async def create_portal_session(
    return_url: str = Query(..., description="URL to return to after managing billing"),
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create Stripe Customer Portal session for subscription management"""
    try:
        portal_url = await stripe_service.create_portal_session(
            db=db,
            user_id=auth.user_id,
            return_url=return_url
        )
        
        return {"portal_url": portal_url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )


@router.post("/cancel")
async def cancel_subscription(
    immediate: bool = Query(False, description="Cancel immediately or at period end"),
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Cancel user subscription"""
    try:
        success = await stripe_service.cancel_subscription(
            db=db,
            user_id=auth.user_id,
            immediate=immediate
        )
        
        if success:
            message = "Subscription canceled immediately" if immediate else "Subscription will cancel at period end"
            return {"success": True, "message": message}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.get("/history")
async def get_usage_history(
    months: int = Query(12, ge=1, le=24, description="Number of months of history"),
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
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


@router.get("/invoices")
async def get_invoices(
    limit: int = Query(10, ge=1, le=100),
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get user's billing invoices"""
    try:
        # This would integrate with Stripe to get invoice data
        # For now, return placeholder
        return {
            "invoices": [],
            "message": "Invoice integration coming soon"
        }
        
    except Exception as e:
        logger.error(f"Failed to get invoices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoices"
        )


@router.get("/limits")
async def check_current_limits(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Check current usage limits and status"""
    try:
        limits_info = await usage_service.check_usage_limits(db, auth.user_id)
        return limits_info
        
    except Exception as e:
        logger.error(f"Failed to check limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check usage limits"
        )


@router.get("/upgrade-recommendation")
async def get_upgrade_recommendation(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get personalized upgrade recommendations"""
    try:
        # Get current usage and subscription
        usage_info = await stripe_service.get_usage_and_billing(db, auth.user_id)
        current_tier = usage_info["subscription"]["tier"]
        usage_percentage = usage_info["usage"]["usage_percentage"]
        
        # Generate recommendations
        recommendations = []
        
        if usage_percentage > 80:
            # User is close to limit
            next_tier = _get_next_tier(current_tier)
            if next_tier:
                tier_info = SUBSCRIPTION_TIERS[next_tier]
                recommendations.append({
                    "type": "upgrade",
                    "tier": next_tier,
                    "reason": f"You're using {usage_percentage:.1f}% of your current limit",
                    "benefits": [
                        f"Increase limit to {tier_info['monthly_route_limit']} routes/month",
                        *tier_info["features"]
                    ],
                    "urgency": "high" if usage_percentage > 95 else "medium"
                })
        
        elif usage_percentage < 20 and current_tier != SubscriptionTier.FREE:
            # User might be over-subscribed
            prev_tier = _get_previous_tier(current_tier)
            if prev_tier:
                tier_info = SUBSCRIPTION_TIERS[prev_tier]
                recommendations.append({
                    "type": "downgrade",
                    "tier": prev_tier,
                    "reason": f"You're only using {usage_percentage:.1f}% of your current limit",
                    "benefits": [
                        f"Save money while still having {tier_info['monthly_route_limit']} routes/month",
                        "Access to core features"
                    ],
                    "urgency": "low"
                })
        
        return {
            "current_tier": current_tier,
            "usage_percentage": usage_percentage,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to get upgrade recommendation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upgrade recommendation"
        )


def _get_next_tier(current_tier: str) -> Optional[str]:
    """Get the next higher subscription tier"""
    tier_order = [
        SubscriptionTier.FREE,
        SubscriptionTier.STARTER,
        SubscriptionTier.PROFESSIONAL,
        SubscriptionTier.ENTERPRISE
    ]
    
    try:
        current_index = tier_order.index(current_tier)
        if current_index < len(tier_order) - 1:
            return tier_order[current_index + 1]
    except ValueError:
        pass
    
    return None


def _get_previous_tier(current_tier: str) -> Optional[str]:
    """Get the next lower subscription tier"""
    tier_order = [
        SubscriptionTier.FREE,
        SubscriptionTier.STARTER,
        SubscriptionTier.PROFESSIONAL,
        SubscriptionTier.ENTERPRISE
    ]
    
    try:
        current_index = tier_order.index(current_tier)
        if current_index > 0:
            return tier_order[current_index - 1]
    except ValueError:
        pass
    
    return None


@router.get("/stats")
async def get_billing_stats(
    auth: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get comprehensive billing and usage statistics"""
    try:
        # Get user statistics
        user_stats = await usage_service.get_user_stats(db, auth.user_id)
        
        # Get subscription details
        subscription_details = await stripe_service.get_subscription_details(db, auth.user_id)
        
        # Get current usage limits
        limits_info = await usage_service.check_usage_limits(db, auth.user_id)
        
        return {
            "subscription": subscription_details,
            "usage_limits": limits_info,
            "statistics": user_stats,
            "tier_features": SUBSCRIPTION_TIERS.get(subscription_details.get("tier"), {})
        }
        
    except Exception as e:
        logger.error(f"Failed to get billing stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing statistics"
        )