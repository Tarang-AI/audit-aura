"""
Notification Service
Handles sending alerts via Email, Slack, and WebSocket
"""
import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
import aiohttp
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class NotificationService:
    """Unified notification service for multiple channels"""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_from: str = "noreply@auditaura.com",
        slack_webhook_url: Optional[str] = None
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.slack_webhook_url = slack_webhook_url
        self.websocket_connections: List[Any] = []
    
    def register_websocket(self, ws):
        """Register a WebSocket connection for live alerts"""
        self.websocket_connections.append(ws)
        logger.info(f"WebSocket registered. Total connections: {len(self.websocket_connections)}")
    
    def unregister_websocket(self, ws):
        """Unregister a WebSocket connection"""
        if ws in self.websocket_connections:
            self.websocket_connections.remove(ws)
            logger.info(f"WebSocket unregistered. Total connections: {len(self.websocket_connections)}")
    
    async def send_violation_alert(
        self,
        violation: Dict[str, Any],
        event: Dict[str, Any],
        evidence: str,
        channels: List[str] = ["websocket", "email", "slack"]
    ):
        """
        Send violation alert through specified channels
        
        Args:
            violation: Violated control information
            event: Event that triggered the violation
            evidence: Generated evidence/explanation
            channels: List of channels to send to (websocket, email, slack)
        """
        try:
            # Format alert message
            alert_data = self._format_alert(violation, event, evidence)
            
            # Send to each channel
            if "websocket" in channels:
                await self._send_websocket_alert(alert_data)
            
            if "email" in channels and self.smtp_host:
                await self._send_email_alert(alert_data)
            
            if "slack" in channels and self.slack_webhook_url:
                await self._send_slack_alert(alert_data)
            
            logger.info(f"Alert sent for violation: {violation.get('control_id', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error sending violation alert: {e}")
    
    def _format_alert(
        self,
        violation: Dict[str, Any],
        event: Dict[str, Any],
        evidence: str
    ) -> Dict[str, Any]:
        """Format alert data"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "violation",
            "severity": violation.get("severity", "medium"),
            "control_id": violation.get("control_id", "Unknown"),
            "standard": violation.get("standard", "Unknown"),
            "category": violation.get("category", "Unknown"),
            "description": violation.get("description", ""),
            "remediation": violation.get("remediation", ""),
            "event": event,
            "evidence": evidence
        }
    
    async def _send_websocket_alert(self, alert_data: Dict[str, Any]):
        """Send alert via WebSocket"""
        try:
            message = json.dumps(alert_data)
            
            # Send to all connected clients
            disconnected = []
            for ws in self.websocket_connections:
                try:
                    await ws.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    disconnected.append(ws)
            
            # Remove disconnected clients
            for ws in disconnected:
                self.unregister_websocket(ws)
            
        except Exception as e:
            logger.error(f"Error sending WebSocket alert: {e}")
    
    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send alert via Email"""
        try:
            if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
                logger.debug("Email not configured, skipping email alert")
                return
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 Compliance Violation: {alert_data['control_id']}"
            msg['From'] = self.smtp_from
            msg['To'] = self.smtp_user  # In production, this should be configurable
            
            # Create HTML body
            html_body = self._create_email_html(alert_data)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent for {alert_data['control_id']}")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    async def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """Send alert via Slack"""
        try:
            if not self.slack_webhook_url:
                logger.debug("Slack not configured, skipping Slack alert")
                return
            
            # Create Slack message
            slack_message = self._create_slack_message(alert_data)
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook_url,
                    json=slack_message,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent for {alert_data['control_id']}")
                    else:
                        logger.error(f"Slack API error: {response.status}")
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def _create_email_html(self, alert_data: Dict[str, Any]) -> str:
        """Create HTML email body"""
        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#17a2b8"
        }
        
        color = severity_colors.get(alert_data['severity'], "#6c757d")
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="border-left: 4px solid {color}; padding-left: 20px;">
                <h2 style="color: {color};">🚨 Compliance Violation Detected</h2>
                
                <p><strong>Control ID:</strong> {alert_data['control_id']}</p>
                <p><strong>Standard:</strong> {alert_data['standard']}</p>
                <p><strong>Category:</strong> {alert_data['category']}</p>
                <p><strong>Severity:</strong> <span style="color: {color};">{alert_data['severity'].upper()}</span></p>
                <p><strong>Time:</strong> {alert_data['timestamp']}</p>
                
                <h3>Description</h3>
                <p>{alert_data['description']}</p>
                
                <h3>Remediation</h3>
                <p>{alert_data['remediation']}</p>
                
                <h3>Evidence</h3>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{alert_data['evidence']}</pre>
                
                <h3>Event Details</h3>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{json.dumps(alert_data['event'], indent=2)}</pre>
            </div>
        </body>
        </html>
        """
    
    def _create_slack_message(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack message payload"""
        severity_emojis = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵"
        }
        
        emoji = severity_emojis.get(alert_data['severity'], "⚪")
        
        return {
            "text": f"{emoji} Compliance Violation: {alert_data['control_id']}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Compliance Violation Detected"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Control ID:*\n{alert_data['control_id']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{alert_data['severity'].upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Standard:*\n{alert_data['standard']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Category:*\n{alert_data['category']}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{alert_data['description']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Remediation:*\n{alert_data['remediation']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Evidence:*\n```{alert_data['evidence'][:500]}```"
                    }
                }
            ]
        }

# Made with Bob
