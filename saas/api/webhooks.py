from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import stripe
import logging
from datetime import datetime, timezone

from ..database.database import get_db
from ..database.models import WebhookLog, User, Subscription, SubscriptionTier, SubscriptionStatus, SUBSCRIPTION_TIERS
from ..billing.stripe_service import stripe_service
from ..services.usage_service import usage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def handle_stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    try:
        # Get raw body and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature"
            )
        
        # Construct and verify webhook event
        event = stripe_service.construct_webhook_event(payload, signature)
        
        # Log webhook event
        webhook_log = WebhookLog(
            stripe_event_id=event["id"],
            event_type=event["type"],
            event_data=event["data"]
        )
        db.add(webhook_log)
        db.commit()
        
        # Process webhook event
        success = await process_webhook_event(db, event, webhook_log)
        
        # Update webhook log
        webhook_log.processed = success
        webhook_log.processed_at = datetime.now(timezone.utc)
        if not success:
            webhook_log.last_error = "Processing failed"
        
        db.commit()
        
        return {"received": True, "processed": success}
        
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid Stripe signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        # Don't raise exception to avoid Stripe retries for client errors
        return {"received": True, "processed": False, "error": str(e)}


async def process_webhook_event(
    db: Session,
    event: dict,
    webhook_log: WebhookLog
) -> bool:
    """Process different types of Stripe webhook events"""
    event_type = event["type"]
    event_data = event["data"]
    
    try:
        webhook_log.processing_attempts += 1
        
        # Customer events
        if event_type == "customer.created":
            return await handle_customer_created(db, event_data)
        
        elif event_type == "customer.updated":
            return await handle_customer_updated(db, event_data)
        
        elif event_type == "customer.deleted":
            return await handle_customer_deleted(db, event_data)
        
        # Subscription events
        elif event_type == "customer.subscription.created":
            return await stripe_service.handle_subscription_created(db, event_data)
        
        elif event_type == "customer.subscription.updated":
            return await stripe_service.handle_subscription_updated(db, event_data)
        
        elif event_type == "customer.subscription.deleted":
            return await stripe_service.handle_subscription_deleted(db, event_data)
        
        # Invoice events
        elif event_type == "invoice.created":
            return await handle_invoice_created(db, event_data)
        
        elif event_type == "invoice.payment_succeeded":
            return await handle_invoice_payment_succeeded(db, event_data)
        
        elif event_type == "invoice.payment_failed":
            return await handle_invoice_payment_failed(db, event_data)
        
        # Payment intent events
        elif event_type == "payment_intent.succeeded":
            return await handle_payment_succeeded(db, event_data)
        
        elif event_type == "payment_intent.payment_failed":
            return await handle_payment_failed(db, event_data)
        
        # Checkout session events
        elif event_type == "checkout.session.completed":
            return await handle_checkout_completed(db, event_data)
        
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return True  # Return True for unhandled events to avoid retries
        
    except Exception as e:
        logger.error(f"Failed to process webhook event {event_type}: {e}")
        webhook_log.last_error = str(e)
        return False


async def handle_customer_created(db: Session, event_data: dict) -> bool:
    """Handle customer.created webhook"""
    try:
        customer_data = event_data["object"]
        customer_id = customer_data["id"]
        user_id = customer_data["metadata"].get("user_id")
        
        if not user_id:
            logger.warning(f"No user_id in customer metadata: {customer_id}")
            return True
        
        # Update user's subscription with Stripe customer ID
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.subscription:
            user.subscription.stripe_customer_id = customer_id
            db.commit()
            logger.info(f"Customer ID {customer_id} linked to user {user.email}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle customer created: {e}")
        return False


async def handle_customer_updated(db: Session, event_data: dict) -> bool:
    """Handle customer.updated webhook"""
    try:
        customer_data = event_data["object"]
        customer_id = customer_data["id"]
        
        # Find subscription by customer ID
        subscription = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        
        if subscription and subscription.user:
            # Update user information if needed
            user = subscription.user
            if customer_data.get("email") and customer_data["email"] != user.email:
                logger.info(f"Updating user email from {user.email} to {customer_data['email']}")
                user.email = customer_data["email"]
            
            if customer_data.get("name") and customer_data["name"] != user.display_name:
                user.display_name = customer_data["name"]
            
            db.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle customer updated: {e}")
        return False


async def handle_customer_deleted(db: Session, event_data: dict) -> bool:
    """Handle customer.deleted webhook"""
    try:
        customer_data = event_data["object"]
        customer_id = customer_data["id"]
        
        # Find and update subscription
        subscription = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        
        if subscription:
            # Reset to free tier
            subscription.stripe_customer_id = None
            subscription.stripe_subscription_id = None
            subscription.tier = SubscriptionTier.FREE
            subscription.status = SubscriptionStatus.CANCELED
            subscription.monthly_route_limit = SUBSCRIPTION_TIERS[SubscriptionTier.FREE]["monthly_route_limit"]
            subscription.canceled_at = datetime.now(timezone.utc)
            
            db.commit()
            logger.info(f"Customer {customer_id} deleted, subscription reset to free tier")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle customer deleted: {e}")
        return False


async def handle_invoice_created(db: Session, event_data: dict) -> bool:
    """Handle invoice.created webhook"""
    try:
        invoice_data = event_data["object"]
        customer_id = invoice_data["customer"]
        
        # Find subscription
        subscription = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        
        if subscription:
            logger.info(f"Invoice created for customer {customer_id}")
            # Could send email notification here
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle invoice created: {e}")
        return False


async def handle_invoice_payment_succeeded(db: Session, event_data: dict) -> bool:
    """Handle invoice.payment_succeeded webhook"""
    try:
        invoice_data = event_data["object"]
        customer_id = invoice_data["customer"]
        subscription_id = invoice_data.get("subscription")
        
        # Find subscription
        subscription = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        
        if subscription:
            # Update subscription status to active
            subscription.status = SubscriptionStatus.ACTIVE
            
            # If this is for a subscription, update the tier based on the line items
            if subscription_id:
                await update_subscription_tier_from_invoice(db, subscription, invoice_data)
            
            db.commit()
            logger.info(f"Payment succeeded for customer {customer_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle payment succeeded: {e}")
        return False


async def handle_invoice_payment_failed(db: Session, event_data: dict) -> bool:
    """Handle invoice.payment_failed webhook"""
    try:
        invoice_data = event_data["object"]
        customer_id = invoice_data["customer"]
        
        # Find subscription
        subscription = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        
        if subscription:
            # Update subscription status
            subscription.status = SubscriptionStatus.PAST_DUE
            db.commit()
            
            logger.warning(f"Payment failed for customer {customer_id}")
            # Could send email notification here
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle payment failed: {e}")
        return False


async def handle_payment_succeeded(db: Session, event_data: dict) -> bool:
    """Handle payment_intent.succeeded webhook"""
    try:
        payment_data = event_data["object"]
        customer_id = payment_data.get("customer")
        
        if customer_id:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_customer_id == customer_id
            ).first()
            
            if subscription:
                logger.info(f"Payment intent succeeded for customer {customer_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle payment succeeded: {e}")
        return False


async def handle_payment_failed(db: Session, event_data: dict) -> bool:
    """Handle payment_intent.payment_failed webhook"""
    try:
        payment_data = event_data["object"]
        customer_id = payment_data.get("customer")
        
        if customer_id:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_customer_id == customer_id
            ).first()
            
            if subscription:
                logger.warning(f"Payment intent failed for customer {customer_id}")
                # Could send email notification here
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle payment failed: {e}")
        return False


async def handle_checkout_completed(db: Session, event_data: dict) -> bool:
    """Handle checkout.session.completed webhook"""
    try:
        session_data = event_data["object"]
        customer_id = session_data["customer"]
        subscription_id = session_data.get("subscription")
        user_id = session_data["metadata"].get("user_id")
        tier = session_data["metadata"].get("tier")
        
        if not user_id or not tier:
            logger.warning(f"Missing metadata in checkout session: {session_data['id']}")
            return True
        
        # Find user and subscription
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.subscription:
            logger.error(f"User or subscription not found: {user_id}")
            return False
        
        subscription = user.subscription
        
        # Update subscription with checkout session data
        subscription.stripe_customer_id = customer_id
        if subscription_id:
            subscription.stripe_subscription_id = subscription_id
        
        # Update tier and limits
        if tier in SUBSCRIPTION_TIERS:
            subscription.tier = tier
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.monthly_route_limit = SUBSCRIPTION_TIERS[tier]["monthly_route_limit"]
        
        db.commit()
        
        logger.info(f"Checkout completed for user {user.email}, tier: {tier}")
        
        # Could send welcome email here
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle checkout completed: {e}")
        return False


async def update_subscription_tier_from_invoice(
    db: Session,
    subscription: Subscription,
    invoice_data: dict
):
    """Update subscription tier based on invoice line items"""
    try:
        lines = invoice_data.get("lines", {}).get("data", [])
        
        for line in lines:
            price_id = line.get("price", {}).get("id")
            
            # Map price ID to tier
            for tier, tier_info in SUBSCRIPTION_TIERS.items():
                if tier_info.get("stripe_price_id") == price_id:
                    subscription.tier = tier
                    subscription.monthly_route_limit = tier_info["monthly_route_limit"]
                    logger.info(f"Updated subscription tier to {tier} based on price {price_id}")
                    return
        
    except Exception as e:
        logger.error(f"Failed to update subscription tier from invoice: {e}")


@router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhook system"""
    return {
        "status": "webhook system operational",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }