"""数据获取子模块"""

from .akshare_fetcher import (
    AShareDataFetcher,
    DataLoader,
    DataCache,
    generate_mock_data,
)

__all__ = ["AShareDataFetcher", "DataLoader", "DataCache", "generate_mock_data"]
