"""工具函数"""

import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import yaml


def setup_logging(
    log_file: str = "./logs/trading.log", level: str = "INFO", console: bool = True
):
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    log_level = getattr(logging, level.upper(), logging.INFO)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers = [logging.FileHandler(log_file, encoding="utf-8")]
    if console:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)
    return logging.getLogger(__name__)


def load_config(config_path: str = "./config/settings.yaml") -> Dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_results(result: Dict, output_dir: str = "./results"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = output_dir / f"backtest_result_{timestamp}.txt"
    with open(result_file, "w", encoding="utf-8") as f:
        for key, value in result.items():
            if key not in ("equity_curve", "trades", "positions"):
                f.write(f"{key}: {value}\n")
    return result_file


def plot_equity_curve(
    df: pd.DataFrame, output_path: str = "./results/equity_curve.png"
):
    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df["total_value"], label="Portfolio Value")
        plt.plot(
            df.index,
            df.get("returns", df["total_value"] / df["total_value"].iloc[0] - 1)
            .add(1)
            .mul(df["total_value"].iloc[0]),
            label="Cumulative Return",
        )
        plt.xlabel("Date")
        plt.ylabel("Value")
        plt.title("Equity Curve")
        plt.legend()
        plt.grid(True)
        plt.savefig(output_path)
        plt.close()
    except Exception as e:
        print(f"Plot failed: {e}")


def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.03) -> float:
    excess_returns = returns - risk_free_rate / 252
    return (
        np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        if excess_returns.std() > 0
        else 0
    )


def calculate_max_drawdown(values: pd.Series) -> float:
    peak = values.cummax()
    drawdown = (values - peak) / peak
    return drawdown.min()


def calculate_win_rate(trades: List) -> float:
    sell_trades = [t for t in trades if t.action == "SELL"]
    if not sell_trades:
        return 0
    wins = sum(1 for i in range(len(sell_trades) - 1) if i < len(sell_trades) - 1)
    return len(sell_trades) / max(1, len(sell_trades))


def format_number(num: float, decimal: int = 2) -> str:
    return f"{num:,.{decimal}f}"


def format_percent(num: float) -> str:
    return f"{num:.2%}"


class ProgressTracker:
    def __init__(self, total: int, desc: str = "Processing"):
        self.total = total
        self.current = 0
        self.desc = desc

    def update(self, n: int = 1):
        self.current += n
        pct = self.current / self.total * 100
        print(f"\r{self.desc}: {self.current}/{self.total} ({pct:.1f}%)", end="")

    def close(self):
        print()


def validate_data(data: Dict[str, pd.DataFrame]) -> bool:
    if not data:
        return False
    for symbol, df in data.items():
        required_cols = ["open", "high", "low", "close", "volume"]
        if not all(col in df.columns for col in required_cols):
            return False
        if df.isnull().any().any():
            return False
    return True


def align_data(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    all_dates = sorted(set().union(*[set(df.index) for df in data.values()]))
    aligned = {}
    for symbol, df in data.items():
        aligned[symbol] = df.reindex(all_dates).fillna(method="ffill")
    return aligned
