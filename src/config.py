"""
配置管理模块
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict


class Config:
    """配置管理类"""

    _instance = None
    _config: Dict[str, Any] = None

    def __new__(cls, config_path: str = None):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if config_path:
                cls._instance.load(config_path)
        return cls._instance

    def load(self, config_path: str):
        """加载配置文件"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        # 环境变量覆盖（可选）
        self._load_env_overrides()

        # 创建日志目录
        if self.get('logging.file.enabled', True):
            log_file = self.get('logging.file.path', 'logs/app.log')
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

    def _load_env_overrides(self):
        """加载环境变量覆盖"""
        # 代理配置
        if os.environ.get('HTTP_PROXY'):
            self._config.setdefault('proxy', {})['http_proxy'] = os.environ['HTTP_PROXY']
        if os.environ.get('HTTPS_PROXY'):
            self._config.setdefault('proxy', {})['https_proxy'] = os.environ['HTTPS_PROXY']
        if os.environ.get('NO_PROXY'):
            self._config.setdefault('proxy', {})['no_proxy'] = os.environ['NO_PROXY']

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持嵌套，用.分隔）"""
        if self._config is None:
            return default

        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """设置配置项"""
        if self._config is None:
            self._config = {}

        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, config_path: str):
        """保存配置到文件"""
        path = Path(config_path)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)

    def to_dict(self) -> Dict[str, Any]:
        """返回配置字典"""
        return self._config.copy() if self._config else {}


# 全局配置实例
config = Config()
