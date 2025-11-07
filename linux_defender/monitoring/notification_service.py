#!/usr/bin/env python3
"""
Notification Service - Multi-channel alert system
Inspired by claude-code-daemon-dev notification architecture

Supported channels:
- Termux-API notifications (Android)
- Slack webhooks
- Email (SMTP)
- Generic webhooks
- Console logging
"""

import os
import json
import subprocess
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque


class NotificationChannel:
    """Base class for notification channels"""

    def __init__(self, channel_type: str, logger=None):
        self.channel_type = channel_type
        self.logger = logger

    def log(self, message):
        """Log message"""
        if self.logger:
            self.logger(message)

    async def send(self, alert: Dict[str, Any]):
        """Send alert through this channel - override in subclasses"""
        raise NotImplementedError


class TermuxAPIChannel(NotificationChannel):
    """Termux-API notification channel (Android)"""

    def __init__(self, logger=None):
        super().__init__('termux-api', logger)

    async def send(self, alert: Dict[str, Any]):
        """Send notification via termux-notification"""
        try:
            # Map severity to notification priority
            priority_map = {
                'info': 'default',
                'warning': 'high',
                'critical': 'max',
                'success': 'default'
            }
            priority = priority_map.get(alert['severity'], 'default')

            # Build termux-notification command
            cmd = [
                'termux-notification',
                '--title', f"Defender: {alert['type']}",
                '--content', alert['message'],
                '--priority', priority,
                '--id', f"defender-{alert['type']}"
            ]

            # Add sound for critical alerts
            if alert['severity'] == 'critical':
                cmd.extend(['--sound', '--vibrate', '500,500,500'])

            subprocess.run(cmd, capture_output=True, timeout=5)
            self.log(f"✓ Termux-API notification sent: {alert['type']}")

        except Exception as e:
            self.log(f"⚠️ Failed to send Termux-API notification: {e}")


class SlackChannel(NotificationChannel):
    """Slack webhook channel"""

    def __init__(self, webhook_url: str, logger=None):
        super().__init__('slack', logger)
        self.webhook_url = webhook_url

    async def send(self, alert: Dict[str, Any]):
        """Send alert to Slack via webhook"""
        try:
            # Map severity to colors
            color_map = {
                'info': '#36a64f',
                'warning': '#ff9900',
                'critical': '#ff0000',
                'success': '#00ff00'
            }
            color = color_map.get(alert['severity'], '#808080')

            # Format data fields for Slack
            fields = []
            if alert.get('data'):
                for key, value in alert['data'].items():
                    fields.append({
                        'title': key.replace('_', ' ').title(),
                        'value': str(value) if not isinstance(value, dict) else json.dumps(value),
                        'short': len(str(value)) < 30
                    })

            payload = {
                'text': 'Linux Defender Alert',
                'attachments': [{
                    'color': color,
                    'title': alert['type'],
                    'text': alert['message'],
                    'fields': fields,
                    'footer': 'Linux Defender',
                    'ts': int(datetime.now().timestamp())
                }]
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            self.log(f"✓ Slack notification sent: {alert['type']}")

        except Exception as e:
            self.log(f"⚠️ Failed to send Slack notification: {e}")


class EmailChannel(NotificationChannel):
    """Email notification channel (SMTP)"""

    def __init__(self, smtp_config: Dict[str, str], logger=None):
        super().__init__('email', logger)
        self.smtp_host = smtp_config.get('host')
        self.smtp_port = smtp_config.get('port', 587)
        self.smtp_user = smtp_config.get('user')
        self.smtp_pass = smtp_config.get('password')
        self.email_to = smtp_config.get('to', self.smtp_user)

    async def send(self, alert: Dict[str, Any]):
        """Send alert via email"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Linux Defender Alert: {alert['type']}"
            msg['From'] = self.smtp_user
            msg['To'] = self.email_to

            # HTML email body
            html_body = self._format_html_alert(alert)
            msg.attach(MIMEText(html_body, 'html'))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            self.log(f"✓ Email notification sent: {alert['type']}")

        except Exception as e:
            self.log(f"⚠️ Failed to send email notification: {e}")

    def _format_html_alert(self, alert: Dict[str, Any]) -> str:
        """Format alert as HTML email"""
        color_map = {
            'info': '#2196F3',
            'warning': '#FF9800',
            'critical': '#F44336',
            'success': '#4CAF50'
        }
        color = color_map.get(alert['severity'], '#9E9E9E')

        data_html = ''
        if alert.get('data'):
            data_html = f'<div class="alert-data"><pre>{json.dumps(alert["data"], indent=2)}</pre></div>'

        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert-container {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin: 20px;
        }}
        .alert-header {{
            font-size: 18px;
            font-weight: bold;
            color: {color};
            margin-bottom: 10px;
        }}
        .alert-message {{
            margin: 10px 0;
        }}
        .alert-data {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 3px;
            font-family: monospace;
        }}
        .alert-footer {{
            margin-top: 20px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="alert-container">
        <div class="alert-header">{alert['type']}</div>
        <div class="alert-message">{alert['message']}</div>
        {data_html}
        <div class="alert-footer">
            Timestamp: {alert['timestamp']}<br>
            Severity: {alert['severity']}<br>
            Source: Linux Defender
        </div>
    </div>
</body>
</html>
"""


class WebhookChannel(NotificationChannel):
    """Generic webhook channel"""

    def __init__(self, webhook_url: str, logger=None):
        super().__init__('webhook', logger)
        self.webhook_url = webhook_url

    async def send(self, alert: Dict[str, Any]):
        """Send alert to generic webhook"""
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                **alert
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            self.log(f"✓ Webhook notification sent: {alert['type']}")

        except Exception as e:
            self.log(f"⚠️ Failed to send webhook notification: {e}")


class ConsoleChannel(NotificationChannel):
    """Console logging channel"""

    def __init__(self, logger=None):
        super().__init__('console', logger)

    async def send(self, alert: Dict[str, Any]):
        """Print alert to console with color coding"""
        # ANSI color codes
        color_map = {
            'info': '\x1b[34m',      # Blue
            'warning': '\x1b[33m',   # Yellow
            'critical': '\x1b[31m',  # Red
            'success': '\x1b[32m'    # Green
        }
        reset = '\x1b[0m'
        color = color_map.get(alert['severity'], reset)

        print(f"{color}[{alert['severity'].upper()}]{reset} {alert['type']}: {alert['message']}")

        if alert.get('data'):
            print(f"Details: {json.dumps(alert['data'], indent=2)}")


class NotificationService:
    """Multi-channel notification service"""

    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        self.logger = logger
        self.channels = {}
        self.alert_history = deque(maxlen=1000)  # Keep last 1000 alerts

    def log(self, message):
        """Log message"""
        if self.logger:
            self.logger(message)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")

    async def initialize(self):
        """Initialize notification channels based on config"""

        # Termux-API (if on Android/Termux)
        if self.config.get('termux_notifications', True):
            try:
                # Check if termux-notification is available
                result = subprocess.run(['which', 'termux-notification'],
                                       capture_output=True)
                if result.returncode == 0:
                    self.channels['termux-api'] = TermuxAPIChannel(self.logger)
                    self.log("✓ Termux-API notification channel initialized")
            except Exception as e:
                self.log(f"⚠️ Termux-API not available: {e}")

        # Slack webhook
        slack_webhook = self.config.get('slack_webhook')
        if slack_webhook:
            self.channels['slack'] = SlackChannel(slack_webhook, self.logger)
            self.log("✓ Slack notification channel initialized")

        # Email (SMTP)
        smtp_config = self.config.get('smtp')
        if smtp_config and smtp_config.get('host'):
            self.channels['email'] = EmailChannel(smtp_config, self.logger)
            self.log("✓ Email notification channel initialized")

        # Generic webhook
        webhook_url = self.config.get('webhook_url')
        if webhook_url:
            self.channels['webhook'] = WebhookChannel(webhook_url, self.logger)
            self.log("✓ Generic webhook channel initialized")

        # Console (always enabled)
        self.channels['console'] = ConsoleChannel(self.logger)
        self.log("✓ Console notification channel initialized")

        self.log(f"Notification service initialized with {len(self.channels)} channels")

    async def send_alert(self, alert_type: str, message: str,
                        severity: str = 'info', data: Optional[Dict] = None):
        """Send alert through all appropriate channels"""

        # Build alert object
        alert = {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

        if data:
            alert['data'] = data

        # Store in history
        self.alert_history.append(alert)

        # Send to appropriate channels
        for channel_name, channel in self.channels.items():
            if self._should_send_to_channel(alert, channel_name):
                try:
                    await channel.send(alert)
                except Exception as e:
                    self.log(f"❌ Failed to send alert via {channel_name}: {e}")

    def _should_send_to_channel(self, alert: Dict[str, Any], channel_name: str) -> bool:
        """Determine if alert should be sent to specific channel"""
        severity = alert['severity']

        # Console always gets everything
        if channel_name == 'console':
            return True

        # Critical alerts go to all channels
        if severity == 'critical':
            return True

        # Warnings go to all except email
        if severity == 'warning' and channel_name != 'email':
            return True

        # Info and success only to console (unless overridden in config)
        if severity in ['info', 'success']:
            return self.config.get(f'{channel_name}_all_severities', False)

        return False

    def get_recent_alerts(self, limit: int = 100) -> List[Dict]:
        """Get recent alerts from history"""
        return list(self.alert_history)[-limit:]

    def clear_history(self) -> int:
        """Clear alert history"""
        count = len(self.alert_history)
        self.alert_history.clear()
        self.log(f"Cleared {count} alerts from history")
        return count

    def get_status(self) -> Dict[str, Any]:
        """Get notification service status"""
        return {
            'channels': list(self.channels.keys()),
            'alert_history_size': len(self.alert_history),
            'recent_alerts': [
                {
                    'type': a['type'],
                    'severity': a['severity'],
                    'timestamp': a['timestamp']
                }
                for a in list(self.alert_history)[-5:]
            ]
        }

    async def test_notifications(self):
        """Send test notifications to all channels"""
        await self.send_alert(
            alert_type='test',
            message='This is a test notification from Linux Defender',
            severity='info',
            data={
                'test': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        self.log("✓ Test notifications sent to all channels")


# Convenience function for creating notification service
def create_notification_service(config_path: Optional[str] = None, logger=None) -> NotificationService:
    """Create notification service from config file"""

    # Default config
    config = {
        'termux_notifications': True,
        'slack_webhook': os.getenv('SLACK_WEBHOOK'),
        'webhook_url': os.getenv('WEBHOOK_URL'),
        'smtp': {
            'host': os.getenv('SMTP_HOST'),
            'port': int(os.getenv('SMTP_PORT', 587)),
            'user': os.getenv('SMTP_USER'),
            'password': os.getenv('SMTP_PASS'),
            'to': os.getenv('EMAIL_TO')
        }
    }

    # Load from config file if provided
    if config_path and Path(config_path).exists():
        try:
            with open(config_path) as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            if logger:
                logger(f"⚠️ Failed to load notification config: {e}")

    return NotificationService(config, logger)
