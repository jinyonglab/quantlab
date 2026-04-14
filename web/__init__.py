"""Web前端服务"""

from flask import Flask, render_template, jsonify, request
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent.parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "web" / "templates"),
    static_folder=str(BASE_DIR / "web" / "static"),
)

from strategies import STRATEGY_REGISTRY, create_strategy
from backtest import BacktestEngine
from data import generate_mock_data, DataLoader, AShareDataFetcher


def get_available_strategies():
    return list(STRATEGY_REGISTRY.keys())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/strategies")
def api_strategies():
    return jsonify({"strategies": get_available_strategies()})


@app.route("/api/backtest", methods=["POST"])
def api_backtest():
    data = request.json
    strategy_name = data.get("strategy", "dual_ma")
    symbols = data.get("symbols", ["600000", "600016", "600036", "000001", "000002"])
    start_date = data.get("start_date", "20230101")
    end_date = data.get("end_date", "20240331")
    initial_capital = float(data.get("initial_capital", 1000000))

    use_mock = data.get("use_mock", True)

    if use_mock:
        stock_data = {}
        for symbol in symbols:
            df = generate_mock_data(symbol, start_date, end_date, initial_price=10.0)
            stock_data[symbol] = df
    else:
        fetcher = AShareDataFetcher(use_cache=True)
        loader = DataLoader(fetcher)
        stock_data = loader.load_universe_data(symbols, start_date, end_date)

    strategy_params = {
        "dual_ma": {"short_window": 20, "long_window": 60, "position_pct": 0.2},
        "momentum": {"lookback_days": 60, "top_n": 5, "rebalance_freq": "W"},
        "bollinger": {"window": 20, "num_std": 2.0, "position_pct": 0.15},
        "grid": {
            "upper_price": 1.10,
            "lower_price": 0.90,
            "grid_num": 10,
            "position_pct": 0.1,
        },
    }

    strategy = create_strategy(strategy_name, **strategy_params.get(strategy_name, {}))
    engine = BacktestEngine(initial_capital=initial_capital)

    result = engine.run(stock_data, strategy, start_date, end_date)

    equity_curve = []
    if "equity_curve" in result:
        for idx, row in result["equity_curve"].iterrows():
            equity_curve.append(
                {
                    "date": str(idx)[:10],
                    "value": float(row["total_value"]),
                    "returns": float(row.get("returns", 0)),
                }
            )

    return jsonify(
        {
            "success": True,
            "result": {
                "total_return": result.get("total_return", "N/A"),
                "annual_return": result.get("annual_return", "N/A"),
                "sharpe_ratio": result.get("sharpe_ratio", "N/A"),
                "max_drawdown": result.get("max_drawdown", "N/A"),
                "total_trades": result.get("total_trades", 0),
                "win_rate": result.get("win_rate", "N/A"),
                "final_value": result.get("final_value", "N/A"),
                "equity_curve": equity_curve,
                "num_positions": len(result.get("positions", {})),
            },
        }
    )


@app.route("/api/stocks")
def api_stocks():
    fetcher = AShareDataFetcher(use_cache=True)
    try:
        symbols = fetcher.get_index_components("000300")[:20]
        return jsonify({"success": True, "symbols": symbols})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    os.makedirs("./web/templates", exist_ok=True)
    os.makedirs("./web/static", exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
