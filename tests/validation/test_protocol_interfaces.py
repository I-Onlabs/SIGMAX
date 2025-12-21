"""
Unit tests demonstrating the use of protocol interfaces for testing.
Tests modules with mocked dependencies using the Protocol pattern.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.modules.protocols import (
    DataModuleProtocol,
    ExecutionModuleProtocol,
    ComplianceModuleProtocol
)


class MockDataModule:
    """Mock DataModule implementing DataModuleProtocol"""

    def __init__(self):
        self.initialized = False
        self.call_count = 0

    async def initialize(self):
        """Initialize the mock data module"""
        self.initialized = True

    async def get_market_data(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> Dict:
        """Return mock market data"""
        self.call_count += 1
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "price": 45000.0 + (self.call_count * 100),
            "volume": 1000000,
            "timestamp": datetime.now().isoformat()
        }

    async def get_historical_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str = "1h"
    ) -> List[List[float]]:
        """Return mock historical data"""
        return [[45000, 45100, 44900, 45050, 1000] for _ in range(100)]

    async def close(self):
        """Close the mock data module"""
        self.initialized = False


class MockExecutionModule:
    """Mock ExecutionModule implementing ExecutionModuleProtocol"""

    def __init__(self):
        self.initialized = False
        self.trades = []
        self.positions_closed = False

    async def initialize(self):
        """Initialize the mock execution module"""
        self.initialized = True

    async def execute_trade(
        self,
        symbol: str,
        action: str,
        size: float,
        price: float = None
    ) -> Dict:
        """Execute a mock trade"""
        trade = {
            "symbol": symbol,
            "action": action,
            "size": size,
            "price": price or 45000.0,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        self.trades.append(trade)
        return trade

    async def close_all_positions(self) -> Dict:
        """Close all positions (emergency stop)"""
        self.positions_closed = True
        return {
            "success": True,
            "closed_count": len(self.trades),
            "positions": self.trades.copy()
        }

    async def get_status(self) -> Dict:
        """Get execution module status"""
        return {
            "initialized": self.initialized,
            "trade_count": len(self.trades),
            "positions_closed": self.positions_closed
        }


class MockComplianceModule:
    """Mock ComplianceModule implementing ComplianceModuleProtocol"""

    def __init__(self, allow_trades: bool = True):
        self.initialized = False
        self.allow_trades = allow_trades
        self.checks_performed = 0

    async def initialize(self):
        """Initialize the mock compliance module"""
        self.initialized = True

    async def check_trade(self, trade: Dict) -> Dict:
        """Check if a trade is compliant"""
        self.checks_performed += 1
        return {
            "approved": self.allow_trades,
            "reason": "Trade approved" if self.allow_trades else "Trade rejected",
            "trade": trade
        }


class TestProtocolInterfaces:
    """Test protocol-based dependency injection"""

    @pytest.mark.asyncio
    async def test_data_module_protocol(self):
        """Test DataModule protocol implementation"""
        data_module = MockDataModule()

        assert not data_module.initialized
        await data_module.initialize()
        assert data_module.initialized

        # Test get_market_data
        market_data = await data_module.get_market_data("BTC/USDT", "1h", 100)
        assert market_data["symbol"] == "BTC/USDT"
        assert market_data["timeframe"] == "1h"
        assert "price" in market_data
        assert "volume" in market_data

        # Test get_historical_data
        historical = await data_module.get_historical_data(
            "BTC/USDT",
            datetime(2024, 1, 1),
            datetime(2024, 12, 31)
        )
        assert len(historical) == 100
        assert len(historical[0]) == 5  # OHLCV

        await data_module.close()
        assert not data_module.initialized

        print("\n=== DataModule Protocol Test ===")
        print("✓ Protocol methods work correctly")
        print(f"✓ Mock data returned: {market_data}")

    @pytest.mark.asyncio
    async def test_execution_module_protocol(self):
        """Test ExecutionModule protocol implementation"""
        execution_module = MockExecutionModule()

        await execution_module.initialize()
        assert execution_module.initialized

        # Test execute_trade
        trade1 = await execution_module.execute_trade("BTC/USDT", "buy", 0.1, 45000)
        assert trade1["status"] == "success"
        assert trade1["action"] == "buy"
        assert len(execution_module.trades) == 1

        trade2 = await execution_module.execute_trade("ETH/USDT", "sell", 0.5, 3000)
        assert len(execution_module.trades) == 2

        # Test get_status
        status = await execution_module.get_status()
        assert status["initialized"] == True
        assert status["trade_count"] == 2

        # Test close_all_positions (emergency stop)
        result = await execution_module.close_all_positions()
        assert result["success"] == True
        assert result["closed_count"] == 2
        assert execution_module.positions_closed == True

        print("\n=== ExecutionModule Protocol Test ===")
        print(f"✓ Executed {len(execution_module.trades)} trades")
        print(f"✓ Emergency stop closed {result['closed_count']} positions")

    @pytest.mark.asyncio
    async def test_compliance_module_protocol(self):
        """Test ComplianceModule protocol implementation"""

        # Test with allowed trades
        compliance_allow = MockComplianceModule(allow_trades=True)
        await compliance_allow.initialize()

        trade = {"symbol": "BTC/USDT", "action": "buy", "size": 0.1}
        result = await compliance_allow.check_trade(trade)
        assert result["approved"] == True
        assert compliance_allow.checks_performed == 1

        # Test with rejected trades
        compliance_reject = MockComplianceModule(allow_trades=False)
        await compliance_reject.initialize()

        result = await compliance_reject.check_trade(trade)
        assert result["approved"] == False
        assert "rejected" in result["reason"].lower()

        print("\n=== ComplianceModule Protocol Test ===")
        print(f"✓ Trade approval works: {result}")
        print(f"✓ Checks performed: {compliance_allow.checks_performed}")

    @pytest.mark.asyncio
    async def test_dependency_injection_pattern(self):
        """Test using mock modules in a system context"""

        # Create mock dependencies
        data_module = MockDataModule()
        execution_module = MockExecutionModule()
        compliance_module = MockComplianceModule(allow_trades=True)

        # Initialize all modules
        await asyncio.gather(
            data_module.initialize(),
            execution_module.initialize(),
            compliance_module.initialize()
        )

        # Simulate a trading workflow
        market_data = await data_module.get_market_data("BTC/USDT")
        price = market_data["price"]

        # Check compliance before trading
        trade = {"symbol": "BTC/USDT", "action": "buy", "size": 0.1, "price": price}
        compliance_result = await compliance_module.check_trade(trade)

        if compliance_result["approved"]:
            # Execute trade
            execution_result = await execution_module.execute_trade(
                trade["symbol"],
                trade["action"],
                trade["size"],
                trade["price"]
            )
            assert execution_result["status"] == "success"

        # Verify the workflow
        status = await execution_module.get_status()
        assert status["trade_count"] == 1

        print("\n=== Dependency Injection Pattern Test ===")
        print(f"✓ Market data retrieved: ${price:,.2f}")
        print("✓ Compliance check passed")
        print("✓ Trade executed successfully")
        print(f"✓ Total trades: {status['trade_count']}")

    @pytest.mark.asyncio
    async def test_emergency_stop_workflow(self):
        """Test emergency stop workflow using protocol interfaces"""

        # Setup modules
        data_module = MockDataModule()
        execution_module = MockExecutionModule()

        await asyncio.gather(
            data_module.initialize(),
            execution_module.initialize()
        )

        # Execute multiple trades
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        for symbol in symbols:
            await execution_module.execute_trade(symbol, "buy", 0.1, 45000)

        # Verify trades were executed
        status_before = await execution_module.get_status()
        assert status_before["trade_count"] == 3

        # Trigger emergency stop
        close_result = await execution_module.close_all_positions()

        assert close_result["success"] == True
        assert close_result["closed_count"] == 3
        assert execution_module.positions_closed == True

        print("\n=== Emergency Stop Workflow Test ===")
        print(f"✓ Executed {status_before['trade_count']} trades")
        print("✓ Emergency stop triggered")
        print(f"✓ Closed {close_result['closed_count']} positions")
        print("✓ All positions closed successfully")

    @pytest.mark.asyncio
    async def test_protocol_type_checking(self):
        """Test that mock implementations satisfy protocol requirements"""

        # These should not raise type errors if protocols are satisfied
        data_module: DataModuleProtocol = MockDataModule()
        execution_module: ExecutionModuleProtocol = MockExecutionModule()
        compliance_module: ComplianceModuleProtocol = MockComplianceModule()

        # Verify all required methods exist
        assert hasattr(data_module, 'initialize')
        assert hasattr(data_module, 'get_market_data')
        assert hasattr(data_module, 'get_historical_data')
        assert hasattr(data_module, 'close')

        assert hasattr(execution_module, 'initialize')
        assert hasattr(execution_module, 'execute_trade')
        assert hasattr(execution_module, 'close_all_positions')
        assert hasattr(execution_module, 'get_status')

        assert hasattr(compliance_module, 'initialize')
        assert hasattr(compliance_module, 'check_trade')

        print("\n=== Protocol Type Checking Test ===")
        print("✓ DataModule satisfies DataModuleProtocol")
        print("✓ ExecutionModule satisfies ExecutionModuleProtocol")
        print("✓ ComplianceModule satisfies ComplianceModuleProtocol")

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent operations using protocol interfaces"""

        data_module = MockDataModule()
        await data_module.initialize()

        # Fetch market data for multiple symbols concurrently
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "DOT/USDT"]

        tasks = [
            data_module.get_market_data(symbol)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == len(symbols)
        for i, result in enumerate(results):
            assert result["symbol"] == symbols[i]
            assert "price" in result

        print("\n=== Concurrent Operations Test ===")
        print(f"✓ Fetched data for {len(symbols)} symbols concurrently")
        print("✓ All operations completed successfully")
        print(f"✓ Data module call count: {data_module.call_count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
