# InvestLab 项目指南

本项目是一个 A 股量化投资研究平台。

## 项目结构

```
InvestLab/
├── backtest/          # 回测引擎
├── config/            # 配置文件
├── data/              # 数据模块（获取、存储、缓存）
├── logs/              # 日志（会被 .gitignore 忽略）
├── results/           # 回测结果（会被 .gitignore 忽略）
├── risk/              # 风险管理
├── strategies/        # 交易策略
├── trading/           # 交易执行
├── utils/             # 工具函数
├── web/               # Web 界面（Flask）
├── main.py            # 命令行入口
├── web_server.py      # Web 服务器入口
├── requirements.txt   # 依赖列表
├── setup.py           # 安装配置
└── tests/             # 测试目录
```

## 开发指南

### 代码规范
- 遵循 PEP 8
- 使用 4 空格缩进
- 函数和类需添加 docstring
- 类型注解（可选但推荐）

### 添加新策略
1. 在 `strategies/` 创建策略类
2. 继承 `BaseStrategy`
3. 实现 `generate_signals` 方法
4. 在 `strategies/__init__.py` 注册

### 运行测试
```bash
python -m pytest tests/
```

## 依赖管理

主要依赖：
- akshare: A 股数据获取
- pandas: 数据处理
- numpy: 数值计算
- flask: Web 服务
- matplotlib/plotly: 可视化

## 发布流程

1. 更新版本号（setup.py, CHANGELOG.md）
2. 运行测试确保通过
3. 打标签：`git tag v0.1.0`
4. 推送到 GitHub：`git push origin v0.1.0`
5. 创建 Release

## 注意事项

- 不要提交 venv/ 目录
- 不要提交 logs/ 和 results/ 目录
- 敏感信息使用环境变量
