"""策略基类和6个核心策略"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Signal:
    symbol: str
    date: pd.Timestamp
    signal_type: str
    strength: float = 1.0


class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(
        self, data: Dict[str, pd.DataFrame], current_date: pd.Timestamp
    ) -> List[Signal]:
        pass

    def on_bar(
        self, symbol: str, df: pd.DataFrame, current_date: pd.Timestamp
    ) -> Optional[Signal]:
        return None


class DualMAStrategy(BaseStrategy):
    def __init__(
        self, short_window: int = 20, long_window: int = 60, position_pct: float = 0.2
    ):
        super().__init__(f"DualMA_{short_window}_{long_window}")
        self.short_window = short_window
        self.long_window = long_window
        self.position_pct = position_pct
        self.signals_cache: Dict[str, pd.DataFrame] = {}

    def generate_signals(
        self, data: Dict[str, pd.DataFrame], current_date: pd.Timestamp
    ) -> List[Signal]:
        signals = []
        for symbol, df in data.items():
            if current_date not in df.index:
                continue
            idx = df.index.get_loc(current_date)
            if idx < self.long_window:
                continue
            window_data = df.iloc[: idx + 1]
            ma_short = window_data["close"].rolling(self.short_window).mean().iloc[-1]
            ma_long = window_data["close"].rolling(self.long_window).mean().iloc[-1]
            ma_short_prev = (
                window_data["close"].rolling(self.short_window).mean().iloc[-2]
            )
            ma_long_prev = (
                window_data["close"].rolling(self.long_window).mean().iloc[-2]
            )
            if ma_short > ma_long and ma_short_prev <= ma_long_prev:
                signals.append(Signal(symbol, current_date, "BUY", self.position_pct))
            elif ma_short < ma_long and ma_short_prev >= ma_long_prev:
                signals.append(Signal(symbol, current_date, "SELL", 1.0))
        return signals


class MomentumStrategy(BaseStrategy):
    def __init__(
        self, lookback_days: int = 60, top_n: int = 30, rebalance_freq: str = "W"
    ):
        super().__init__(f"Momentum_{lookback_days}d")
        self.lookback_days = lookback_days
        self.top_n = top_n
        self.rebalance_freq = rebalance_freq
        self.current_positions: set = set()
        self.last_rebalance: Optional[pd.Timestamp] = None

    def should_rebalance(self, current_date: pd.Timestamp) -> bool:
        if self.last_rebalance is None:
            return True
        freq_map = {"D": 1, "W": 7, "M": 30}
        days = freq_map.get(self.rebalance_freq, 7)
        return (current_date - self.last_rebalance).days >= days

    def generate_signals(
        self, data: Dict[str, pd.DataFrame], current_date: pd.Timestamp
    ) -> List[Signal]:
        if not self.should_rebalance(current_date):
            return []
        momentum_scores = {}
        for symbol, df in data.items():
            if current_date not in df.index:
                continue
            idx = df.index.get_loc(current_date)
            if idx < self.lookback_days:
                continue
            period_data = df.iloc[idx - self.lookback_days : idx + 1]
            if len(period_data) < self.lookback_days * 0.8:
                continue
            momentum = period_data["close"].iloc[-1] / period_data["close"].iloc[0] - 1
            momentum_scores[symbol] = momentum
        sorted_stocks = sorted(
            momentum_scores.items(), key=lambda x: x[1], reverse=True
        )
        new_positions = set([s[0] for s in sorted_stocks[: self.top_n]])
        signals = []
        for symbol in new_positions - self.current_positions:
            signals.append(Signal(symbol, current_date, "BUY", 1.0 / self.top_n))
        for symbol in self.current_positions - new_positions:
            signals.append(Signal(symbol, current_date, "SELL", 1.0))
        self.current_positions = new_positions
        self.last_rebalance = current_date
        return signals


class MultiFactorStrategy(BaseStrategy):
    def __init__(
        self,
        factors: List[Dict] = None,
        top_n: int = 50,
        max_weight: float = 0.05,
        rebalance_freq: str = "M",
    ):
        super().__init__("MultiFactor")
        self.factors = factors or [
            {"name": "PE", "weight": 0.2, "direction": -1},
            {"name": "ROE", "weight": 0.25, "direction": 1},
            {"name": "Momentum20", "weight": 0.2, "direction": 1},
        ]
        self.top_n = top_n
        self.max_weight = max_weight
        self.rebalance_freq = rebalance_freq
        self.current_positions: Dict[str, float] = {}
        self.last_rebalance: Optional[pd.Timestamp] = None

    def should_rebalance(self, current_date: pd.Timestamp) -> bool:
        if self.last_rebalance is None:
            return True
        months = (
            1 if self.rebalance_freq == "M" else 4 if self.rebalance_freq == "Q" else 7
        )
        return (current_date - self.last_rebalance).days >= months * 30

    def calculate_factor_score(self, df: pd.DataFrame, factor: Dict) -> float:
        if factor["name"] == "Momentum20":
            if len(df) < 21:
                return 0
            return (df["close"].iloc[-1] / df["close"].iloc[-21] - 1) * factor[
                "direction"
            ]
        elif factor["name"] == "Momentum60":
            if len(df) < 61:
                return 0
            return (df["close"].iloc[-1] / df["close"].iloc[-61] - 1) * factor[
                "direction"
            ]
        return 0

    def generate_signals(
        self, data: Dict[str, pd.DataFrame], current_date: pd.Timestamp
    ) -> List[Signal]:
        if not self.should_rebalance(current_date):
            return []
        scores = {}
        for symbol, df in data.items():
            if current_date not in df.index:
                continue
            idx = df.index.get_loc(current_date)
            if idx < 60:
                continue
            factor_scores = []
            for factor in self.factors:
                score = self.calculate_factor_score(df.iloc[: idx + 1], factor)
                factor_scores.append(score * factor["weight"])
            scores[symbol] = sum(factor_scores)
        sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        new_positions = dict(sorted_stocks[: self.top_n])
        total_score = sum(new_positions.values())
        if total_score > 0:
            new_positions = {
                k: v / total_score * self.top_n * self.max_weight
                for k, v in new_positions.items()
            }
        signals = []
        for symbol in set(new_positions.keys()) - set(self.current_positions.keys()):
            signals.append(
                Signal(symbol, current_date, "BUY", new_positions.get(symbol, 0))
            )
        for symbol in set(self.current_positions.keys()) - set(new_positions.keys()):
            signals.append(Signal(symbol, current_date, "SELL", 1.0))
        self.current_positions = new_positions
        self.last_rebalance = current_date
        return signals


class BollingerBandStrategy(BaseStrategy):
    def __init__(
        self, window: int = 20, num_std: float = 2.0, position_pct: float = 0.15
    ):
        super().__init__(f"Bollinger_{window}_{num_std}")
        self.window = window
        self.num_std = num_std
        self.position_pct = position_pct
        self.signals_cache: Dict[str, pd.DataFrame] = {}

    def generate_signals(
        self, data: Dict[str, pd.DataFrame], current_date: pd.Timestamp
    ) -> List[Signal]:
        signals = []
        for symbol, df in data.items():
            if current_date not in df.index:
                continue
            idx = df.index.get_loc(current_date)
            if idx < self.window:
                continue
            window_data = df.iloc[: idx + 1]
            sma = window_data["close"].rolling(self.window).mean().iloc[-1]
            std = window_data["close"].rolling(self.window).std().iloc[-1]
            upper = sma + self.num_std * std
            lower = sma - self.num_std * std
            current_price = window_data["close"].iloc[-1]
            if current_price < lower:
                signals.append(Signal(symbol, current_date, "BUY", self.position_pct))
            elif current_price > upper:
                signals.append(Signal(symbol, current_date, "SELL", 1.0))
        return signals


class ETF50PairsStrategy(BaseStrategy):
    def __init__(
        self,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        lookback: int = 60,
    ):
        super().__init__(f"ETF50Pairs_{entry_threshold}_{exit_threshold}")
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.lookback = lookback
        self.positions: Dict[str, str] = {}
        self.spread_history: Dict[str, float] = {}

    def generate_signals(
        self, data: Dict[str, pd.DataFrame], current_date: pd.Timestamp
    ) -> List[Signal]:
        signals = []
        symbols = list(data.keys())
        if len(symbols) < 2:
            return signals
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i + 1 :]:
                if (
                    current_date not in data[sym1].index
                    or current_date not in data[sym2].index
                ):
                    continue
                idx1 = data[sym1].index.get_loc(current_date)
                idx2 = data[sym2].index.get_loc(current_date)
                if idx1 < self.lookback or idx2 < self.lookback:
                    continue
                price1 = data[sym1].iloc[idx1]["close"]
                price2 = data[sym2].iloc[idx1]["close"]
                hist1 = data[sym1].iloc[idx1 - self.lookback : idx1 + 1]["close"]
                hist2 = data[sym2].iloc[idx1 - self.lookback : idx1 + 1]["close"]
                spread = (price1 / hist1.iloc[0]) - (price2 / hist2.iloc[0])
                spread_mean = (hist1 / hist1.iloc[0] - hist2 / hist2.iloc[0]).mean()
                spread_std = (hist1 / hist1.iloc[0] - hist2 / hist2.iloc[0]).std()
                z_score = (spread - spread_mean) / spread_std if spread_std > 0 else 0
                pair_key = f"{sym1}_{sym2}"
                if z_score > self.entry_threshold:
                    if self.positions.get(pair_key) != "short_spread":
                        signals.append(Signal(sym1, current_date, "SELL", 1.0))
                        signals.append(Signal(sym2, current_date, "BUY", 1.0))
                        self.positions[pair_key] = "short_spread"
                elif z_score < -self.entry_threshold:
                    if self.positions.get(pair_key) != "long_spread":
                        signals.append(Signal(sym1, current_date, "BUY", 1.0))
                        signals.append(Signal(sym2, current_date, "SELL", 1.0))
                        self.positions[pair_key] = "long_spread"
                elif abs(z_score) < self.exit_threshold:
                    if pair_key in self.positions:
                        signals.append(Signal(sym1, current_date, "SELL", 1.0))
                        signals.append(Signal(sym2, current_date, "BUY", 1.0))
                        del self.positions[pair_key]
        return signals


class GridStrategy(BaseStrategy):
    def __init__(
        self,
        upper_price: float = 1.10,
        lower_price: float = 0.90,
        grid_num: int = 10,
        position_pct: float = 0.1,
    ):
        super().__init__(f"Grid_{upper_price}_{lower_price}_{grid_num}")
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.grid_num = grid_num
        self.position_pct = position_pct
        self.base_price: Optional[float] = None
        self.grid_levels: List[float] = []
        self.current_prices: Dict[str, float] = {}

    def initialize_grid(self, base_price: float):
        self.base_price = base_price
        self.upper_price = base_price * self.upper_price
        self.lower_price = base_price * self.lower_price
        step = (self.upper_price - self.lower_price) / self.grid_num
        self.grid_levels = [
            self.lower_price + i * step for i in range(self.grid_num + 1)
        ]

    def generate_signals(
        self, data: Dict[str, pd.DataFrame], current_date: pd.Timestamp
    ) -> List[Signal]:
        signals = []
        for symbol, df in data.items():
            if current_date not in df.index:
                continue
            current_price = df.iloc[df.index.get_loc(current_date)]["close"]
            if self.base_price is None:
                self.initialize_grid(current_price)
            self.current_prices[symbol] = current_price
            grid_pos = (current_price - self.lower_price) / (
                self.upper_price - self.lower_price
            )
            grid_idx = int(grid_pos * self.grid_num)
            grid_idx = max(0, min(self.grid_num, grid_idx))
            if current_price < self.grid_levels[grid_idx]:
                signals.append(Signal(symbol, current_date, "BUY", self.position_pct))
            elif current_price > self.grid_levels[grid_idx]:
                signals.append(Signal(symbol, current_date, "SELL", self.position_pct))
        return signals


STRATEGY_REGISTRY = {
    "dual_ma": DualMAStrategy,
    "momentum": MomentumStrategy,
    "multi_factor": MultiFactorStrategy,
    "bollinger": BollingerBandStrategy,
    "etf_50_pairs": ETF50PairsStrategy,
    "grid": GridStrategy,
}


def create_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
    strategy_class = STRATEGY_REGISTRY.get(strategy_name)
    if strategy_class is None:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    return strategy_class(**kwargs)
