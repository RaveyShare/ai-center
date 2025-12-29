"""杏仁 AI-Center - 智能任务分类、演化分析与复盘服务"""

__version__ = "0.1.0"
__author__ = "Ravey"

from .config import Settings, get_settings
from .core.almond_analyzer import AlmondAnalyzer
from .workflow.graph_builder import AlmondWorkflowManager

__all__ = ["Settings", "get_settings", "AlmondAnalyzer", "AlmondWorkflowManager"]
