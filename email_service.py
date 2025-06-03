#!/usr/bin/env python3
"""
Email Notification Service for BlockVerify
Sends usage alerts, billing notifications, and account updates
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Configuration from environment variables
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@blockverify.com")
        self.from_name = os.getenv("FROM_NAME", "BlockVerify")
        
    def send_email(self, to: str, subject: str, body: str, html_body: Optional[str] = None):
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to
            
            # Add text version
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML version if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"📧 Email sent to {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to}: {e}")
            return False

class UsageNotificationService:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
        
    def send_usage_warning(self, company_name: str, contact_email: str, 
                          current_usage: int, monthly_limit: int, plan_type: str):
        """Send 80% usage warning"""
        usage_pct = (current_usage / monthly_limit) * 100
        
        subject = f"⚠️ {usage_pct:.0f}% API quota used this month"
        
        body = f"""Hi {company_name},

You've used {current_usage:,} of your {monthly_limit:,} monthly API calls ({usage_pct:.0f}%).

Current plan: {plan_type.title()}
Remaining calls: {monthly_limit - current_usage:,}

To avoid overage charges, consider upgrading your plan:
https://portal.blockverify.com/upgrade

Overage rates:
• Starter: $0.03 per extra call
• Professional: $0.02 per extra call
• Enterprise: $0.01 per extra call

Questions? Reply to this email or visit our support center.

Best regards,
The BlockVerify Team

---
BlockVerify - Privacy-preserving age verification
https://blockverify.com
"""
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #ff9800; margin: 0;">⚠️ API Usage Alert</h2>
            </div>
            
            <p>Hi <strong>{company_name}</strong>,</p>
            
            <p>You've used <strong>{current_usage:,}</strong> of your <strong>{monthly_limit:,}</strong> monthly API calls (<strong>{usage_pct:.0f}%</strong>).</p>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0;">
                <strong>Current plan:</strong> {plan_type.title()}<br>
                <strong>Remaining calls:</strong> {monthly_limit - current_usage:,}
            </div>
            
            <p>To avoid overage charges, consider upgrading your plan:</p>
            <p><a href="https://portal.blockverify.com/upgrade" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Upgrade Plan</a></p>
            
            <h3>Overage Rates:</h3>
            <ul>
                <li><strong>Starter:</strong> $0.03 per extra call</li>
                <li><strong>Professional:</strong> $0.02 per extra call</li>
                <li><strong>Enterprise:</strong> $0.01 per extra call</li>
            </ul>
            
            <p>Questions? Reply to this email or visit our <a href="https://blockverify.com/support">support center</a>.</p>
            
            <p>Best regards,<br>The BlockVerify Team</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                BlockVerify - Privacy-preserving age verification<br>
                <a href="https://blockverify.com">https://blockverify.com</a>
            </p>
        </div>
        """
        
        return self.email_service.send_email(contact_email, subject, body, html_body)
    
    def send_overage_alert(self, company_name: str, contact_email: str,
                          current_usage: int, monthly_limit: int, plan_type: str):
        """Send quota exceeded alert"""
        overage_count = current_usage - monthly_limit
        
        # Calculate overage cost based on plan
        overage_rates = {"starter": 3, "professional": 2, "enterprise": 1}
        rate_cents = overage_rates.get(plan_type.lower(), 3)
        overage_cost = (overage_count * rate_cents) / 100
        
        subject = f"🚨 Monthly quota exceeded - ${overage_cost:.2f} in overage charges"
        
        body = f"""QUOTA EXCEEDED ALERT

Hi {company_name},

You've exceeded your monthly quota of {monthly_limit:,} API calls.

Current usage: {current_usage:,} calls
Overage: {overage_count:,} calls
Additional charges: ${overage_cost:.2f}

Your service continues uninterrupted, but additional usage will be billed at ${rate_cents/100:.2f} per call.

Action recommended:
1. Upgrade to a higher plan: https://portal.blockverify.com/upgrade
2. Monitor your usage: https://portal.blockverify.com/dashboard
3. Contact support if this usage is unexpected

Current plan: {plan_type.title()}
Overage rate: ${rate_cents/100:.2f} per call

Questions? Reply to this email immediately.

Best regards,
The BlockVerify Team
"""
        
        return self.email_service.send_email(contact_email, subject, body)
    
    def send_critical_usage_alert(self, company_name: str, contact_email: str,
                                 current_usage: int, monthly_limit: int, plan_type: str):
        """Send critical usage alert (150%+ usage)"""
        overage_count = current_usage - monthly_limit
        usage_pct = (current_usage / monthly_limit) * 100
        
        subject = f"🔥 URGENT: High API usage detected ({usage_pct:.0f}% of quota)"
        
        body = f"""URGENT: HIGH USAGE ALERT

Company: {company_name}
Current usage: {current_usage:,} calls ({usage_pct:.0f}% of quota)
Monthly limit: {monthly_limit:,} calls
Overage: {overage_count:,} calls

This requires immediate attention.

Action required:
1. Review your API usage patterns immediately
2. Consider upgrading: https://portal.blockverify.com/upgrade
3. Contact support if this is unexpected: support@blockverify.com

If this usage is intentional, please ignore this alert.
If this usage is unexpected, please contact support immediately.

Emergency support: support@blockverify.com

Best regards,
BlockVerify Team
"""
        
        # Also send internal alert
        self.email_service.send_email(
            "alerts@blockverify.com",
            f"High usage alert: {company_name}",
            f"Company {company_name} has {usage_pct:.0f}% usage ({current_usage:,} calls). Review account."
        )
        
        return self.email_service.send_email(contact_email, subject, body)

# Integration with existing billing system
def create_notification_service():
    """Create and return notification service instance"""
    email_service = EmailService()
    return UsageNotificationService(email_service) 