#!/usr/bin/env python3
"""
Usage Tracker with Smart Notifications
Integrates with B2B Portal to send usage alerts
"""

from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
import logging

from email_service import create_notification_service

logger = logging.getLogger(__name__)

class UsageTracker:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.notification_service = create_notification_service()
        
    def track_api_usage(self, company_id: str, api_key_id: str, endpoint: str):
        """Track API usage and trigger notifications if needed"""
        
        # Import here to avoid circular imports
        from b2b_portal.app import Company, APIUsage
        
        # Get company
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            logger.error(f"Company not found: {company_id}")
            return
        
        # Increment usage
        company.current_usage += 1
        
        # Create usage record
        usage = APIUsage(
            id=self._generate_id(),
            company_id=company_id,
            api_key_id=api_key_id,
            endpoint=endpoint,
            timestamp=datetime.utcnow(),
            response_code=200,
            response_time_ms=100.0  # Default values
        )
        
        self.db.add(usage)
        self.db.commit()
        
        # Check for notification triggers
        self._check_usage_alerts(company)
        
        logger.info(f"📊 Usage tracked: {company.name} now at {company.current_usage}/{company.monthly_quota}")
    
    def _check_usage_alerts(self, company):
        """Check if we need to send usage alerts"""
        
        if company.monthly_quota <= 0:
            return  # No quota set
            
        usage_percentage = (company.current_usage / company.monthly_quota) * 100
        
        # Check what alerts we've already sent this month
        last_alert_level = self._get_last_alert_level(company.id)
        
        if usage_percentage >= 200 and last_alert_level < 200:
            # Emergency level - 200%+ usage
            self.notification_service.send_critical_usage_alert(
                company.name,
                company.email,
                company.current_usage,
                company.monthly_quota,
                company.subscription_status
            )
            self._record_alert_sent(company.id, 200)
            logger.warning(f"🚨 Emergency alert sent to {company.name} (200%+ usage)")
            
        elif usage_percentage >= 150 and last_alert_level < 150:
            # Critical level - 150% usage
            self.notification_service.send_critical_usage_alert(
                company.name,
                company.email,
                company.current_usage,
                company.monthly_quota,
                company.subscription_status
            )
            self._record_alert_sent(company.id, 150)
            logger.warning(f"🔥 Critical alert sent to {company.name} (150% usage)")
            
        elif usage_percentage >= 100 and last_alert_level < 100:
            # Quota exceeded - 100% usage
            self.notification_service.send_overage_alert(
                company.name,
                company.email,
                company.current_usage,
                company.monthly_quota,
                company.subscription_status
            )
            self._record_alert_sent(company.id, 100)
            logger.info(f"🚨 Overage alert sent to {company.name} (100% quota exceeded)")
            
        elif usage_percentage >= 80 and last_alert_level < 80:
            # Warning level - 80% usage
            self.notification_service.send_usage_warning(
                company.name,
                company.email,
                company.current_usage,
                company.monthly_quota,
                company.subscription_status
            )
            self._record_alert_sent(company.id, 80)
            logger.info(f"⚠️ Usage warning sent to {company.name} (80% quota used)")
    
    def _get_last_alert_level(self, company_id: str) -> int:
        """Get the highest alert level sent this month"""
        # Simple implementation - store in database or cache
        # For now, return 0 (no alerts sent)
        return 0
    
    def _record_alert_sent(self, company_id: str, alert_level: int):
        """Record that we sent an alert"""
        # Store alert level in database or cache
        # This prevents duplicate alerts
        logger.info(f"Alert level {alert_level} recorded for company {company_id}")
    
    def _generate_id(self) -> str:
        """Generate unique ID for usage records"""
        import secrets
        return secrets.token_urlsafe(16)

# Middleware for automatic usage tracking
class UsageTrackingMiddleware:
    def __init__(self, app, db_session_factory):
        self.app = app
        self.db_session_factory = db_session_factory
        
    async def __call__(self, scope, receive, send):
        """Track API usage for authenticated requests"""
        
        if scope["type"] == "http" and scope["path"].startswith("/v1/"):
            # This is an API call that should be tracked
            
            # Extract company/API key from request (implement based on your auth)
            company_id = self._extract_company_id(scope)
            api_key_id = self._extract_api_key_id(scope)
            
            if company_id and api_key_id:
                # Track usage
                with self.db_session_factory() as db:
                    tracker = UsageTracker(db)
                    tracker.track_api_usage(company_id, api_key_id, scope["path"])
        
        # Continue with normal request processing
        await self.app(scope, receive, send)
    
    def _extract_company_id(self, scope) -> Optional[str]:
        """Extract company ID from request (implement based on your auth system)"""
        # TODO: Implement based on your authentication system
        return None
    
    def _extract_api_key_id(self, scope) -> Optional[str]:
        """Extract API key ID from request (implement based on your auth system)"""
        # TODO: Implement based on your authentication system
        return None 