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
    """数据缓存管理"""

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
    """A股数据获取器"""

    def __init__(self, cache_dir: str = "./data/cache", use_cache: bool = True):
        if not AKSHARE_AVAILABLE:
            raise RuntimeError("请安装AKShare: pip install akshare")

        self.cache = DataCache(cache_dir) if use_cache else None
        self.use_cache = use_cache

    def _convert_symbol(self, symbol: str) -> str:
        """转换股票代码格式"""
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
        """获取日线数据"""
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

    def get_minute_data(
        self, symbol: str, period: str = "60", start: str = None, end: str = None
    ) -> pd.DataFrame:
        """获取分钟级数据"""
        cache_key = f"minute_{symbol}_{period}_{start}_{end}"

        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key, max_age=300)
            if cached is not None:
                return cached

        symbol_conv = self._convert_symbol(symbol)

        try:
            if period == "5":
                df = ak.stock_zh_a_hist_min_em(
                    symbol=symbol_conv,
                    period="5",
                    start_date=start,
                    end_date=end,
                    adjust="qfq",
                )
            elif period == "15":
                df = ak.stock_zh_a_hist_min_em(
                    symbol=symbol_conv,
                    period="15",
                    start_date=start,
                    end_date=end,
                    adjust="qfq",
                )
            elif period == "30":
                df = ak.stock_zh_a_hist_min_em(
                    symbol=symbol_conv,
                    period="30",
                    start_date=start,
                    end_date=end,
                    adjust="qfq",
                )
            elif period == "60":
                df = ak.stock_zh_a_hist_min_em(
                    symbol=symbol_conv,
                    period="60",
                    start_date=start,
                    end_date=end,
                    adjust="qfq",
                )
            else:
                raise ValueError(f"不支持的周期: {period}")

            df["datetime"] = pd.to_datetime(df["时间"])
            df.set_index("datetime", inplace=True)

            result = df[["开盘", "收盘", "最高", "最低", "成交量"]].copy()
            result.columns = ["open", "close", "high", "low", "volume"]
            result = result.astype(
                {
                    "open": float,
                    "close": float,
                    "high": float,
                    "low": float,
                    "volume": float,
                }
            )

            if self.use_cache and self.cache:
                self.cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"获取分钟数据失败 {symbol} {period}: {e}")
            return pd.DataFrame()

    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        cache_key = f"info_{symbol}"

        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key, max_age=86400 * 7)
            if cached is not None:
                return cached

        symbol_conv = self._convert_symbol(symbol)

        try:
            df = ak.stock_individual_info_em(symbol=symbol_conv[2:])
            info = dict(zip(df["item"], df["value"]))

            if self.use_cache and self.cache:
                self.cache.set(cache_key, info)

            return info
        except Exception as e:
            logger.error(f"获取股票信息失败 {symbol}: {e}")
            return {}

    def get_stock_list(self, market: str = "all") -> pd.DataFrame:
        """获取股票列表"""
        cache_key = f"stocklist_{market}"

        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key, max_age=86400)
            if cached is not None:
                return cached

        try:
            if market == "all":
                df = ak.stock_zh_a_spot_em()
            elif market == "sh":
                df = ak.stock_sh_spot_em()
            elif market == "sz":
                df = ak.stock_sz_spot_em()
            else:
                df = ak.stock_zh_a_spot_em()

            if self.use_cache and self.cache:
                self.cache.set(cache_key, df)

            return df

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_index_components(self, index_code: str = "000300") -> List[str]:
        """获取指数成分股"""
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
            elif index_code == "000016":
                df = ak.index_stock_cons_weight_csindex(symbol="000016")
            else:
                df = ak.index_stock_cons(symbol=index_code)

            codes = df["代码"].tolist()

            if self.use_cache and self.cache:
                self.cache.set(cache_key, codes)

            return codes

        except Exception as e:
            logger.error(f"获取指数成分股失败 {index_code}: {e}")
            return []

    def get_financial_data(
        self, symbol: str, start: str = None, end: str = None
    ) -> pd.DataFrame:
        """获取财务数据"""
        cache_key = f"financial_{symbol}_{start}_{end}"

        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key, max_age=86400 * 7)
            if cached is not None:
                return cached

        try:
            df = ak.stock_financial_analysis_indicator(
                symbol=symbol, start_date=start, end_date=end
            )

            if self.use_cache and self.cache:
                self.cache.set(cache_key, df)

            return df

        except Exception as e:
            logger.error(f"获取财务数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_market_margin(self, date: str = None) -> pd.DataFrame:
        """获取融资融券数据"""
        try:
            if date:
                df = ak.stock_margin_detail_szse(date=date)
            else:
                df = ak.stock_margin_szse_last()
            return df
        except Exception as e:
            logger.error(f"获取融资融券数据失败: {e}")
            return pd.DataFrame()

    def get_block_trade(
        self, symbol: str, start: str = None, end: str = None
    ) -> pd.DataFrame:
        """获取大宗交易数据"""
        cache_key = f"block_{symbol}_{start}_{end}"

        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key, max_age=86400)
            if cached is not None:
                return cached

        try:
            df = ak.stock_block_trade_em(symbol=symbol, start_date=start, end_date=end)

            if self.use_cache and self.cache:
                self.cache.set(cache_key, df)

            return df

        except Exception as e:
            logger.error(f"获取大宗交易数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_etf_data(
        self, symbol: str = "510300", start: str = None, end: str = None
    ) -> pd.DataFrame:
        """获取ETF数据"""
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
    """统一数据加载器 - 支持批量加载和回测数据准备"""

    def __init__(self, fetcher: AShareDataFetcher = None):
        self.fetcher = fetcher or AShareDataFetcher()

    def load_universe_data(
        self, symbols: List[str], start: str, end: str, adjust: str = "qfq"
    ) -> Dict[str, pd.DataFrame]:
        """批量加载多只股票数据"""
        data = {}
        for symbol in symbols:
            df = self.fetcher.get_daily_data(symbol, start, end, adjust)
            if not df.empty:
                data[symbol] = df
        return data

    def load_index_data(
        self, index_code: str = "000300", start: str = None, end: str = None
    ) -> Tuple[List[str], Dict]:
        """加载指数成分股数据"""
        symbols = self.fetcher.get_index_components(index_code)
        if not symbols:
            return [], {}

        symbols = symbols[:100]
        data = self.load_universe_data(symbols, start or "20230101", end or "20240331")
        return symbols, data

    def prepare_backtest_data(
        self, universe: str = "hs300", start: str = "20230101", end: str = "20240331"
    ) -> Dict[str, pd.DataFrame]:
        """准备回测数据"""
        if universe == "hs300":
            symbols = self.fetcher.get_index_components("000300")
        elif universe == "zz500":
            symbols = self.fetcher.get_index_components("000905")
        elif universe == "zz50":
            symbols = self.fetcher.get_index_components("000016")
        else:
            symbols = self.fetcher.get_index_components("000300")

        symbols = symbols[:100]
        return self.load_universe_data(symbols, start, end)


def generate_mock_data(
    symbol: str, start: str, end: str, initial_price: float = 10.0
) -> pd.DataFrame:
    """生成模拟数据用于测试"""
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
