"""日志配置模块"""
import logging
import sys
from pythonjsonlogger import jsonlogger

from ..config import get_settings


def setup_logging() -> None:
    """设置日志配置"""
    settings = get_settings()

    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)

    # 根据配置选择格式
    if settings.log_format == "json":
        # JSON 格式（生产环境）
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # 文本格式（开发环境）
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 设置第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("dashscope").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取日志器

    Args:
        name: 日志器名称（通常使用 __name__）

    Returns:
        日志器实例
    """
    # 确保日志已配置
    if not logging.getLogger().handlers:
        setup_logging()

    return logging.getLogger(name)