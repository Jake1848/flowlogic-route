from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    ForeignKey, Numeric, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

Base = declarative_base()


class SubscriptionTier(str, Enum):
    """Subscription tier enumeration"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional" 
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    UNPAID = "unpaid"


class User(Base):
    """User model with Firebase Auth integration"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    route_logs = relationship("RouteLog", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(email='{self.email}', firebase_uid='{self.firebase_uid}')>"


class Subscription(Base):
    """User subscription model integrated with Stripe"""
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Stripe integration
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)
    stripe_price_id = Column(String(255), nullable=True)
    
    # Subscription details
    tier = Column(String(50), nullable=False, default=SubscriptionTier.FREE)
    status = Column(String(50), nullable=False, default=SubscriptionStatus.ACTIVE)
    
    # Billing
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    
    # Usage limits (routes per month)
    monthly_route_limit = Column(Integer, nullable=False, default=10)  # Free tier limit
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(user_id='{self.user_id}', tier='{self.tier}', status='{self.status}')>"


class APIKey(Base):
    """API key model for user authentication"""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # API key details
    key_hash = Column(String(255), nullable=False, unique=True, index=True)  # Hashed API key
    key_prefix = Column(String(20), nullable=False)  # First few chars for display (e.g., "fl_live_abc...")
    name = Column(String(255), nullable=False)  # User-defined name for the key
    
    # Permissions and restrictions
    is_active = Column(Boolean, default=True, nullable=False)
    allowed_ips = Column(JSONB, nullable=True)  # List of allowed IP addresses
    rate_limit_override = Column(Integer, nullable=True)  # Custom rate limit for this key
    
    # Usage tracking
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index('idx_api_key_hash', 'key_hash'),
        Index('idx_api_key_user_active', 'user_id', 'is_active'),
    )

    def __repr__(self):
        return f"<APIKey(name='{self.name}', prefix='{self.key_prefix}', active={self.is_active})>"


class RouteLog(Base):
    """Route generation log for usage tracking and debugging"""
    __tablename__ = "route_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=True)
    
    # Request details
    endpoint = Column(String(100), nullable=False)  # /route/auto, /route/upload, etc.
    method = Column(String(10), nullable=False, default="POST")
    
    # Route generation details
    addresses_count = Column(Integer, nullable=False)
    trucks_generated = Column(Integer, nullable=False, default=0)
    stops_processed = Column(Integer, nullable=False, default=0)
    total_miles = Column(Numeric(10, 2), nullable=True)
    fuel_cost = Column(Numeric(10, 2), nullable=True)
    
    # Request metadata
    request_data = Column(JSONB, nullable=True)  # Sanitized request payload
    response_summary = Column(JSONB, nullable=True)  # Key response metrics
    constraints_used = Column(Text, nullable=True)  # Natural language constraints
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)  # Time taken to process
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Client info
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="route_logs")
    api_key = relationship("APIKey")

    __table_args__ = (
        Index('idx_route_log_user_created', 'user_id', 'created_at'),
        Index('idx_route_log_created', 'created_at'),
        Index('idx_route_log_success', 'success'),
    )

    def __repr__(self):
        return f"<RouteLog(user_id='{self.user_id}', endpoint='{self.endpoint}', success={self.success})>"


class UsageRecord(Base):
    """Monthly usage tracking for billing and limits"""
    __tablename__ = "usage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Usage period
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    
    # Usage metrics
    routes_generated = Column(Integer, nullable=False, default=0)
    total_stops_processed = Column(Integer, nullable=False, default=0)
    total_miles_calculated = Column(Numeric(12, 2), nullable=False, default=0)
    api_calls_made = Column(Integer, nullable=False, default=0)
    
    # Cost tracking
    estimated_cost = Column(Numeric(10, 4), nullable=False, default=0)  # Based on usage
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="usage_records")

    __table_args__ = (
        UniqueConstraint('user_id', 'year', 'month', name='uq_usage_user_period'),
        Index('idx_usage_user_period', 'user_id', 'year', 'month'),
        CheckConstraint('month >= 1 AND month <= 12', name='ck_usage_month_valid'),
    )

    def __repr__(self):
        return f"<UsageRecord(user_id='{self.user_id}', period='{self.year}-{self.month:02d}', routes={self.routes_generated})>"


class WebhookLog(Base):
    """Stripe webhook event log for debugging and audit"""
    __tablename__ = "webhook_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Stripe webhook details
    stripe_event_id = Column(String(255), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    
    # Processing details
    processed = Column(Boolean, nullable=False, default=False)
    processing_attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    
    # Event data
    event_data = Column(JSONB, nullable=True)  # Full webhook payload
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_webhook_log_type_created', 'event_type', 'created_at'),
        Index('idx_webhook_log_processed', 'processed'),
    )

    def __repr__(self):
        return f"<WebhookLog(event_id='{self.stripe_event_id}', type='{self.event_type}', processed={self.processed})>"


class AdminMetrics(Base):
    """Daily metrics for admin dashboard"""
    __tablename__ = "admin_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metrics date
    date = Column(DateTime(timezone=True), nullable=False, unique=True, index=True)
    
    # User metrics
    total_users = Column(Integer, nullable=False, default=0)
    new_users = Column(Integer, nullable=False, default=0)
    active_users = Column(Integer, nullable=False, default=0)  # Users who made API calls
    
    # Subscription metrics
    free_tier_users = Column(Integer, nullable=False, default=0)
    starter_tier_users = Column(Integer, nullable=False, default=0)
    professional_tier_users = Column(Integer, nullable=False, default=0)
    enterprise_tier_users = Column(Integer, nullable=False, default=0)
    
    # Usage metrics
    total_routes_generated = Column(Integer, nullable=False, default=0)
    total_api_calls = Column(Integer, nullable=False, default=0)
    total_miles_calculated = Column(Numeric(15, 2), nullable=False, default=0)
    
    # Revenue metrics (in cents)
    daily_revenue = Column(Integer, nullable=False, default=0)
    monthly_recurring_revenue = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<AdminMetrics(date='{self.date.date()}', users={self.total_users}, routes={self.total_routes_generated})>"


# Subscription tier configuration
SUBSCRIPTION_TIERS = {
    SubscriptionTier.FREE: {
        "name": "Free",
        "price": 0,
        "monthly_route_limit": 10,
        "features": [
            "10 routes per month",
            "Basic route optimization",
            "Email support"
        ],
        "stripe_price_id": None
    },
    SubscriptionTier.STARTER: {
        "name": "Starter", 
        "price": 4900,  # $49.00 in cents
        "monthly_route_limit": 200,
        "features": [
            "200 routes per month",
            "Advanced AI optimization",
            "CSV upload support",
            "Priority email support",
            "Basic analytics"
        ],
        "stripe_price_id": "price_starter_monthly"  # Replace with actual Stripe price ID
    },
    SubscriptionTier.PROFESSIONAL: {
        "name": "Professional",
        "price": 19900,  # $199.00 in cents
        "monthly_route_limit": 1000,
        "features": [
            "1,000 routes per month", 
            "Premium AI optimization",
            "Live re-routing",
            "API access",
            "Phone support",
            "Advanced analytics",
            "Custom integrations"
        ],
        "stripe_price_id": "price_professional_monthly"  # Replace with actual Stripe price ID
    },
    SubscriptionTier.ENTERPRISE: {
        "name": "Enterprise",
        "price": 99900,  # $999.00 in cents
        "monthly_route_limit": 10000,
        "features": [
            "10,000 routes per month",
            "Enterprise AI optimization",
            "Dedicated support",
            "Custom deployment",
            "SLA guarantee",
            "Advanced security",
            "Multi-tenant support"
        ],
        "stripe_price_id": "price_enterprise_monthly"  # Replace with actual Stripe price ID
    }
}