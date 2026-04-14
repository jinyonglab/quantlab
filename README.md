# InvestLab 量化投资研究平台

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-orange)](https://flask.palletsprojects.com/)

InvestLab 是一个面向 A 股市场的量化投资研究平台，提供策略开发、回测分析、风险管理和可视化界面等功能。

## ✨ 功能特性

- 📊 **多策略支持**：双均线、动量、布林带、网格交易等多种策略
- 📈 **回测引擎**：支持多策略并行回测，模拟/真实数据双模式
- 💰 **风险管理**：内置风险控制模块
- 🌐 **Web 界面**：基于 Flask 的可视化操作界面
- 📉 **数据支持**：支持 AKShare 数据源，自动缓存
- 📊 **结果可视化**：权益曲线、绩效指标图表展示

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 或 conda

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/InvestLab.git
cd InvestLab
```

2. **创建虚拟环境**
```bash
# 使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 或使用 conda
conda create -n investlab python=3.11
conda activate investlab
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

### 运行方式

#### 1. 命令行模式
```bash
# 交互模式
python main.py

# 单策略回测（模拟数据）
python main.py --mode single --strategy dual_ma --mock

# 单策略回测（真实数据）
python main.py --mode single --strategy dual_ma --real

# 多策略组合回测
python main.py --mode multi --mock
```

#### 2. Web 界面模式
```bash
python web_server.py
```
访问 http://localhost:8081

## 📁 项目结构

```
InvestLab/
├── backtest/          # 回测引擎模块
├── config/            # 配置文件
├── data/              # 数据获取与存储
│   ├── cache/         # 数据缓存
│   └── fetcher/       # 数据获取器
├── logs/              # 日志文件
├── results/           # 回测结果
├── risk/              # 风险管理
├── strategies/        # 策略模块
├── trading/           # 交易执行
├── utils/             # 工具函数
├── web/               # Web 前端
│   ├── static/        # 静态资源
│   └── templates/     # HTML 模板
├── main.py            # 主程序入口
├── web_server.py      # Web 服务器
└── requirements.txt   # 依赖列表
```

## 📊 支持的策略

| 策略名称 | 说明 | 参数 |
|---------|------|------|
| dual_ma | 双均线策略 | short_window, long_window |
| momentum | 动量策略 | lookback_days, top_n |
| bollinger | 布林带策略 | window, num_std |
| grid | 网格交易策略 | upper_price, lower_price, grid_num |
| multi_factor | 多因子策略 | - |

## 📝 使用示例

```python
from strategies import create_strategy
from backtest import BacktestEngine
from data import generate_mock_data

# 创建策略
strategy = create_strategy("dual_ma", short_window=20, long_window=60)

# 准备数据
data = generate_mock_data("600000", "20230101", "20240331")

# 运行回测
engine = BacktestEngine(initial_capital=1000000)
result = engine.run({"600000": data}, strategy)

print(f"总收益率: {result['total_return']}")
print(f"夏普比率: {result['sharpe_ratio']}")
```

## 🛠️ 配置说明

配置文件位于 `config/settings.yaml`，可修改：
- 回测参数（初始资金、手续费率等）
- 策略默认参数
- 数据缓存路径

## 📈 回测绩效指标

- 总收益率 (Total Return)
- 年化收益率 (Annual Return)
- 夏普比率 (Sharpe Ratio)
- 最大回撤 (Max Drawdown)
- 胜率 (Win Rate)
- 交易次数

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目基于 [MIT](LICENSE) 许可证开源。

## 🙏 致谢

- 数据支持：[AKShare](https://www.akshare.xyz/)
- Web框架：[Flask](https://flask.palletsprojects.com/)
- 图表库：[Chart.js](https://www.chartjs.org/)

## 📧 联系方式

如有问题，请提交 [Issue](https://github.com/yourusername/InvestLab/issues) 或联系作者。

---

**⚠️ 免责声明**：本项目仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。
