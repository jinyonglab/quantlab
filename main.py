"""主程序入口"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import config
from data import AShareDataFetcher, DataLoader, generate_mock_data
from strategies import (
    create_strategy,
    DualMAStrategy,
    MomentumStrategy,
    MultiFactorStrategy,
    BollingerBandStrategy,
    ETF50PairsStrategy,
    GridStrategy,
)
from backtest import BacktestEngine, MultiStrategyBacktest
from risk import RiskManager
from trading import TradeExecutor
from utils import setup_logging, save_results, plot_equity_curve, ProgressTracker


def run_single_strategy_backtest(
    strategy_name: str = "dual_ma", use_mock_data: bool = True, symbols: list = None
) -> dict:
    print(f"\n{'=' * 60}")
    print(f"运行单策略回测: {strategy_name}")
    print(f"{'=' * 60}\n")

    setup_logging()
    logger = logging.getLogger(__name__)

    start_time = time.time()

    if use_mock_data:
        print("使用模拟数据...")
        symbols = symbols or ["600000", "600016", "600036", "000001", "000002"]
        data = {}
        for symbol in symbols:
            df = generate_mock_data(symbol, "20230101", "20240331", initial_price=10.0)
            data[symbol] = df
        print(f"加载了 {len(data)} 只股票数据")
    else:
        print("加载真实数据...")
        fetcher = AShareDataFetcher()
        loader = DataLoader(fetcher)
        symbols = symbols or ["600000", "600016", "600036", "000001", "000002"]
        data = loader.load_universe_data(symbols, "20230101", "20240331")
        print(f"成功加载 {len(data)} 只股票数据")

    strategy_params = config.get_strategy_config(strategy_name)
    print(f"策略参数: {strategy_params}")

    strategy = create_strategy(strategy_name, **strategy_params)

    engine_config = config.backtest
    engine = BacktestEngine(
        initial_capital=engine_config.get("initial_capital", 1000000),
        commission_rate=engine_config.get("commission_rate", 0.0003),
        stamp_tax=engine_config.get("stamp_tax", 0.001),
        min_commission=engine_config.get("min_commission", 5),
        slippage=engine_config.get("slippage", 0.001),
    )

    print(f"\n初始资金: {engine.initial_capital:,.2f}")
    print(f"回测期间: 2023-01-01 至 2024-03-31")
    print(f"策略: {strategy.name}")
    print(f"\n开始回测...\n")

    result = engine.run(data, strategy, start_date="20230101", end_date="20240331")

    print(f"\n{'=' * 60}")
    print("回测结果")
    print(f"{'=' * 60}")
    print(f"总收益率:     {result.get('total_return', 'N/A')}")
    print(f"年化收益率:   {result.get('annual_return', 'N/A')}")
    print(f"夏普比率:     {result.get('sharpe_ratio', 'N/A')}")
    print(f"最大回撤:     {result.get('max_drawdown', 'N/A')}")
    print(f"总交易次数:   {result.get('total_trades', 0)}")
    print(f"胜率:         {result.get('win_rate', 'N/A')}")
    print(f"最终市值:     {result.get('final_value', 'N/A')}")

    save_results(result)

    if "equity_curve" in result:
        plot_equity_curve(result["equity_curve"])

    elapsed = time.time() - start_time
    print(f"\n回测耗时: {elapsed:.2f}秒")

    return result


def run_multi_strategy_backtest(use_mock_data: bool = True):
    print(f"\n{'=' * 60}")
    print("多策略组合回测")
    print(f"{'=' * 60}\n")

    setup_logging()

    if use_mock_data:
        symbols = [
            "600000",
            "600016",
            "600036",
            "000001",
            "000002",
            "000004",
            "000005",
            "000006",
            "000007",
            "000008",
        ]
        data = {}
        for symbol in symbols:
            df = generate_mock_data(symbol, "20230101", "20240331", initial_price=10.0)
            data[symbol] = df
    else:
        fetcher = AShareDataFetcher()
        loader = DataLoader(fetcher)
        symbols = ["600000", "600016", "600036", "000001", "000002"]
        data = loader.load_universe_data(symbols, "20230101", "20240331")

    strategies = [
        ("dual_ma", create_strategy("dual_ma", short_window=20, long_window=60)),
        ("momentum", create_strategy("momentum", lookback_days=60, top_n=5)),
        ("bollinger", create_strategy("bollinger", window=20, num_std=2)),
    ]

    engine = BacktestEngine(initial_capital=1000000)
    multi_backtest = MultiStrategyBacktest(engine)

    results = multi_backtest.run_parallel(
        data, strategies, start_date="20230101", end_date="20240331"
    )

    print(f"\n{'=' * 60}")
    print("各策略回测结果")
    print(f"{'=' * 60}")

    for name, result in results.items():
        print(f"\n策略: {name}")
        print(f"  总收益率:   {result.get('total_return', 'N/A')}")
        print(f"  夏普比率:   {result.get('sharpe_ratio', 'N/A')}")
        print(f"  最大回撤:   {result.get('max_drawdown', 'N/A')}")

    return results


def run_with_real_data():
    print(f"\n{'=' * 60}")
    print("使用真实数据运行")
    print(f"{'=' * 60}\n")

    fetcher = AShareDataFetcher(use_cache=True)
    print("正在获取沪深300成分股...")
    hs300_symbols = fetcher.get_index_components("000300")
    print(f"获取到 {len(hs300_symbols)} 只股票")

    symbols = hs300_symbols[:20]
    print(f"加载前 {len(symbols)} 只股票数据...")

    data = fetcher.load_universe_data(symbols, "20230101", "20240331")
    print(f"成功加载 {len(data)} 只股票数据")

    strategy = create_strategy("dual_ma", short_window=20, long_window=60)
    engine = BacktestEngine(initial_capital=1000000)

    result = engine.run(data, strategy)

    print(f"\n回测结果:")
    print(f"  总收益率: {result.get('total_return', 'N/A')}")
    print(f"  夏普比率: {result.get('sharpe_ratio', 'N/A')}")

    return result


def interactive_mode():
    print(f"\n{'=' * 60}")
    print("InvestLab 量化交易系统")
    print(f"{'=' * 60}")
    print("\n1. 单策略回测 (模拟数据)")
    print("2. 多策略组合回测 (模拟数据)")
    print("3. 单策略回测 (真实数据)")
    print("4. 退出")

    choice = input("\n请选择 (1-4): ").strip()

    if choice == "1":
        strategy_name = input(
            "请输入策略名称 (dual_ma/momentum/multi_factor/bollinger/grid): "
        ).strip()
        if not strategy_name:
            strategy_name = "dual_ma"
        run_single_strategy_backtest(strategy_name, use_mock_data=True)
    elif choice == "2":
        run_multi_strategy_backtest(use_mock_data=True)
    elif choice == "3":
        run_with_real_data()
    elif choice == "4":
        print("退出系统")
        sys.exit(0)
    else:
        print("无效选择")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="InvestLab 量化交易系统")
    parser.add_argument(
        "--mode",
        type=str,
        default="interactive",
        choices=["interactive", "single", "multi", "realtime"],
        help="运行模式",
    )
    parser.add_argument("--strategy", type=str, default="dual_ma", help="策略名称")
    parser.add_argument(
        "--mock", action="store_true", default=True, help="使用模拟数据"
    )
    parser.add_argument("--real", action="store_true", help="使用真实数据")

    args = parser.parse_args()

    if args.mode == "single":
        run_single_strategy_backtest(args.strategy, use_mock_data=not args.real)
    elif args.mode == "multi":
        run_multi_strategy_backtest(use_mock_data=not args.real)
    elif args.mode == "interactive":
        interactive_mode()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
