"""回测引擎测试"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest import BacktestEngine
from strategies import create_strategy
from data import generate_mock_data


class TestBacktestEngine(unittest.TestCase):
    """测试回测引擎"""

    def setUp(self):
        """测试前置准备"""
        self.engine = BacktestEngine(initial_capital=100000)

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.engine.initial_capital, 100000)

    def test_mock_data_generation(self):
        """测试模拟数据生成"""
        data = generate_mock_data("600000", "20230101", "20231231")
        self.assertIsNotNone(data)
        self.assertGreater(len(data), 0)


if __name__ == "__main__":
    unittest.main()
