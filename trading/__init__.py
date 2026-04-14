"""交易执行模块"""

import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Order:
    order_id: str
    symbol: str
    action: str
    order_type: str
    price: float
    shares: int
    status: str
    filled_shares: int = 0
    filled_price: float = 0.0
    create_time: datetime = None
    update_time: datetime = None


class TradeExecutor:
    def __init__(self, mode: str = "simulation"):
        self.mode = mode
        self.pending_orders: List[Order] = []
        self.filled_orders: List[Order] = []
        self.order_id = 0
        self.mode_configured = False

    def _next_order_id(self) -> str:
        self.order_id += 1
        return f"{self.mode.upper()}_{datetime.now().strftime('%Y%m%d')}_{self.order_id:06d}"

    def configure(self, broker_config: Dict = None):
        if self.mode == "simulation":
            self.mode_configured = True
            logger.info("模拟交易模式已配置")
        elif self.mode == "qmt":
            logger.info("QMT模式配置中...")
        elif self.mode == "ptrade":
            logger.info("PTrade模式配置中...")

    def buy(
        self, symbol: str, price: float, shares: int, order_type: str = "limit"
    ) -> Order:
        order = Order(
            order_id=self._next_order_id(),
            symbol=symbol,
            action="BUY",
            order_type=order_type,
            price=price,
            shares=shares,
            status="PENDING",
            create_time=datetime.now(),
        )
        self.pending_orders.append(order)
        if self.mode == "simulation":
            order.status = "FILLED"
            order.filled_shares = shares
            order.filled_price = price
            order.update_time = datetime.now()
            self.filled_orders.append(order)
            logger.info(f"[模拟买入] {symbol} {shares}股 @ {price}")
        return order

    def sell(
        self, symbol: str, price: float, shares: int, order_type: str = "limit"
    ) -> Order:
        order = Order(
            order_id=self._next_order_id(),
            symbol=symbol,
            action="SELL",
            order_type=order_type,
            price=price,
            shares=shares,
            status="PENDING",
            create_time=datetime.now(),
        )
        self.pending_orders.append(order)
        if self.mode == "simulation":
            order.status = "FILLED"
            order.filled_shares = shares
            order.filled_price = price
            order.update_time = datetime.now()
            self.filled_orders.append(order)
            logger.info(f"[模拟卖出] {symbol} {shares}股 @ {price}")
        return order

    def cancel_order(self, order_id: str) -> bool:
        for order in self.pending_orders:
            if order.order_id == order_id:
                order.status = "CANCELLED"
                self.pending_orders.remove(order)
                logger.info(f"订单已取消: {order_id}")
                return True
        return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        for order in self.pending_orders + self.filled_orders:
            if order.order_id == order_id:
                return order
        return None

    def get_pending_orders(self) -> List[Order]:
        return self.pending_orders.copy()

    def get_filled_orders(self) -> List[Order]:
        return self.filled_orders.copy()

    def sync_positions(self) -> Dict[str, Dict]:
        positions = {}
        for order in self.filled_orders:
            if order.symbol not in positions:
                positions[order.symbol] = {"shares": 0, "avg_cost": 0}
            if order.action == "BUY":
                pos = positions[order.symbol]
                total_cost = (
                    pos["shares"] * pos["avg_cost"]
                    + order.filled_shares * order.filled_price
                )
                pos["shares"] += order.filled_shares
                pos["avg_cost"] = total_cost / pos["shares"] if pos["shares"] > 0 else 0
            elif order.action == "SELL":
                positions[order.symbol]["shares"] -= order.filled_shares
                if positions[order.symbol]["shares"] <= 0:
                    del positions[order.symbol]
        return positions


class BrokerAdapter:
    def __init__(self, broker_type: str = "simulation"):
        self.broker_type = broker_type
        self.executor = TradeExecutor(mode=broker_type)

    def get_account_info(self) -> Dict:
        if self.broker_type == "simulation":
            return {
                "cash": 1000000,
                "total_assets": 1000000,
                "available_cash": 1000000,
                "market_value": 0,
            }
        return {}

    def get_positions(self) -> Dict[str, Dict]:
        return self.executor.sync_positions()

    def place_order(self, symbol: str, action: str, price: float, shares: int) -> Order:
        if action.upper() == "BUY":
            return self.executor.buy(symbol, price, shares)
        else:
            return self.executor.sell(symbol, price, shares)
