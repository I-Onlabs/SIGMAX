"""
Execution Engine

Executes orders on exchanges via CCXT.
"""

import ccxt.async_support as ccxtasync
from typing import Dict, Optional

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import OrderIntent, OrderAck, Fill, Reject, OrderStatus, RejectReason, get_trading_metrics


class ExecutionEngine:
    """
    Execution engine for CEX orders.
    
    Uses CCXT to execute orders on exchanges.
    """
    
    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("exec_cex")
        self.trading_metrics = get_trading_metrics()
        
        # Exchange instances
        self.exchanges: Dict[str, ccxtasync.Exchange] = {}
        
        # Symbol mapping (symbol_id -> pair)
        self.symbol_map = {
            1: "BTC/USDT",
            2: "ETH/USDT",
            3: "SOL/USDT",
            4: "BNB/USDT",
            5: "XRP/USDT",
        }
        
        self.running = False
        
    async def start(self):
        """Start the execution engine"""
        # Initialize exchange connections
        for exchange_name, ex_config in self.config.exchanges.items():
            try:
                exchange_class = getattr(ccxtasync, exchange_name)
                exchange = exchange_class({
                    'apiKey': ex_config.api_key,
                    'secret': ex_config.api_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',
                    }
                })
                
                if ex_config.testnet:
                    exchange.set_sandbox_mode(True)
                
                self.exchanges[exchange_name] = exchange
                
                self.logger.info("exchange_connected",
                               exchange=exchange_name,
                               testnet=ex_config.testnet)
            except Exception as e:
                self.logger.error("exchange_init_error",
                                exchange=exchange_name,
                                error=str(e))
        
        self.running = True
        self.logger.info("execution_engine_started", num_exchanges=len(self.exchanges))
        
    async def stop(self):
        """Stop the execution engine"""
        self.running = False
        
        # Close all exchange connections
        for exchange in self.exchanges.values():
            await exchange.close()
        
        self.logger.info("execution_engine_stopped")
    
    async def execute_order(self, order: OrderIntent):
        """
        Execute order on exchange.
        
        Args:
            order: OrderIntent to execute
        """
        try:
            start_ts = get_timestamp_ns()
            
            # Get exchange
            exchange = self.exchanges.get(order.route)
            if not exchange:
                self.logger.error("exchange_not_found",
                                client_id=order.client_id,
                                route=order.route)
                
                reject = Reject(
                    ts_ns=get_timestamp_ns(),
                    client_id=order.client_id,
                    reason_code=RejectReason.NO_ROUTE,
                    reason_msg=f"Exchange {order.route} not available",
                    source="execution"
                )
                await self.publisher.publish_rejection(reject)
                return
            
            # Get symbol
            symbol = self.symbol_map.get(order.symbol_id)
            if not symbol:
                self.logger.error("symbol_not_found",
                                client_id=order.client_id,
                                symbol_id=order.symbol_id)
                return
            
            # Record submission
            self.trading_metrics.record_order_submitted(
                symbol=symbol,
                side=order.side.name,
                order_type=order.order_type.name
            )
            
            # Execute order (paper trading mode - no actual execution)
            # In production, would call:
            # result = await exchange.create_order(...)
            
            # For now, simulate success
            exchange_order_id = f"SIM-{order.client_id}"
            
            # Publish acknowledgment
            ack = OrderAck(
                ts_ns=get_timestamp_ns(),
                client_id=order.client_id,
                exchange_order_id=exchange_order_id,
                status=OrderStatus.SUBMITTED,
                venue_code=1,  # Binance
                submit_ts_ns=order.ts_ns
            )
            await self.publisher.publish_ack(ack)
            
            # Simulate fill (in production, would come from exchange feed)
            fill = Fill(
                ts_ns=get_timestamp_ns(),
                client_id=order.client_id,
                exchange_order_id=exchange_order_id,
                price=order.price or 0.0,
                qty=order.qty,
                fee=order.qty * (order.price or 0.0) * 0.001,  # 0.1% fee
                fee_currency="USDT",
                venue_code=1,
                is_maker=True,
                trade_id=f"TRADE-{order.client_id}"
            )
            await self.publisher.publish_fill(fill)
            
            # Record fill
            self.trading_metrics.record_order_filled(
                symbol=symbol,
                side=order.side.name,
                size_usd=order.qty * (order.price or 0.0)
            )
            
            self.logger.info("order_executed",
                           client_id=order.client_id,
                           symbol=symbol,
                           side=order.side.name,
                           qty=order.qty,
                           price=order.price,
                           exchange_order_id=exchange_order_id)
            
            # Record latency
            end_ts = get_timestamp_ns()
            exec_latency_us = calculate_latency_us(start_ts, end_ts)
            total_latency_us = calculate_latency_us(order.ts_ns, end_ts)
            
            self.metrics.record_latency("execute", exec_latency_us)
            self.metrics.record_latency("order_to_fill", total_latency_us)
            
        except Exception as e:
            self.logger.error("execute_order_error",
                            client_id=order.client_id,
                            error=str(e),
                            exc_info=True)
            self.metrics.record_error("execute_failed")
            
            # Publish rejection
            reject = Reject(
                ts_ns=get_timestamp_ns(),
                client_id=order.client_id,
                reason_code=RejectReason.INTERNAL_ERROR,
                reason_msg=str(e),
                source="execution"
            )
            await self.publisher.publish_rejection(reject)
