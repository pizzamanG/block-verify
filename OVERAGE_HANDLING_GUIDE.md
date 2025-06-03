"""
Smart Overage Notification System
Sends alerts before customers hit expensive overages
"""

from enum import Enum
from datetime import datetime
from typing import Optional
import logging

class AlertLevel(Enum):
    WARNING_80 = "80_percent"
    ALERT_100 = "100_percent"  
    CRITICAL_150 = "150_percent"
    EMERGENCY_200 = "200_percent"

class OverageManager:
    def __init__(self, email_service, db_session):
        self.email_service = email_service
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    def check_and_notify_overage(self, client_id: str, current_usage: int, monthly_limit: int):
        """Check usage and send appropriate notifications"""
        
        usage_percentage = (current_usage / monthly_limit) * 100
        
        # Get last notification sent
        last_alert = self.get_last_alert_sent(client_id)
        
        if usage_percentage >= 200 and last_alert != AlertLevel.EMERGENCY_200:
            self.send_emergency_alert(client_id, current_usage, monthly_limit)
            self.record_alert_sent(client_id, AlertLevel.EMERGENCY_200)
            
        elif usage_percentage >= 150 and last_alert != AlertLevel.CRITICAL_150:
            self.send_critical_alert(client_id, current_usage, monthly_limit)
            self.record_alert_sent(client_id, AlertLevel.CRITICAL_150)
            
        elif usage_percentage >= 100 and last_alert != AlertLevel.ALERT_100:
            self.send_quota_exceeded_alert(client_id, current_usage, monthly_limit)
            self.record_alert_sent(client_id, AlertLevel.ALERT_100)
            
        elif usage_percentage >= 80 and last_alert != AlertLevel.WARNING_80:
            self.send_warning_alert(client_id, current_usage, monthly_limit)
            self.record_alert_sent(client_id, AlertLevel.WARNING_80)
    
    def send_warning_alert(self, client_id: str, usage: int, limit: int):
        """80% usage warning"""
        client = self.get_client(client_id)
        
        self.email_service.send_email(
            to=client.contact_email,
            subject="⚠️ 80% API quota used this month",
            body=f"""
            Hi {client.business_name},
            
            You've used {usage:,} of your {limit:,} monthly API calls (80%).
            
            Current plan: {client.plan_type.title()}
            Overage rate: $0.{self.get_overage_rate(client.plan_type):02d} per call
            
            Consider upgrading to avoid overage charges:
            {self.get_upgrade_url(client_id)}
            
            Best regards,
            BlockVerify Team
            """
        )
    
    def send_quota_exceeded_alert(self, client_id: str, usage: int, limit: int):
        """100% quota exceeded"""
        client = self.get_client(client_id)
        overage_count = usage - limit
        overage_cost = overage_count * (self.get_overage_rate(client.plan_type) / 100)
        
        self.email_service.send_email(
            to=client.contact_email,
            subject="🚨 Monthly quota exceeded - overage billing active",
            body=f"""
            Hi {client.business_name},
            
            You've exceeded your monthly quota of {limit:,} API calls.
            
            Current usage: {usage:,} calls
            Overage: {overage_count:,} calls
            Additional charges: ${overage_cost:.2f}
            
            Your service continues uninterrupted, but additional usage 
            will be billed at $0.{self.get_overage_rate(client.plan_type):02d} per call.
            
            Upgrade to a higher plan: {self.get_upgrade_url(client_id)}
            
            Questions? Reply to this email.
            """
        )
    
    def send_critical_alert(self, client_id: str, usage: int, limit: int):
        """150% usage - significant overage"""
        client = self.get_client(client_id)
        overage_count = usage - limit
        overage_cost = overage_count * (self.get_overage_rate(client.plan_type) / 100)
        
        self.email_service.send_email(
            to=client.contact_email,
            subject="🔥 High overage usage detected",
            body=f"""
            URGENT: High API usage detected
            
            Company: {client.business_name}
            Current usage: {usage:,} calls (150% of quota)
            Estimated overage charges: ${overage_cost:.2f}
            
            Action required:
            1. Review your API usage patterns
            2. Consider upgrading: {self.get_upgrade_url(client_id)}
            3. Contact support if this is unexpected
            
            Support: support@blockverify.com
            """
        )
    
    def send_emergency_alert(self, client_id: str, usage: int, limit: int):
        """200%+ usage - emergency intervention"""
        client = self.get_client(client_id)
        
        # Send to both customer AND internal team
        self.email_service.send_email(
            to=[client.contact_email, "alerts@blockverify.com"],
            subject="🚨 EMERGENCY: Extreme overage usage",
            body=f"""
            EMERGENCY OVERAGE ALERT
            
            Company: {client.business_name}
            Usage: {usage:,} calls (200%+ of quota)
            
            This requires immediate attention.
            
            Customer: Please contact support immediately
            Internal: Review account for potential abuse
            """
        )
        
        # Optional: Implement rate limiting at this point
        self.consider_rate_limiting(client_id)

# Integration with your existing billing system
def enhanced_record_usage(self, client_id: str, api_key_id: str, usage_type: UsageType, 
                         endpoint: str = None, **metadata) -> UsageRecord:
    """Enhanced version with overage notifications"""
    
    # Original usage recording
    usage_record = self.original_record_usage(client_id, api_key_id, usage_type, endpoint, **metadata)
    
    # Get updated client data
    client = self.db.query(Client).filter(Client.id == client_id).first()
    
    # Check for overage notifications
    overage_manager = OverageManager(self.email_service, self.db)
    overage_manager.check_and_notify_overage(
        client_id, 
        client.current_usage, 
        client.monthly_limit
    )
    
    return usage_record 