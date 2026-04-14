"""策略模块测试"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies import create_strategy, STRATEGY_REGISTRY


class TestStrategies(unittest.TestCase):
    """测试策略模块"""

    def test_strategy_registry(self):
        """测试策略注册表"""
        self.assertIn("dual_ma", STRATEGY_REGISTRY)
        self.assertIn("momentum", STRATEGY_REGISTRY)
        self.assertIn("bollinger", STRATEGY_REGISTRY)

    def test_create_dual_ma_strategy(self):
        """测试创建双均线策略"""
        strategy = create_strategy("dual_ma", short_window=10, long_window=30)
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.short_window, 10)
        self.assertEqual(strategy.long_window, 30)

    def test_create_momentum_strategy(self):
        """测试创建动量策略"""
        strategy = create_strategy("momentum", lookback_days=20, top_n=5)
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.lookback_days, 20)


if __name__ == "__main__":
    unittest.main()
