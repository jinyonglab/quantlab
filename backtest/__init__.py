"""回测引擎"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from strategies import BaseStrategy, Signal, create_strategy


@dataclass
class Trade:
    date: pd.Timestamp
    symbol: str
    action: str
    price: float
    shares: int
    commission: float
    order_id: str = ""


@dataclass
class Position:
    symbol: str
    shares: int
    avg_cost: float
    current_value: float = 0.0


@dataclass
class PortfolioState:
    cash: float
    positions: Dict[str, Position]
    total_value: float
    date: pd.Timestamp


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = 1000000,
        commission_rate: float = 0.0003,
        stamp_tax: float = 0.001,
        min_commission: float = 5,
        slippage: float = 0.001,
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.stamp_tax = stamp_tax
        self.min_commission = min_commission
        self.slippage = slippage
        self.reset()

    def reset(self):
        self.cash = self.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.daily_values: List[Dict] = []
        self.order_id = 0
        self.max_value = self.initial_capital
        self.current_date: Optional[pd.Timestamp] = None

    def _next_order_id(self) -> str:
        self.order_id += 1
        return f"ORDER_{self.order_id:06d}"

    def _get_commission(self, amount: float, is_sell: bool = False) -> float:
        commission = max(amount * self.commission_rate, self.min_commission)
        if is_sell:
            commission += amount * self.stamp_tax
        return commission

    def _apply_slippage(self, price: float, is_buy: bool = True) -> float:
        if is_buy:
            return price * (1 + self.slippage)
        return price * (1 - self.slippage)

    def _execute_order(
        self,
        signal: Signal,
        current_date: pd.Timestamp,
        current_prices: Dict[str, float],
    ):
        symbol = signal.symbol
        if symbol not in current_prices:
            return
        price = self._apply_slippage(
            current_prices[symbol], is_buy=(signal.signal_type == "BUY")
        )
        order_id = self._next_order_id()
        if signal.signal_type == "BUY":
            available_cash = self.cash * 0.3
            position_value = available_cash * signal.strength
            shares = int(position_value / price / 100) * 100
            if shares <= 0:
                return
            cost = shares * price
            commission = self._get_commission(cost, is_sell=False)
            total_cost = cost + commission
            if total_cost > self.cash:
                shares = int(self.cash / (price * 1.001) / 100) * 100
                if shares <= 0:
                    return
                total_cost = shares * price + self._get_commission(shares * price)
            self.cash -= total_cost
            if symbol in self.positions:
                old_pos = self.positions[symbol]
                new_shares = old_pos.shares + shares
                new_avg = (
                    old_pos.shares * old_pos.avg_cost + shares * price
                ) / new_shares
                self.positions[symbol] = Position(symbol, new_shares, new_avg)
            else:
                self.positions[symbol] = Position(symbol, shares, price)
            self.trades.append(
                Trade(current_date, symbol, "BUY", price, shares, commission, order_id)
            )
        elif signal.signal_type == "SELL":
            if symbol not in self.positions:
                return
            pos = self.positions[symbol]
            shares_to_sell = int(pos.shares * signal.strength / 100) * 100
            if shares_to_sell <= 0:
                shares_to_sell = 100
            shares_to_sell = min(shares_to_sell, pos.shares)
            revenue = shares_to_sell * price
            commission = self._get_commission(revenue, is_sell=True)
            net_revenue = revenue - commission
            self.cash += net_revenue
            pos.shares -= shares_to_sell
            if pos.shares <= 0:
                del self.positions[symbol]
            else:
                self.positions[symbol] = pos
            self.trades.append(
                Trade(
                    current_date,
                    symbol,
                    "SELL",
                    price,
                    shares_to_sell,
                    commission,
                    order_id,
                )
            )

    def _calculate_total_value(self, current_prices: Dict[str, float]) -> float:
        stock_value = sum(
            pos.shares * current_prices.get(pos.symbol, pos.avg_cost)
            for pos in self.positions.values()
        )
        return self.cash + stock_value

    def _update_daily_value(
        self, current_date: pd.Timestamp, current_prices: Dict[str, float]
    ):
        total_value = self._calculate_total_value(current_prices)
        self.max_value = max(self.max_value, total_value)
        self.daily_values.append(
            {
                "date": current_date,
                "cash": self.cash,
                "stock_value": total_value - self.cash,
                "total_value": total_value,
                "returns": (total_value - self.initial_capital) / self.initial_capital,
                "drawdown": (self.max_value - total_value) / self.max_value,
            }
        )

    def run(
        self,
        data: Dict[str, pd.DataFrame],
        strategy: BaseStrategy,
        start_date: str = None,
        end_date: str = None,
    ) -> Dict:
        self.reset()
        all_dates = sorted(set().union(*[set(df.index) for df in data.values()]))
        if start_date:
            all_dates = [d for d in all_dates if str(d)[:10] >= start_date]
        if end_date:
            all_dates = [d for d in all_dates if str(d)[:10] <= end_date]
        if not all_dates:
            raise ValueError("没有可用的交易日")
        for current_date in all_dates:
            self.current_date = current_date
            current_prices = {
                symbol: df.loc[current_date, "close"]
                for symbol, df in data.items()
                if current_date in df.index
            }
            self._update_daily_value(current_date, current_prices)
            signals = strategy.generate_signals(data, current_date)
            for signal in signals:
                self._execute_order(signal, current_date, current_prices)
        return self._generate_report()

    def _generate_report(self) -> Dict:
        df_values = pd.DataFrame(self.daily_values)
        if df_values.empty:
            return {"error": "No data"}
        df_values.set_index("date", inplace=True)
        total_return = (
            (df_values["total_value"].iloc[-1] / self.initial_capital - 1)
            if len(df_values) > 0
            else 0
        )
        returns = df_values["returns"].dropna()
        sharpe = (
            np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        )
        max_drawdown = (
            df_values["drawdown"].max() if "drawdown" in df_values.columns else 0
        )
        annual_return = total_return * 252 / len(df_values) if len(df_values) > 0 else 0
        win_rate = len(
            [
                t
                for t in self.trades
                if t.action == "SELL" and self._calculate_trade_pnl(t) > 0
            ]
        ) / max(1, len([t for t in self.trades if t.action == "SELL"]))
        return {
            "total_return": f"{total_return:.2%}",
            "annual_return": f"{annual_return:.2%}",
            "sharpe_ratio": f"{sharpe:.2f}",
            "max_drawdown": f"{max_drawdown:.2%}",
            "total_trades": len(self.trades),
            "win_rate": f"{win_rate:.2%}",
            "final_value": f"{df_values['total_value'].iloc[-1]:.2f}",
            "equity_curve": df_values,
            "trades": self.trades,
            "positions": self.positions,
        }

    def _calculate_trade_pnl(self, trade: Trade) -> float:
        return 0


class MultiStrategyBacktest:
    def __init__(self, engine: BacktestEngine = None):
        self.engine = engine or BacktestEngine()
        self.strategy_results: Dict[str, Dict] = {}

    def run_parallel(
        self,
        data: Dict[str, pd.DataFrame],
        strategies: List[Tuple[str, BaseStrategy]],
        start_date: str = None,
        end_date: str = None,
    ) -> Dict[str, Dict]:
        results = {}
        for name, strategy in strategies:
            print(f"Running strategy: {name}")
            self.engine.reset()
            result = self.engine.run(data, strategy, start_date, end_date)
            results[name] = result
            self.strategy_results[name] = result
        return results

    def run_portfolio(
        self,
        data: Dict[str, pd.DataFrame],
        strategies: List[Tuple[str, BaseStrategy]],
        weights: Dict[str, float] = None,
        start_date: str = None,
        end_date: str = None,
    ) -> Dict:
        weights = weights or {name: 1.0 / len(strategies) for name, _ in strategies}
        all_dates = sorted(set().union(*[set(df.index) for df in data.values()]))
        if start_date:
            all_dates = [d for d in all_dates if str(d)[:10] >= start_date]
        if end_date:
            all_dates = [d for d in all_dates if str(d)[:10] <= end_date]
        portfolio_values = []
        for current_date in all_dates:
            date_weights = {}
            for name, strategy in strategies:
                signals = strategy.generate_signals(data, current_date)
                date_weights[name] = len(signals)
            total_signals = sum(date_weights.values())
            if total_signals > 0:
                normalized = {k: v / total_signals for k, v in date_weights.items()}
            else:
                normalized = weights
            current_prices = {
                symbol: df.loc[current_date, "close"]
                for symbol, df in data.items()
                if current_date in df.index
            }
            portfolio_values.append(
                {"date": current_date, "weights": normalized, "prices": current_prices}
            )
        return {"portfolio_values": portfolio_values, "weights": weights}
