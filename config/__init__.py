"""配置加载模块"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    _instance: Optional["Config"] = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

    @property
    def system(self) -> Dict[str, Any]:
        return self._config.get("system", {})

    @property
    def backtest(self) -> Dict[str, Any]:
        return self._config.get("backtest", {})

    @property
    def data(self) -> Dict[str, Any]:
        return self._config.get("data", {})

    @property
    def strategies(self) -> Dict[str, Any]:
        return self._config.get("strategies", {})

    @property
    def risk(self) -> Dict[str, Any]:
        return self._config.get("risk", {})

    @property
    def trading(self) -> Dict[str, Any]:
        return self._config.get("trading", {})

    @property
    def logging_config(self) -> Dict[str, Any]:
        return self._config.get("logging", {})

    def get_strategy_config(self, name: str) -> Dict[str, Any]:
        return self.strategies.get(name, {})

    def reload(self):
        self._load_config()


config = Config()
