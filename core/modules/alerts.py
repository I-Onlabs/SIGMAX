"""
Alert and Notification System for SIGMAX

Provides multi-channel alerting for critical events:
- Risk limit breaches
- Large losses
- Trade execution failures
- System errors
- Arbitrage opportunities
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
from loguru import logger
import json

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not available. Webhook alerts disabled.")


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertChannel(Enum):
    """Alert delivery channels"""
    CONSOLE = "console"
    WEBHOOK = "webhook"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"


@dataclass
class Alert:
    """Alert message"""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'tags': self.tags
        }


class AlertManager:
    """
    Centralized alert management system

    Features:
    - Multi-channel delivery
    - Alert throttling to prevent spam
    - Priority-based routing
    - Alert history tracking
    - Customizable alert rules
    """

    def __init__(
        self,
        enabled_channels: Optional[List[AlertChannel]] = None,
        webhook_urls: Optional[Dict[str, str]] = None,
        throttle_seconds: int = 60
    ):
        self.enabled_channels = enabled_channels or [AlertChannel.CONSOLE]
        self.webhook_urls = webhook_urls or {}
        self.throttle_seconds = throttle_seconds

        # Alert history
        self.alert_history: List[Alert] = []
        self.max_history = 1000

        # Throttling
        self.last_alert_time: Dict[str, datetime] = {}

        # Custom handlers
        self.custom_handlers: Dict[AlertChannel, Callable] = {}

        # Alert rules
        self.alert_rules: List[Dict[str, Any]] = []

        logger.info(f"✓ Alert Manager initialized with channels: {[c.value for c in self.enabled_channels]}")

    def add_custom_handler(self, channel: AlertChannel, handler: Callable):
        """Register custom alert handler"""
        self.custom_handlers[channel] = handler
        logger.info(f"✓ Custom handler registered for {channel.value}")

    def add_alert_rule(
        self,
        condition: str,
        level: AlertLevel,
        title: str,
        message_template: str,
        channels: Optional[List[AlertChannel]] = None
    ):
        """
        Add custom alert rule

        Args:
            condition: Python expression to evaluate
            level: Alert level
            title: Alert title
            message_template: Message template with {variable} placeholders
            channels: Specific channels for this rule
        """
        rule = {
            'condition': condition,
            'level': level,
            'title': title,
            'message_template': message_template,
            'channels': channels or self.enabled_channels
        }
        self.alert_rules.append(rule)
        logger.info(f"✓ Alert rule added: {title}")

    async def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        channels: Optional[List[AlertChannel]] = None
    ):
        """
        Send alert through configured channels

        Args:
            level: Alert severity
            title: Alert title
            message: Alert message
            data: Additional data
            tags: Alert tags for filtering
            channels: Override default channels
        """
        # Check throttling
        alert_key = f"{title}:{message}"
        if alert_key in self.last_alert_time:
            time_since_last = (datetime.now() - self.last_alert_time[alert_key]).total_seconds()
            if time_since_last < self.throttle_seconds:
                logger.debug(f"Alert throttled: {title}")
                return

        # Create alert
        alert = Alert(
            level=level,
            title=title,
            message=message,
            data=data or {},
            tags=tags or []
        )

        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)

        # Update throttle time
        self.last_alert_time[alert_key] = datetime.now()

        # Send through channels
        target_channels = channels or self.enabled_channels

        tasks = []
        for channel in target_channels:
            if channel == AlertChannel.CONSOLE:
                tasks.append(self._send_console(alert))
            elif channel == AlertChannel.WEBHOOK:
                tasks.append(self._send_webhook(alert))
            elif channel in self.custom_handlers:
                tasks.append(self.custom_handlers[channel](alert))
            else:
                logger.warning(f"Channel {channel.value} not configured")

        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"✓ Alert sent: [{level.value.upper()}] {title}")

    async def _send_console(self, alert: Alert):
        """Send alert to console"""
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨",
            AlertLevel.EMERGENCY: "🔴"
        }

        emoji = emoji_map.get(alert.level, "📢")

        logger.log(
            "INFO" if alert.level == AlertLevel.INFO else "WARNING" if alert.level == AlertLevel.WARNING else "ERROR",
            f"{emoji} ALERT [{alert.level.value.upper()}] {alert.title}: {alert.message}"
        )

    async def _send_webhook(self, alert: Alert):
        """Send alert via webhook"""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available, webhook skipped")
            return

        if 'default' not in self.webhook_urls:
            logger.warning("No default webhook URL configured")
            return

        url = self.webhook_urls['default']

        try:
            async with aiohttp.ClientSession() as session:
                payload = alert.to_dict()
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.debug(f"✓ Webhook alert sent to {url}")
                    else:
                        logger.error(f"Webhook failed: {response.status}")
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")

    def get_recent_alerts(
        self,
        limit: int = 50,
        level: Optional[AlertLevel] = None,
        tags: Optional[List[str]] = None
    ) -> List[Alert]:
        """
        Get recent alerts with optional filtering

        Args:
            limit: Maximum number of alerts
            level: Filter by level
            tags: Filter by tags (any match)

        Returns:
            List of filtered alerts
        """
        alerts = self.alert_history[-limit:]

        if level:
            alerts = [a for a in alerts if a.level == level]

        if tags:
            alerts = [a for a in alerts if any(tag in a.tags for tag in tags)]

        return alerts

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        if not self.alert_history:
            return {
                'total_alerts': 0,
                'by_level': {},
                'recent_1h': 0,
                'recent_24h': 0
            }

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        by_level = {}
        recent_1h = 0
        recent_24h = 0

        for alert in self.alert_history:
            # Count by level
            level_str = alert.level.value
            by_level[level_str] = by_level.get(level_str, 0) + 1

            # Count recent
            if alert.timestamp >= one_hour_ago:
                recent_1h += 1
            if alert.timestamp >= one_day_ago:
                recent_24h += 1

        return {
            'total_alerts': len(self.alert_history),
            'by_level': by_level,
            'recent_1h': recent_1h,
            'recent_24h': recent_24h
        }

    def clear_history(self):
        """Clear alert history"""
        self.alert_history.clear()
        logger.info("✓ Alert history cleared")


class TradingAlerts:
    """
    Pre-configured alert templates for trading events
    """

    def __init__(self, alert_manager: AlertManager):
        self.manager = alert_manager

    async def risk_limit_breach(
        self,
        limit_type: str,
        current_value: float,
        limit_value: float,
        symbol: Optional[str] = None
    ):
        """Alert for risk limit breach"""
        await self.manager.send_alert(
            level=AlertLevel.CRITICAL,
            title=f"Risk Limit Breach: {limit_type}",
            message=f"{limit_type} exceeded! Current: {current_value:.2f}, Limit: {limit_value:.2f}",
            data={
                'limit_type': limit_type,
                'current_value': current_value,
                'limit_value': limit_value,
                'symbol': symbol
            },
            tags=['risk', 'breach', limit_type]
        )

    async def large_loss(
        self,
        symbol: str,
        loss_amount: float,
        loss_pct: float,
        position_size: float
    ):
        """Alert for large loss"""
        await self.manager.send_alert(
            level=AlertLevel.CRITICAL,
            title=f"Large Loss: {symbol}",
            message=f"Significant loss detected! {symbol}: ${loss_amount:.2f} ({loss_pct:.2f}%)",
            data={
                'symbol': symbol,
                'loss_amount': loss_amount,
                'loss_pct': loss_pct,
                'position_size': position_size
            },
            tags=['loss', 'pnl', symbol]
        )

    async def trade_execution_failure(
        self,
        symbol: str,
        action: str,
        reason: str,
        attempted_size: float
    ):
        """Alert for trade execution failure"""
        await self.manager.send_alert(
            level=AlertLevel.WARNING,
            title=f"Trade Execution Failed: {symbol}",
            message=f"Failed to {action} {symbol}: {reason}",
            data={
                'symbol': symbol,
                'action': action,
                'reason': reason,
                'attempted_size': attempted_size
            },
            tags=['execution', 'failure', symbol]
        )

    async def arbitrage_opportunity(
        self,
        pair: str,
        exchanges: List[str],
        profit_pct: float,
        volume: float
    ):
        """Alert for arbitrage opportunity"""
        await self.manager.send_alert(
            level=AlertLevel.INFO,
            title=f"Arbitrage Opportunity: {pair}",
            message=f"Found arbitrage: {pair} between {exchanges[0]} and {exchanges[1]}, profit: {profit_pct:.2f}%",
            data={
                'pair': pair,
                'exchanges': exchanges,
                'profit_pct': profit_pct,
                'volume': volume
            },
            tags=['arbitrage', 'opportunity', pair]
        )

    async def system_error(
        self,
        component: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """Alert for system errors"""
        await self.manager.send_alert(
            level=AlertLevel.CRITICAL,
            title=f"System Error: {component}",
            message=f"Error in {component}: {error_message}",
            data={
                'component': component,
                'error_message': error_message,
                'error_details': error_details or {}
            },
            tags=['system', 'error', component]
        )

    async def emergency_stop_triggered(
        self,
        reason: str,
        trigger_details: Dict[str, Any]
    ):
        """Alert for emergency stop"""
        await self.manager.send_alert(
            level=AlertLevel.EMERGENCY,
            title="EMERGENCY STOP TRIGGERED",
            message=f"Trading halted! Reason: {reason}",
            data={
                'reason': reason,
                'trigger_details': trigger_details
            },
            tags=['emergency', 'stop', 'halt']
        )

    async def performance_milestone(
        self,
        milestone_type: str,
        value: float,
        period: str
    ):
        """Alert for performance milestones"""
        await self.manager.send_alert(
            level=AlertLevel.INFO,
            title=f"Performance Milestone: {milestone_type}",
            message=f"Achieved {milestone_type}: {value:.2f} over {period}",
            data={
                'milestone_type': milestone_type,
                'value': value,
                'period': period
            },
            tags=['performance', 'milestone']
        )

    async def market_anomaly(
        self,
        symbol: str,
        anomaly_type: str,
        severity: float,
        description: str
    ):
        """Alert for market anomalies"""
        level = AlertLevel.CRITICAL if severity > 0.8 else AlertLevel.WARNING

        await self.manager.send_alert(
            level=level,
            title=f"Market Anomaly: {symbol}",
            message=f"{anomaly_type} detected in {symbol}: {description}",
            data={
                'symbol': symbol,
                'anomaly_type': anomaly_type,
                'severity': severity,
                'description': description
            },
            tags=['anomaly', 'market', symbol]
        )

    async def position_alert(
        self,
        symbol: str,
        alert_type: str,
        current_pnl: float,
        current_pnl_pct: float
    ):
        """Alert for position updates"""
        level = AlertLevel.WARNING if current_pnl < 0 else AlertLevel.INFO

        await self.manager.send_alert(
            level=level,
            title=f"Position Alert: {symbol}",
            message=f"{alert_type} - {symbol} PnL: ${current_pnl:.2f} ({current_pnl_pct:.2f}%)",
            data={
                'symbol': symbol,
                'alert_type': alert_type,
                'current_pnl': current_pnl,
                'current_pnl_pct': current_pnl_pct
            },
            tags=['position', 'pnl', symbol]
        )


# Global alert manager instance
_global_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager"""
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
    return _global_alert_manager


def set_alert_manager(manager: AlertManager):
    """Set global alert manager"""
    global _global_alert_manager
    _global_alert_manager = manager
