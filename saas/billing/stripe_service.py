import os
import stripe
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from ..database.models import User, Subscription, SubscriptionTier, SubscriptionStatus, SUBSCRIPTION_TIERS
from ..database.database import get_db

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


class StripeService:
    """Stripe billing integration for FlowLogic RouteAI"""
    
    def __init__(self):
        self.webhook_secret = STRIPE_WEBHOOK_SECRET
        self.price_ids = {
            SubscriptionTier.STARTER: os.getenv("STRIPE_PRICE_STARTER", "price_starter_monthly"),
            SubscriptionTier.PROFESSIONAL: os.getenv("STRIPE_PRICE_PROFESSIONAL", "price_professional_monthly"),
            SubscriptionTier.ENTERPRISE: os.getenv("STRIPE_PRICE_ENTERPRISE", "price_enterprise_monthly"),
        }
    
    async def create_customer(self, user: User) -> str:
        """Create a Stripe customer for a user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.display_name,
                metadata={
                    "user_id": str(user.id),
                    "firebase_uid": user.firebase_uid,
                    "company": user.company_name or "",
                }
            )
            
            logger.info(f"Stripe customer created: {customer.id} for user {user.email}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create billing account"
            )
    
    async def create_checkout_session(
        self,
        db: Session,
        user_id: str,
        tier: SubscriptionTier,
        success_url: str,
        cancel_url: str,
        trial_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout session for subscription"""
        try:
            # Get user and subscription
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            subscription = user.subscription
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User has no subscription record"
                )
            
            # Ensure user has a Stripe customer ID
            if not subscription.stripe_customer_id:
                customer_id = await self.create_customer(user)
                subscription.stripe_customer_id = customer_id
                db.commit()
            else:
                customer_id = subscription.stripe_customer_id
            
            # Get price ID for the tier
            price_id = self.price_ids.get(tier)
            if not price_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid subscription tier: {tier}"
                )
            
            # Create checkout session parameters
            session_params = {
                "customer": customer_id,
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": price_id,
                    "quantity": 1,
                }],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "user_id": str(user_id),
                    "tier": tier,
                },
                "allow_promotion_codes": True,
                "billing_address_collection": "required",
                "customer_update": {
                    "address": "auto",
                    "name": "auto",
                },
                "subscription_data": {
                    "metadata": {
                        "user_id": str(user_id),
                        "tier": tier,
                    }
                }
            }
            
            # Add trial period if specified
            if trial_days and trial_days > 0:
                session_params["subscription_data"]["trial_period_days"] = trial_days
            
            # Create the checkout session
            session = stripe.checkout.Session.create(**session_params)
            
            logger.info(f"Checkout session created: {session.id} for user {user.email}")
            
            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "customer_id": customer_id,
                "price_id": price_id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout session creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create checkout session"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Checkout session creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create checkout session"
            )
    
    async def create_portal_session(self, db: Session, user_id: str, return_url: str) -> str:
        """Create a Stripe Customer Portal session"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.subscription or not user.subscription.stripe_customer_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No billing account found"
                )
            
            session = stripe.billing_portal.Session.create(
                customer=user.subscription.stripe_customer_id,
                return_url=return_url,
            )
            
            logger.info(f"Portal session created for user {user.email}")
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Portal session creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create billing portal session"
            )
    
    async def get_subscription_details(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get detailed subscription information"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subscription not found"
                )
            
            subscription = user.subscription
            result = {
                "tier": subscription.tier,
                "status": subscription.status,
                "monthly_route_limit": subscription.monthly_route_limit,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "trial_start": subscription.trial_start,
                "trial_end": subscription.trial_end,
                "canceled_at": subscription.canceled_at,
                "tier_info": SUBSCRIPTION_TIERS.get(subscription.tier, {})
            }
            
            # Get Stripe subscription details if available
            if subscription.stripe_subscription_id:
                try:
                    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                    result.update({
                        "stripe_status": stripe_sub.status,
                        "cancel_at_period_end": stripe_sub.cancel_at_period_end,
                        "next_invoice_date": datetime.fromtimestamp(
                            stripe_sub.current_period_end, tz=timezone.utc
                        ) if stripe_sub.current_period_end else None,
                    })
                except stripe.error.StripeError as e:
                    logger.warning(f"Failed to fetch Stripe subscription details: {e}")
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get subscription details: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve subscription details"
            )
    
    async def cancel_subscription(self, db: Session, user_id: str, immediate: bool = False) -> bool:
        """Cancel a user's subscription"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subscription not found"
                )
            
            subscription = user.subscription
            
            # Cancel in Stripe if exists
            if subscription.stripe_subscription_id:
                try:
                    if immediate:
                        stripe.Subscription.delete(subscription.stripe_subscription_id)
                    else:
                        stripe.Subscription.modify(
                            subscription.stripe_subscription_id,
                            cancel_at_period_end=True
                        )
                except stripe.error.StripeError as e:
                    logger.error(f"Failed to cancel Stripe subscription: {e}")
                    # Continue with local cancellation
            
            # Update local subscription
            if immediate:
                subscription.status = SubscriptionStatus.CANCELED
                subscription.canceled_at = datetime.now(timezone.utc)
                subscription.tier = SubscriptionTier.FREE
                subscription.monthly_route_limit = SUBSCRIPTION_TIERS[SubscriptionTier.FREE]["monthly_route_limit"]
            
            db.commit()
            
            logger.info(f"Subscription {'immediately ' if immediate else ''}canceled for user {user.email}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cancel subscription: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )
    
    async def get_usage_and_billing(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get current usage and billing information"""
        try:
            from ..services.usage_service import usage_service
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get current month usage
            now = datetime.now(timezone.utc)
            current_usage = await usage_service.get_monthly_usage(db, user_id, now.year, now.month)
            
            # Get subscription details
            subscription = user.subscription
            tier_info = SUBSCRIPTION_TIERS.get(subscription.tier, {})
            
            # Calculate usage percentage
            usage_percentage = 0
            if subscription.monthly_route_limit > 0:
                usage_percentage = (current_usage.routes_generated / subscription.monthly_route_limit) * 100
            
            # Determine next billing date
            next_billing_date = None
            if subscription.current_period_end:
                next_billing_date = subscription.current_period_end
            
            return {
                "subscription": {
                    "tier": subscription.tier,
                    "status": subscription.status,
                    "tier_name": tier_info.get("name", subscription.tier),
                    "price": tier_info.get("price", 0),
                },
                "usage": {
                    "routes_used": current_usage.routes_generated,
                    "routes_limit": subscription.monthly_route_limit,
                    "usage_percentage": min(usage_percentage, 100),
                    "period_start": subscription.current_period_start,
                    "period_end": subscription.current_period_end,
                },
                "billing": {
                    "next_billing_date": next_billing_date,
                    "trial_end": subscription.trial_end,
                    "canceled_at": subscription.canceled_at,
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get usage and billing info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve usage and billing information"
            )
    
    def construct_webhook_event(self, payload: bytes, signature: str):
        """Construct and verify Stripe webhook event"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    async def handle_subscription_created(self, db: Session, event_data: Dict[str, Any]) -> bool:
        """Handle subscription.created webhook"""
        try:
            subscription_data = event_data["object"]
            user_id = subscription_data["metadata"].get("user_id")
            
            if not user_id:
                logger.error("No user_id in subscription metadata")
                return False
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.subscription:
                logger.error(f"User or subscription not found: {user_id}")
                return False
            
            # Update subscription with Stripe data
            subscription = user.subscription
            subscription.stripe_subscription_id = subscription_data["id"]
            subscription.stripe_price_id = subscription_data["items"]["data"][0]["price"]["id"]
            subscription.status = subscription_data["status"]
            subscription.current_period_start = datetime.fromtimestamp(
                subscription_data["current_period_start"], tz=timezone.utc
            )
            subscription.current_period_end = datetime.fromtimestamp(
                subscription_data["current_period_end"], tz=timezone.utc
            )
            
            # Handle trial period
            if subscription_data.get("trial_start") and subscription_data.get("trial_end"):
                subscription.trial_start = datetime.fromtimestamp(
                    subscription_data["trial_start"], tz=timezone.utc
                )
                subscription.trial_end = datetime.fromtimestamp(
                    subscription_data["trial_end"], tz=timezone.utc
                )
            
            db.commit()
            logger.info(f"Subscription created for user {user.email}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to handle subscription created: {e}")
            return False
    
    async def handle_subscription_updated(self, db: Session, event_data: Dict[str, Any]) -> bool:
        """Handle subscription.updated webhook"""
        try:
            subscription_data = event_data["object"]
            stripe_subscription_id = subscription_data["id"]
            
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_subscription_id
            ).first()
            
            if not subscription:
                logger.error(f"Subscription not found: {stripe_subscription_id}")
                return False
            
            # Update subscription status and period
            subscription.status = subscription_data["status"]
            subscription.current_period_start = datetime.fromtimestamp(
                subscription_data["current_period_start"], tz=timezone.utc
            )
            subscription.current_period_end = datetime.fromtimestamp(
                subscription_data["current_period_end"], tz=timezone.utc
            )
            
            # Handle cancellation
            if subscription_data.get("canceled_at"):
                subscription.canceled_at = datetime.fromtimestamp(
                    subscription_data["canceled_at"], tz=timezone.utc
                )
            
            db.commit()
            logger.info(f"Subscription updated: {stripe_subscription_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to handle subscription updated: {e}")
            return False
    
    async def handle_subscription_deleted(self, db: Session, event_data: Dict[str, Any]) -> bool:
        """Handle subscription.deleted webhook"""
        try:
            subscription_data = event_data["object"]
            stripe_subscription_id = subscription_data["id"]
            
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_subscription_id
            ).first()
            
            if not subscription:
                logger.error(f"Subscription not found: {stripe_subscription_id}")
                return False
            
            # Cancel subscription and revert to free tier
            subscription.status = SubscriptionStatus.CANCELED
            subscription.tier = SubscriptionTier.FREE
            subscription.monthly_route_limit = SUBSCRIPTION_TIERS[SubscriptionTier.FREE]["monthly_route_limit"]
            subscription.canceled_at = datetime.now(timezone.utc)
            
            db.commit()
            logger.info(f"Subscription deleted: {stripe_subscription_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to handle subscription deleted: {e}")
            return False


# Global Stripe service instance
stripe_service = StripeService()


# Utility functions
async def create_checkout_session(
    db: Session,
    user_id: str,
    tier: SubscriptionTier,
    success_url: str,
    cancel_url: str,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function to create checkout session"""
    return await stripe_service.create_checkout_session(
        db, user_id, tier, success_url, cancel_url, **kwargs
    )


async def get_subscription_details(db: Session, user_id: str) -> Dict[str, Any]:
    """Convenience function to get subscription details"""
    return await stripe_service.get_subscription_details(db, user_id)