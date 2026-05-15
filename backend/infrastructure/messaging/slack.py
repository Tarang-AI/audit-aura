"""
Slack Notification Service
Sends alerts to Slack channels via webhooks
"""
import logging
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Handles Slack webhook notifications"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier
        
        Args:
            webhook_url: Slack webhook URL (optional, can be set later)
        """
        self.webhook_url = webhook_url
        self.enabled = webhook_url is not None
        
    def set_webhook_url(self, webhook_url: str):
        """Set or update the Slack webhook URL"""
        self.webhook_url = webhook_url
        self.enabled = True
        logger.info("Slack webhook URL configured")
        
    async def send_message(self, text: str, blocks: Optional[list] = None) -> bool:
        """
        Send a message to Slack
        
        Args:
            text: Plain text message (fallback)
            blocks: Slack Block Kit blocks for rich formatting
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled or not self.webhook_url:
            logger.warning("Slack notifications disabled - no webhook URL configured")
            return False
            
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack message sent successfully")
                        return True
                    else:
                        logger.error(f"Slack API error: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    async def send_violation_alert(self, violation: Dict[str, Any]) -> bool:
        """
        Send a violation alert to Slack
        
        Args:
            violation: Violation data dictionary
            
        Returns:
            bool: True if successful
        """
        severity = violation.get("severity", "unknown")
        control_id = violation.get("control_id", "Unknown")
        description = violation.get("description", "No description")
        resource = violation.get("resource", "N/A")
        
        # Severity emoji and color
        severity_config = {
            "critical": {"emoji": "🔴", "color": "#d32f2f"},
            "high": {"emoji": "🟠", "color": "#f57c00"},
            "medium": {"emoji": "🟡", "color": "#fbc02d"},
            "low": {"emoji": "🔵", "color": "#1976d2"}
        }
        
        config = severity_config.get(severity, {"emoji": "⚪", "color": "#757575"})
        
        text = f"{config['emoji']} *{severity.upper()}* Compliance Violation Detected"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{config['emoji']} Compliance Violation Alert"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{severity.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Control ID:*\n{control_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Resource:*\n{resource}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{description}"
                }
            }
        ]
        
        # Add remediation if available
        if violation.get("remediation"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Remediation:*\n{violation['remediation']}"
                }
            })
        
        # Add divider
        blocks.append({"type": "divider"})
        
        return await self.send_message(text, blocks)
    
    async def send_compliance_update(self, compliance_data: Dict[str, Any]) -> bool:
        """
        Send a compliance score update to Slack
        
        Args:
            compliance_data: Compliance score data
            
        Returns:
            bool: True if successful
        """
        overall_score = compliance_data.get("overall_score", 0)
        standards = compliance_data.get("standards", {})
        
        # Determine emoji based on score
        if overall_score >= 0.9:
            emoji = "✅"
            color = "#4caf50"
        elif overall_score >= 0.75:
            emoji = "⚠️"
            color = "#ff9800"
        else:
            emoji = "❌"
            color = "#f44336"
        
        text = f"{emoji} Compliance Score Update: {overall_score*100:.1f}%"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Compliance Score Update"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Overall Compliance:* {overall_score*100:.1f}%"
                }
            }
        ]
        
        # Add standards breakdown
        if standards:
            fields = []
            for standard, score in standards.items():
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{standard}:*\n{score*100:.1f}%"
                })
            
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })
        
        return await self.send_message(text, blocks)
    
    async def send_pr_update(self, pr_data: Dict[str, Any]) -> bool:
        """
        Send a PR status update to Slack
        
        Args:
            pr_data: PR data dictionary
            
        Returns:
            bool: True if successful
        """
        number = pr_data.get("number", "Unknown")
        title = pr_data.get("title", "No title")
        status = pr_data.get("status", "unknown")
        url = pr_data.get("url", "")
        
        status_config = {
            "merged": {"emoji": "✅", "text": "Merged"},
            "open": {"emoji": "🔄", "text": "Opened"},
            "closed": {"emoji": "❌", "text": "Closed"}
        }
        
        config = status_config.get(status, {"emoji": "📝", "text": status.title()})
        
        text = f"{config['emoji']} PR #{number} {config['text']}: {title}"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{config['emoji']} *PR #{number} {config['text']}*\n{title}"
                }
            }
        ]
        
        if url:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{url}|View on GitHub>"
                }
            })
        
        return await self.send_message(text, blocks)


# Global Slack notifier instance
_slack_notifier: Optional[SlackNotifier] = None


def get_slack_notifier(webhook_url: Optional[str] = None) -> SlackNotifier:
    """Get or create the global Slack notifier instance"""
    global _slack_notifier
    if _slack_notifier is None:
        _slack_notifier = SlackNotifier(webhook_url)
    elif webhook_url and webhook_url != _slack_notifier.webhook_url:
        _slack_notifier.set_webhook_url(webhook_url)
    return _slack_notifier