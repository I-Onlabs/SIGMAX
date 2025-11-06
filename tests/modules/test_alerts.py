"""
Unit tests for Alert Management System
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from core.modules.alerts import (
    AlertManager,
    TradingAlerts,
    Alert,
    AlertLevel,
    AlertChannel
)


class TestAlertManager:
    """Tests for AlertManager"""

    @pytest.fixture
    def alert_manager(self):
        """Create AlertManager instance"""
        return AlertManager(
            enabled_channels=[AlertChannel.CONSOLE],
            throttle_seconds=5
        )

    def test_initialization(self, alert_manager):
        """Test alert manager initialization"""
        assert alert_manager is not None
        assert AlertChannel.CONSOLE in alert_manager.enabled_channels
        assert alert_manager.throttle_seconds == 5
        assert len(alert_manager.alert_history) == 0

    @pytest.mark.asyncio
    async def test_send_alert(self, alert_manager):
        """Test sending an alert"""
        await alert_manager.send_alert(
            level=AlertLevel.INFO,
            title="Test Alert",
            message="This is a test alert",
            tags=['test']
        )

        assert len(alert_manager.alert_history) == 1
        alert = alert_manager.alert_history[0]
        assert alert.level == AlertLevel.INFO
        assert alert.title == "Test Alert"
        assert 'test' in alert.tags

    @pytest.mark.asyncio
    async def test_alert_throttling(self, alert_manager):
        """Test alert throttling"""
        # Send same alert twice quickly
        await alert_manager.send_alert(
            level=AlertLevel.INFO,
            title="Test Alert",
            message="Same message"
        )

        await alert_manager.send_alert(
            level=AlertLevel.INFO,
            title="Test Alert",
            message="Same message"
        )

        # Only one should be in history due to throttling
        assert len(alert_manager.alert_history) == 1

    @pytest.mark.asyncio
    async def test_alert_different_messages_not_throttled(self, alert_manager):
        """Test that different alerts are not throttled"""
        await alert_manager.send_alert(
            level=AlertLevel.INFO,
            title="Alert 1",
            message="Message 1"
        )

        await alert_manager.send_alert(
            level=AlertLevel.INFO,
            title="Alert 2",
            message="Message 2"
        )

        # Both should be in history
        assert len(alert_manager.alert_history) == 2

    @pytest.mark.asyncio
    async def test_alert_levels(self, alert_manager):
        """Test different alert levels"""
        levels = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.CRITICAL, AlertLevel.EMERGENCY]

        for level in levels:
            await alert_manager.send_alert(
                level=level,
                title=f"{level.value} Alert",
                message=f"This is a {level.value} alert"
            )

        assert len(alert_manager.alert_history) == 4

        # Check all levels are represented
        history_levels = [a.level for a in alert_manager.alert_history]
        for level in levels:
            assert level in history_levels

    def test_get_recent_alerts(self, alert_manager):
        """Test getting recent alerts"""
        # Add some alerts to history
        for i in range(10):
            alert_manager.alert_history.append(Alert(
                level=AlertLevel.INFO,
                title=f"Alert {i}",
                message=f"Message {i}",
                tags=['test']
            ))

        recent = alert_manager.get_recent_alerts(limit=5)
        assert len(recent) == 5

    def test_get_recent_alerts_filter_by_level(self, alert_manager):
        """Test filtering alerts by level"""
        # Add alerts with different levels
        alert_manager.alert_history.append(Alert(
            level=AlertLevel.INFO,
            title="Info Alert",
            message="Info"
        ))
        alert_manager.alert_history.append(Alert(
            level=AlertLevel.CRITICAL,
            title="Critical Alert",
            message="Critical"
        ))

        # Filter by level
        critical_alerts = alert_manager.get_recent_alerts(level=AlertLevel.CRITICAL)
        assert len(critical_alerts) == 1
        assert critical_alerts[0].level == AlertLevel.CRITICAL

    def test_get_recent_alerts_filter_by_tags(self, alert_manager):
        """Test filtering alerts by tags"""
        alert_manager.alert_history.append(Alert(
            level=AlertLevel.INFO,
            title="Alert 1",
            message="Message",
            tags=['trading', 'btc']
        ))
        alert_manager.alert_history.append(Alert(
            level=AlertLevel.INFO,
            title="Alert 2",
            message="Message",
            tags=['system', 'error']
        ))

        # Filter by tags
        trading_alerts = alert_manager.get_recent_alerts(tags=['trading'])
        assert len(trading_alerts) == 1
        assert 'trading' in trading_alerts[0].tags

    def test_get_alert_stats(self, alert_manager):
        """Test alert statistics"""
        # Add alerts
        alert_manager.alert_history.append(Alert(
            level=AlertLevel.INFO,
            title="Info",
            message="Info",
            timestamp=datetime.now()
        ))
        alert_manager.alert_history.append(Alert(
            level=AlertLevel.CRITICAL,
            title="Critical",
            message="Critical",
            timestamp=datetime.now() - timedelta(hours=2)
        ))

        stats = alert_manager.get_alert_stats()

        assert stats['total_alerts'] == 2
        assert 'by_level' in stats
        assert stats['by_level']['info'] == 1
        assert stats['by_level']['critical'] == 1
        assert 'recent_1h' in stats
        assert 'recent_24h' in stats

    def test_clear_history(self, alert_manager):
        """Test clearing alert history"""
        # Add alerts
        for i in range(5):
            alert_manager.alert_history.append(Alert(
                level=AlertLevel.INFO,
                title=f"Alert {i}",
                message=f"Message {i}"
            ))

        alert_manager.clear_history()
        assert len(alert_manager.alert_history) == 0

    def test_max_history_limit(self):
        """Test max history limit"""
        alert_manager = AlertManager(enabled_channels=[AlertChannel.CONSOLE])
        alert_manager.max_history = 5

        # Add more than max
        for i in range(10):
            alert_manager.alert_history.append(Alert(
                level=AlertLevel.INFO,
                title=f"Alert {i}",
                message=f"Message {i}"
            ))

        # Should only keep last 5
        assert len(alert_manager.alert_history) <= 5

    def test_add_custom_handler(self, alert_manager):
        """Test adding custom alert handler"""
        custom_handler = AsyncMock()
        alert_manager.add_custom_handler(AlertChannel.EMAIL, custom_handler)

        assert AlertChannel.EMAIL in alert_manager.custom_handlers

    def test_add_alert_rule(self, alert_manager):
        """Test adding custom alert rule"""
        alert_manager.add_alert_rule(
            condition="price > 100000",
            level=AlertLevel.INFO,
            title="Price Alert",
            message_template="Price is {price}",
            channels=[AlertChannel.CONSOLE]
        )

        assert len(alert_manager.alert_rules) == 1

    def test_alert_to_dict(self):
        """Test converting alert to dictionary"""
        alert = Alert(
            level=AlertLevel.INFO,
            title="Test",
            message="Test message",
            tags=['test']
        )

        alert_dict = alert.to_dict()

        assert alert_dict['level'] == 'info'
        assert alert_dict['title'] == "Test"
        assert alert_dict['message'] == "Test message"
        assert 'timestamp' in alert_dict
        assert alert_dict['tags'] == ['test']


class TestTradingAlerts:
    """Tests for TradingAlerts"""

    @pytest.fixture
    def alert_manager(self):
        """Create AlertManager instance"""
        return AlertManager(enabled_channels=[AlertChannel.CONSOLE])

    @pytest.fixture
    def trading_alerts(self, alert_manager):
        """Create TradingAlerts instance"""
        return TradingAlerts(alert_manager)

    @pytest.mark.asyncio
    async def test_risk_limit_breach(self, trading_alerts):
        """Test risk limit breach alert"""
        await trading_alerts.risk_limit_breach(
            limit_type='daily_loss',
            current_value=15.0,
            limit_value=10.0,
            symbol='BTC/USDT'
        )

        assert len(trading_alerts.manager.alert_history) == 1
        alert = trading_alerts.manager.alert_history[0]
        assert alert.level == AlertLevel.CRITICAL
        assert 'risk' in alert.tags

    @pytest.mark.asyncio
    async def test_large_loss(self, trading_alerts):
        """Test large loss alert"""
        await trading_alerts.large_loss(
            symbol='BTC/USDT',
            loss_amount=500.0,
            loss_pct=10.0,
            position_size=5000.0
        )

        assert len(trading_alerts.manager.alert_history) == 1
        alert = trading_alerts.manager.alert_history[0]
        assert alert.level == AlertLevel.CRITICAL
        assert 'loss' in alert.tags

    @pytest.mark.asyncio
    async def test_trade_execution_failure(self, trading_alerts):
        """Test trade execution failure alert"""
        await trading_alerts.trade_execution_failure(
            symbol='BTC/USDT',
            action='buy',
            reason='Insufficient funds',
            attempted_size=0.1
        )

        assert len(trading_alerts.manager.alert_history) == 1
        alert = trading_alerts.manager.alert_history[0]
        assert alert.level == AlertLevel.WARNING
        assert 'execution' in alert.tags

    @pytest.mark.asyncio
    async def test_arbitrage_opportunity(self, trading_alerts):
        """Test arbitrage opportunity alert"""
        await trading_alerts.arbitrage_opportunity(
            pair='BTC/USDT',
            exchanges=['binance', 'kraken'],
            profit_pct=1.5,
            volume=10000.0
        )

        assert len(trading_alerts.manager.alert_history) == 1
        alert = trading_alerts.manager.alert_history[0]
        assert alert.level == AlertLevel.INFO
        assert 'arbitrage' in alert.tags

    @pytest.mark.asyncio
    async def test_system_error(self, trading_alerts):
        """Test system error alert"""
        await trading_alerts.system_error(
            component='orchestrator',
            error_message='Connection timeout',
            error_details={'timeout': 30}
        )

        assert len(trading_alerts.manager.alert_history) == 1
        alert = trading_alerts.manager.alert_history[0]
        assert alert.level == AlertLevel.CRITICAL
        assert 'system' in alert.tags

    @pytest.mark.asyncio
    async def test_emergency_stop_triggered(self, trading_alerts):
        """Test emergency stop alert"""
        await trading_alerts.emergency_stop_triggered(
            reason='Daily loss limit exceeded',
            trigger_details={'loss': 15.0, 'limit': 10.0}
        )

        assert len(trading_alerts.manager.alert_history) == 1
        alert = trading_alerts.manager.alert_history[0]
        assert alert.level == AlertLevel.EMERGENCY
        assert 'emergency' in alert.tags

    @pytest.mark.asyncio
    async def test_performance_milestone(self, trading_alerts):
        """Test performance milestone alert"""
        await trading_alerts.performance_milestone(
            milestone_type='total_pnl',
            value=1000.0,
            period='month'
        )

        assert len(trading_alerts.manager.alert_history) == 1
        alert = trading_alerts.manager.alert_history[0]
        assert alert.level == AlertLevel.INFO
        assert 'performance' in alert.tags

    @pytest.mark.asyncio
    async def test_market_anomaly(self, trading_alerts):
        """Test market anomaly alert"""
        await trading_alerts.market_anomaly(
            symbol='BTC/USDT',
            anomaly_type='flash_crash',
            severity=0.9,
            description='Rapid price drop detected'
        )

        assert len(trading_alerts.manager.alert_history) == 1
        alert = trading_alerts.manager.alert_history[0]
        # High severity should trigger critical alert
        assert alert.level in [AlertLevel.CRITICAL, AlertLevel.WARNING]
        assert 'anomaly' in alert.tags

    @pytest.mark.asyncio
    async def test_position_alert(self, trading_alerts):
        """Test position update alert"""
        await trading_alerts.position_alert(
            symbol='BTC/USDT',
            alert_type='target_reached',
            current_pnl=100.0,
            current_pnl_pct=10.0
        )

        assert len(trading_alerts.manager.alert_history) == 1
        alert = trading_alerts.manager.alert_history[0]
        assert 'position' in alert.tags

    @pytest.mark.asyncio
    async def test_multiple_alerts_different_types(self, trading_alerts):
        """Test sending multiple alerts of different types"""
        await trading_alerts.risk_limit_breach('exposure', 100, 80)
        await trading_alerts.large_loss('BTC/USDT', 50, 5, 1000)
        await trading_alerts.system_error('api', 'timeout')

        # All alerts should be in history
        assert len(trading_alerts.manager.alert_history) == 3

        # Different alert types
        tags = [tag for alert in trading_alerts.manager.alert_history for tag in alert.tags]
        assert 'risk' in tags
        assert 'loss' in tags
        assert 'system' in tags
