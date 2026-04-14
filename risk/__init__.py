"""风险管理模块"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from strategies import Signal


@dataclass
class RiskLimit:
    name: str
    value: float
    enabled: bool = True


class RiskManager:
    def __init__(
        self,
        max_position_pct: float = 0.3,
        max_total_position: float = 0.8,
        max_drawdown: float = 0.15,
        stop_loss: float = 0.07,
        take_profit: float = 0.20,
    ):
        self.max_position_pct = max_position_pct
        self.max_total_position = max_total_position
        self.max_drawdown = max_drawdown
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.limits = [
            RiskLimit("max_position_pct", max_position_pct),
            RiskLimit("max_total_position", max_total_position),
            RiskLimit("max_drawdown", max_drawdown),
            RiskLimit("stop_loss", stop_loss),
            RiskLimit("take_profit", take_profit),
        ]
        self.current_positions: Dict[str, float] = {}
        self.entry_prices: Dict[str, float] = {}
        self.max_value = 0
        self.current_value = 0

    def update_position(self, symbol: str, shares: int, price: float):
        if shares > 0:
            self.current_positions[symbol] = shares * price
            if symbol not in self.entry_prices:
                self.entry_prices[symbol] = price
        else:
            self.current_positions.pop(symbol, None)
            self.entry_prices.pop(symbol, None)

    def update_value(self, current_value: float):
        self.current_value = current_value
        self.max_value = max(self.max_value, current_value)

    def check_signal(self, signal: Signal, total_value: float) -> Tuple[bool, str]:
        if not self.current_positions:
            return True, ""
        position_value = signal.strength * total_value
        if position_value / total_value > self.max_position_pct:
            return (
                False,
                f"单只仓位超限: {position_value / total_value:.2%} > {self.max_position_pct:.2%}",
            )
        total_position = sum(self.current_positions.values())
        if total_position / total_value > self.max_total_position:
            return (
                False,
                f"总仓位超限: {total_position / total_value:.2%} > {self.max_total_position:.2%}",
            )
        drawdown = (
            (self.max_value - self.current_value) / self.max_value
            if self.max_value > 0
            else 0
        )
        if drawdown > self.max_drawdown:
            return False, f"回撤超限: {drawdown:.2%} > {self.max_drawdown:.2%}"
        return True, ""

    def check_stop_loss(self, symbol: str, current_price: float) -> Tuple[bool, str]:
        if symbol not in self.entry_prices:
            return False, ""
        entry_price = self.entry_prices[symbol]
        loss = (current_price - entry_price) / entry_price
        if loss < -self.stop_loss:
            return True, f"止损触发: {loss:.2%} < -{self.stop_loss:.2%}"
        return False, ""

    def check_take_profit(self, symbol: str, current_price: float) -> Tuple[bool, str]:
        if symbol not in self.entry_prices:
            return False, ""
        entry_price = self.entry_prices[symbol]
        profit = (current_price - entry_price) / entry_price
        if profit > self.take_profit:
            return True, f"止盈触发: {profit:.2%} > {self.take_profit:.2%}"
        return False, ""

    def get_portfolio_risk(self) -> Dict:
        total_position_value = sum(self.current_positions.values())
        if self.current_value == 0:
            return {"total_exposure": 0, "num_positions": 0, "drawdown": 0}
        return {
            "total_exposure": total_position_value / self.current_value,
            "num_positions": len(self.current_positions),
            "drawdown": (self.max_value - self.current_value) / self.max_value
            if self.max_value > 0
            else 0,
            "max_position": max(self.current_positions.values()) / self.current_value
            if self.current_positions
            else 0,
        }


class PortfolioOptimizer:
    def __init__(self, risk_aversion: float = 1.0):
        self.risk_aversion = risk_aversion

    def optimize_weights(
        self, returns: pd.DataFrame, current_weights: Dict[str, float] = None
    ) -> Dict[str, float]:
        cov_matrix = returns.cov()
        expected_returns = returns.mean()
        num_assets = len(expected_returns)
        if current_weights is None:
            current_weights = {col: 1.0 / num_assets for col in expected_returns.index}
        adjusted_weights = {}
        for asset in expected_returns.index:
            weight = 0.5 * (1.0 / num_assets) + 0.5 * current_weights.get(asset, 0)
            adjusted_weights[asset] = min(0.2, max(0.01, weight))
        total = sum(adjusted_weights.values())
        return {k: v / total for k, v in adjusted_weights.items()}
