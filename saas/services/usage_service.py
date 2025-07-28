from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from decimal import Decimal
import logging

from ..database.models import UsageRecord, RouteLog, User, Subscription, SubscriptionTier

logger = logging.getLogger(__name__)


class UsageService:
    """Service for tracking and managing user usage"""
    
    def __init__(self):
        # Cost per route calculation (for internal tracking)
        self.base_cost_per_route = Decimal("0.10")  # $0.10 per route
        self.ai_processing_cost = Decimal("0.05")   # $0.05 for AI processing
        
    async def record_route_usage(
        self,
        db: Session,
        user_id: str,
        api_key_id: Optional[str],
        endpoint: str,
        addresses_count: int,
        trucks_generated: int,
        stops_processed: int,
        total_miles: Optional[float] = None,
        fuel_cost: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        request_data: Optional[Dict] = None,
        response_summary: Optional[Dict] = None,
        constraints_used: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RouteLog:
        """Record a route generation event"""
        try:
            # Create route log entry
            route_log = RouteLog(
                user_id=user_id,
                api_key_id=api_key_id,
                endpoint=endpoint,
                addresses_count=addresses_count,
                trucks_generated=trucks_generated,
                stops_processed=stops_processed,
                total_miles=Decimal(str(total_miles)) if total_miles else None,
                fuel_cost=Decimal(str(fuel_cost)) if fuel_cost else None,
                processing_time_ms=processing_time_ms,
                success=success,
                error_message=error_message,
                request_data=request_data,
                response_summary=response_summary,
                constraints_used=constraints_used,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(route_log)
            
            # Update monthly usage record only for successful route generations
            if success:
                await self._update_monthly_usage(
                    db, user_id, addresses_count, stops_processed, 
                    total_miles or 0, processing_time_ms
                )
            
            db.commit()
            db.refresh(route_log)
            
            logger.info(f"Route usage recorded for user {user_id}: {endpoint}")
            return route_log
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record route usage: {e}")
            raise
    
    async def _update_monthly_usage(
        self,
        db: Session,
        user_id: str,
        routes_generated: int,
        stops_processed: int,
        miles_calculated: float,
        processing_time_ms: Optional[int] = None
    ):
        """Update monthly usage record"""
        now = datetime.now(timezone.utc)
        year = now.year
        month = now.month
        
        # Calculate estimated cost
        route_cost = self.base_cost_per_route * routes_generated
        ai_cost = self.ai_processing_cost * routes_generated
        estimated_cost = route_cost + ai_cost
        
        # Get or create usage record
        usage_record = db.query(UsageRecord).filter(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.year == year,
                UsageRecord.month == month
            )
        ).first()
        
        if not usage_record:
            usage_record = UsageRecord(
                user_id=user_id,
                year=year,
                month=month,
                routes_generated=0,
                total_stops_processed=0,
                total_miles_calculated=Decimal("0"),
                api_calls_made=0,
                estimated_cost=Decimal("0")
            )
            db.add(usage_record)
        
        # Update usage metrics
        usage_record.routes_generated += routes_generated
        usage_record.total_stops_processed += stops_processed
        usage_record.total_miles_calculated += Decimal(str(miles_calculated))
        usage_record.api_calls_made += 1
        usage_record.estimated_cost += estimated_cost
        usage_record.updated_at = now
    
    async def get_monthly_usage(
        self,
        db: Session,
        user_id: str,
        year: int,
        month: int
    ) -> UsageRecord:
        """Get usage record for a specific month"""
        usage_record = db.query(UsageRecord).filter(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.year == year,
                UsageRecord.month == month
            )
        ).first()
        
        if not usage_record:
            # Return empty usage record
            usage_record = UsageRecord(
                user_id=user_id,
                year=year,
                month=month,
                routes_generated=0,
                total_stops_processed=0,
                total_miles_calculated=Decimal("0"),
                api_calls_made=0,
                estimated_cost=Decimal("0")
            )
        
        return usage_record
    
    async def check_usage_limits(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Check if user is within usage limits"""
        try:
            # Get user subscription
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.subscription:
                return {
                    "allowed": False,
                    "reason": "No subscription found",
                    "usage": {},
                    "limits": {}
                }
            
            subscription = user.subscription
            
            # Get current month usage
            now = datetime.now(timezone.utc)
            current_usage = await self.get_monthly_usage(db, user_id, now.year, now.month)
            
            # Check route limit
            routes_used = current_usage.routes_generated
            route_limit = subscription.monthly_route_limit
            
            # Calculate usage percentage
            usage_percentage = (routes_used / route_limit * 100) if route_limit > 0 else 0
            
            # Determine if usage is allowed
            allowed = routes_used < route_limit
            
            # Warning thresholds
            warning_threshold = route_limit * 0.8  # 80%
            critical_threshold = route_limit * 0.95  # 95%
            
            warning_level = None
            if routes_used >= critical_threshold:
                warning_level = "critical"
            elif routes_used >= warning_threshold:
                warning_level = "warning"
            
            return {
                "allowed": allowed,
                "usage": {
                    "routes_used": routes_used,
                    "routes_limit": route_limit,
                    "usage_percentage": min(usage_percentage, 100),
                    "remaining_routes": max(0, route_limit - routes_used)
                },
                "limits": {
                    "tier": subscription.tier,
                    "monthly_route_limit": route_limit,
                    "period_start": subscription.current_period_start,
                    "period_end": subscription.current_period_end
                },
                "warning_level": warning_level,
                "reason": "Usage limit exceeded" if not allowed else None
            }
            
        except Exception as e:
            logger.error(f"Failed to check usage limits for user {user_id}: {e}")
            return {
                "allowed": False,
                "reason": "Failed to check usage limits",
                "usage": {},
                "limits": {}
            }
    
    async def get_usage_history(
        self,
        db: Session,
        user_id: str,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """Get usage history for the last N months"""
        try:
            # Get usage records for the last N months
            usage_records = db.query(UsageRecord).filter(
                UsageRecord.user_id == user_id
            ).order_by(
                UsageRecord.year.desc(),
                UsageRecord.month.desc()
            ).limit(months).all()
            
            return [
                {
                    "year": record.year,
                    "month": record.month,
                    "routes_generated": record.routes_generated,
                    "total_stops_processed": record.total_stops_processed,
                    "total_miles_calculated": float(record.total_miles_calculated),
                    "api_calls_made": record.api_calls_made,
                    "estimated_cost": float(record.estimated_cost)
                }
                for record in usage_records
            ]
            
        except Exception as e:
            logger.error(f"Failed to get usage history for user {user_id}: {e}")
            return []
    
    async def get_route_logs(
        self,
        db: Session,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get recent route logs for a user"""
        try:
            query = db.query(RouteLog).filter(RouteLog.user_id == user_id)
            
            if success_only:
                query = query.filter(RouteLog.success == True)
            
            route_logs = query.order_by(
                RouteLog.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return [
                {
                    "id": str(log.id),
                    "endpoint": log.endpoint,
                    "addresses_count": log.addresses_count,
                    "trucks_generated": log.trucks_generated,
                    "stops_processed": log.stops_processed,
                    "total_miles": float(log.total_miles) if log.total_miles else None,
                    "fuel_cost": float(log.fuel_cost) if log.fuel_cost else None,
                    "processing_time_ms": log.processing_time_ms,
                    "success": log.success,
                    "error_message": log.error_message,
                    "constraints_used": log.constraints_used,
                    "created_at": log.created_at,
                    "ip_address": log.ip_address
                }
                for log in route_logs
            ]
            
        except Exception as e:
            logger.error(f"Failed to get route logs for user {user_id}: {e}")
            return []
    
    async def get_user_stats(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            # Get all-time stats
            stats = db.query(
                func.count(RouteLog.id).label("total_requests"),
                func.sum(RouteLog.addresses_count).label("total_addresses"),
                func.sum(RouteLog.trucks_generated).label("total_trucks"),
                func.sum(RouteLog.stops_processed).label("total_stops"),
                func.sum(RouteLog.total_miles).label("total_miles"),
                func.sum(RouteLog.fuel_cost).label("total_fuel_cost"),
                func.avg(RouteLog.processing_time_ms).label("avg_processing_time"),
                func.count(RouteLog.id).filter(RouteLog.success == True).label("successful_requests"),
            ).filter(RouteLog.user_id == user_id).first()
            
            # Get current month usage
            now = datetime.now(timezone.utc)
            current_usage = await self.get_monthly_usage(db, user_id, now.year, now.month)
            
            # Calculate success rate
            success_rate = 0
            if stats.total_requests and stats.total_requests > 0:
                success_rate = (stats.successful_requests / stats.total_requests) * 100
            
            return {
                "all_time": {
                    "total_requests": stats.total_requests or 0,
                    "total_addresses": stats.total_addresses or 0,
                    "total_trucks": stats.total_trucks or 0,
                    "total_stops": stats.total_stops or 0,
                    "total_miles": float(stats.total_miles or 0),
                    "total_fuel_cost": float(stats.total_fuel_cost or 0),
                    "avg_processing_time_ms": float(stats.avg_processing_time or 0),
                    "success_rate": success_rate
                },
                "current_month": {
                    "routes_generated": current_usage.routes_generated,
                    "stops_processed": current_usage.total_stops_processed,
                    "miles_calculated": float(current_usage.total_miles_calculated),
                    "api_calls": current_usage.api_calls_made,
                    "estimated_cost": float(current_usage.estimated_cost)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats for {user_id}: {e}")
            return {"all_time": {}, "current_month": {}}
    
    async def cleanup_old_logs(self, db: Session, days: int = 90) -> int:
        """Clean up old route logs (older than specified days)"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Delete old logs
            deleted_count = db.query(RouteLog).filter(
                RouteLog.created_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old route logs")
            return deleted_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup old logs: {e}")
            return 0


# Global usage service instance
usage_service = UsageService()


# Utility functions
async def record_route_usage(db: Session, user_id: str, **kwargs) -> RouteLog:
    """Convenience function to record route usage"""
    return await usage_service.record_route_usage(db, user_id, **kwargs)


async def check_usage_limits(db: Session, user_id: str) -> Dict[str, Any]:
    """Convenience function to check usage limits"""
    return await usage_service.check_usage_limits(db, user_id)