"""数据获取模块 - AKShare接口封装"""

import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pickle
import hashlib
import logging

try:
    import akshare as ak

    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    logging.warning("AKShare未安装，将使用模拟数据")

logger = logging.getLogger(__name__)


class DataCache:
    def __init__(self, cache_dir: str = "./data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_suffix = ".pkl"

    def _get_cache_path(self, key: str) -> Path:
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}{self.cache_suffix}"

    def get(self, key: str, max_age: int = 86400) -> Optional[pd.DataFrame]:
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None
        if time.time() - cache_path.stat().st_mtime > max_age:
            return None
        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def set(self, key: str, df: pd.DataFrame):
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(df, f)
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")

    def clear(self):
        for f in self.cache_dir.glob(f"*{self.cache_suffix}"):
            f.unlink()


class AShareDataFetcher:
    def __init__(self, cache_dir: str = "./data/cache", use_cache: bool = True):
        if not AKSHARE_AVAILABLE:
            raise RuntimeError("请安装AKShare: pip install akshare")
        self.cache = DataCache(cache_dir) if use_cache else None
        self.use_cache = use_cache

    def _convert_symbol(self, symbol: str) -> str:
        symbol = str(symbol).strip()
        if symbol.startswith(("sh", "sz")):
            return symbol
        if symbol.startswith("6"):
            return f"sh{symbol}"
        elif symbol.startswith(("0", "3")):
            return f"sz{symbol}"
        return symbol

    def get_daily_data(
        self, symbol: str, start: str, end: str, adjust: str = "qfq"
    ) -> pd.DataFrame:
        cache_key = f"daily_{symbol}_{start}_{end}_{adjust}"
        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        symbol_conv = self._convert_symbol(symbol)
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol_conv[2:],
                period="daily",
                start_date=start,
                end_date=end,
                adjust=adjust,
            )
            df.columns = [
                "date",
                "open",
                "close",
                "high",
                "low",
                "volume",
                "amount",
                "amplitude",
                "change_pct",
                "change_amount",
                "turnover",
            ]
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df = df.astype(
                {
                    "open": float,
                    "close": float,
                    "high": float,
                    "low": float,
                    "volume": float,
                    "amount": float,
                }
            )
            result = df[["open", "high", "low", "close", "volume", "amount"]]
            if self.use_cache and self.cache:
                self.cache.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"获取日线数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_list(self, market: str = "all") -> pd.DataFrame:
        cache_key = f"stocklist_{market}"
        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key, max_age=86400)
            if cached is not None:
                return cached
        try:
            if market == "all":
                df = ak.stock_zh_a_spot_em()
            else:
                df = ak.stock_zh_a_spot_em()
            if self.use_cache and self.cache:
                self.cache.set(cache_key, df)
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_index_components(self, index_code: str = "000300") -> List[str]:
        cache_key = f"index_{index_code}"
        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key, max_age=86400)
            if cached is not None:
                return cached
        try:
            if index_code == "000300":
                df = ak.index_stock_cons_weight_csindex(symbol="000300")
            elif index_code == "000905":
                df = ak.index_stock_cons_weight_csindex(symbol="000905")
            else:
                df = ak.index_stock_cons(symbol=index_code)
            codes = df["代码"].tolist()
            if self.use_cache and self.cache:
                self.cache.set(cache_key, codes)
            return codes
        except Exception as e:
            logger.error(f"获取指数成分股失败 {index_code}: {e}")
            return []

    def get_etf_data(
        self, symbol: str = "510300", start: str = None, end: str = None
    ) -> pd.DataFrame:
        cache_key = f"etf_{symbol}_{start}_{end}"
        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        try:
            df = ak.fund_etf_hist_em(
                symbol=symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq",
            )
            df.columns = [
                "date",
                "open",
                "close",
                "high",
                "low",
                "volume",
                "amount",
                "amplitude",
                "change_pct",
                "change_amount",
                "turnover",
            ]
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            result = df[["open", "high", "low", "close", "volume", "amount"]].copy()
            result = result.astype(
                {
                    "open": float,
                    "close": float,
                    "high": float,
                    "low": float,
                    "volume": float,
                    "amount": float,
                }
            )
            if self.use_cache and self.cache:
                self.cache.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"获取ETF数据失败 {symbol}: {e}")
            return pd.DataFrame()


class DataLoader:
    def __init__(self, fetcher: AShareDataFetcher = None):
        self.fetcher = fetcher or AShareDataFetcher()

    def load_universe_data(
        self, symbols: List[str], start: str, end: str, adjust: str = "qfq"
    ) -> Dict[str, pd.DataFrame]:
        data = {}
        for symbol in symbols:
            df = self.fetcher.get_daily_data(symbol, start, end, adjust)
            if not df.empty:
                data[symbol] = df
        return data

    def prepare_backtest_data(
        self, universe: str = "hs300", start: str = "20230101", end: str = "20240331"
    ) -> Dict[str, pd.DataFrame]:
        if universe == "hs300":
            symbols = self.fetcher.get_index_components("000300")
        elif universe == "zz500":
            symbols = self.fetcher.get_index_components("000905")
        else:
            symbols = self.fetcher.get_index_components("000300")
        symbols = symbols[:50]
        return self.load_universe_data(symbols, start, end)


def generate_mock_data(
    symbol: str, start: str, end: str, initial_price: float = 10.0
) -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end, freq="B")
    np.random.seed(hash(symbol) % 2**32)
    returns = np.random.normal(0.0005, 0.02, len(dates))
    prices = initial_price * np.exp(np.cumsum(returns))
    df = pd.DataFrame(
        {
            "open": prices * (1 + np.random.uniform(-0.005, 0.005, len(dates))),
            "high": prices * (1 + np.random.uniform(0.005, 0.015, len(dates))),
            "low": prices * (1 + np.random.uniform(-0.015, -0.005, len(dates))),
            "close": prices,
            "volume": np.random.uniform(1e6, 1e8, len(dates)),
            "amount": prices * np.random.uniform(1e6, 1e8, len(dates)),
        },
        index=dates,
    )
    return df
