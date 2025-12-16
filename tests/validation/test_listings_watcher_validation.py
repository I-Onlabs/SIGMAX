import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import time

from apps.signals.listings_watcher.main import ListingsWatcher
from pkg.schemas import SignalEvent, SignalType
from pkg.schemas.signals import ListingMetaCode

@pytest.mark.asyncio
async def test_listings_watcher_detects_new_listing():
    """
    Test that the ListingsWatcher detects a new listing and publishes a signal.
    """
    # Mock configuration
    mock_config = MagicMock()
    mock_config.observability.log_level = "INFO"
    mock_config.observability.log_path = None
    mock_config.is_production.return_value = False
    mock_config.ipc.transport = "zmq"
    mock_config.ipc.zmq_base_port = 5555

    # Mock SignalPublisher
    with patch("apps.signals.listings_watcher.main.SignalPublisher") as MockPublisher:
        mock_publisher_instance = MockPublisher.return_value
        mock_publisher_instance.start = AsyncMock()
        mock_publisher_instance.stop = AsyncMock()
        mock_publisher_instance.publish = AsyncMock()

        # Instantiate Watcher
        watcher = ListingsWatcher(mock_config)

        # Override _get_symbol_id to avoid DB lookup/cache logic complexity for this test
        watcher._get_symbol_id = AsyncMock(return_value=12345)

        # Mock ccxt exchanges
        with patch("ccxt.async_support.binance") as MockBinance, \
             patch("ccxt.async_support.coinbase") as MockCoinbase, \
             patch("ccxt.async_support.kraken") as MockKraken, \
             patch("ccxt.async_support.kucoin") as MockKucoin:

            mock_binance = AsyncMock()
            mock_coinbase = AsyncMock()
            mock_kraken = AsyncMock()
            mock_kucoin = AsyncMock()

            MockBinance.return_value = mock_binance
            MockCoinbase.return_value = mock_coinbase
            MockKraken.return_value = mock_kraken
            MockKucoin.return_value = mock_kucoin

            # Setup initial state (first call to fetch_markets)
            mock_binance.fetch_markets.side_effect = [
                [{'symbol': 'BTC/USDT', 'active': True}], # Init
                [{'symbol': 'BTC/USDT', 'active': True}, {'symbol': 'LTC/USDT', 'active': True}], # Poll 1 (New Listing)
                asyncio.CancelledError()
            ]

            mock_coinbase.fetch_markets.side_effect = [
                [{'symbol': 'ETH/USDT', 'active': True}],
                [{'symbol': 'ETH/USDT', 'active': True}],
                asyncio.CancelledError()
            ]

            mock_kraken.fetch_markets.side_effect = [
                [{'symbol': 'XRP/USDT', 'active': True}],
                [{'symbol': 'XRP/USDT', 'active': True}],
                asyncio.CancelledError()
            ]

            mock_kucoin.fetch_markets.side_effect = [
                [{'symbol': 'SOL/USDT', 'active': True}],
                [{'symbol': 'SOL/USDT', 'active': True}],
                asyncio.CancelledError()
            ]

            # Start the watcher
            with patch("asyncio.sleep", AsyncMock()):
                task = asyncio.create_task(watcher.start())

                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except asyncio.TimeoutError:
                    await watcher.stop()
                except Exception:
                    pass

        # Verify publish was called for LTC/USDT
        assert mock_publisher_instance.publish.called
        call_args = mock_publisher_instance.publish.call_args
        assert call_args is not None

        signal_event = call_args[0][0]
        assert isinstance(signal_event, SignalEvent)
        assert signal_event.symbol_id == 12345
        assert signal_event.sig_type == SignalType.LISTING
        assert signal_event.meta_code == ListingMetaCode.NEW_LISTING
        assert signal_event.metadata['symbol'] == 'LTC/USDT'
        assert signal_event.metadata['exchange'] == 'binance'

@pytest.mark.asyncio
async def test_listings_watcher_initialization_no_alert():
    """
    Test that the ListingsWatcher does NOT alert on symbols present during initialization.
    """
    mock_config = MagicMock()
    mock_config.observability.log_level = "INFO"
    mock_config.observability.log_path = None
    mock_config.is_production.return_value = False
    mock_config.ipc.transport = "zmq"
    mock_config.ipc.zmq_base_port = 5555

    with patch("apps.signals.listings_watcher.main.SignalPublisher") as MockPublisher:
        mock_publisher_instance = MockPublisher.return_value
        mock_publisher_instance.start = AsyncMock()
        mock_publisher_instance.stop = AsyncMock()
        mock_publisher_instance.publish = AsyncMock()

        watcher = ListingsWatcher(mock_config)

        with patch("ccxt.async_support.binance") as MockBinance, \
             patch("ccxt.async_support.coinbase") as MockCoinbase, \
             patch("ccxt.async_support.kraken") as MockKraken, \
             patch("ccxt.async_support.kucoin") as MockKucoin:

            # Setup mocks to return empty lists or static lists
            for MockClass in [MockBinance, MockCoinbase, MockKraken, MockKucoin]:
                mock_instance = MockClass.return_value
                mock_instance.fetch_markets.side_effect = [
                    [{'symbol': 'BTC/USDT', 'active': True}],
                    [{'symbol': 'BTC/USDT', 'active': True}],
                    asyncio.CancelledError()
                ]

            with patch("asyncio.sleep", AsyncMock()):
                task = asyncio.create_task(watcher.start())
                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except:
                    pass

        # Should NOT publish any signal
        mock_publisher_instance.publish.assert_not_called()
