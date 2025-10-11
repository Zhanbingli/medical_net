"""
结构化日志系统 - 提供统一的日志接口和格式
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
import json

from app.core.config import get_settings

settings = get_settings()


class StructuredLogger:
    """
    结构化日志记录器

    特性：
    - JSON格式输出
    - 上下文信息追踪
    - 不同环境的日志级别
    - 性能监控支持
    """

    def __init__(self, name: str):
        """
        初始化日志记录器

        Args:
            name: 日志记录器名称
        """
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """设置日志记录器"""
        # 设置日志级别
        if settings.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        # 避免重复添加handler
        if self.logger.handlers:
            return

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

        # 设置格式化器
        if settings.debug:
            # 开发环境：易读格式
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        else:
            # 生产环境：JSON格式
            formatter = JSONFormatter()

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _build_log_dict(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        构建日志字典

        Args:
            level: 日志级别
            message: 日志消息
            extra: 额外信息

        Returns:
            日志字典
        """
        log_dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": self.logger.name,
        }

        if extra:
            log_dict.update(extra)

        return log_dict

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        if settings.debug:
            log_dict = self._build_log_dict("DEBUG", message, kwargs)
            self.logger.debug(json.dumps(log_dict) if not settings.debug else message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        log_dict = self._build_log_dict("INFO", message, kwargs)
        self.logger.info(json.dumps(log_dict) if not settings.debug else message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        log_dict = self._build_log_dict("WARNING", message, kwargs)
        self.logger.warning(json.dumps(log_dict) if not settings.debug else message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        log_dict = self._build_log_dict("ERROR", message, kwargs)
        self.logger.error(json.dumps(log_dict) if not settings.debug else message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        log_dict = self._build_log_dict("CRITICAL", message, kwargs)
        self.logger.critical(json.dumps(log_dict) if not settings.debug else message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """记录异常日志"""
        log_dict = self._build_log_dict("ERROR", message, kwargs)
        self.logger.exception(json.dumps(log_dict) if not settings.debug else message, extra=kwargs)


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为JSON

        Args:
            record: 日志记录

        Returns:
            JSON格式的日志字符串
        """
        log_dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_dict.update(record.extra_fields)

        return json.dumps(log_dict)


# 日志记录器缓存
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        结构化日志记录器实例
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


# 默认日志记录器
logger = get_logger("app")


# 性能监控装饰器
def log_execution_time(func):
    """
    记录函数执行时间的装饰器

    使用方法:
        @log_execution_time
        async def my_function():
            pass
    """
    import functools
    import time

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        func_logger = get_logger(func.__module__)

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            func_logger.info(
                f"Function {func.__name__} completed",
                function=func.__name__,
                execution_time_ms=round(execution_time * 1000, 2),
                status="success",
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            func_logger.error(
                f"Function {func.__name__} failed",
                function=func.__name__,
                execution_time_ms=round(execution_time * 1000, 2),
                status="error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        func_logger = get_logger(func.__module__)

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            func_logger.info(
                f"Function {func.__name__} completed",
                function=func.__name__,
                execution_time_ms=round(execution_time * 1000, 2),
                status="success",
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            func_logger.error(
                f"Function {func.__name__} failed",
                function=func.__name__,
                execution_time_ms=round(execution_time * 1000, 2),
                status="error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    # 判断是否为异步函数
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
