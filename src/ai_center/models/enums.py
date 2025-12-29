"""杏仁状态机枚举定义"""
from enum import Enum


class AlmondState(str, Enum):
    """杏仁状态"""
    # 诞生态
    NEW = "new"  # 🌱 新杏仁

    # 理解态
    UNDERSTANDING = "understanding"  # 👀 被理解中
    UNDERSTOOD = "understood"  # 已理解

    # 演化态
    EVOLVING = "evolving"  # 🔄 演化中

    # 三条分化路径
    MEMORY = "memory"  # 🧠 记忆型
    ACTION = "action"  # ✅ 行动型
    GOAL = "goal"  # 🎯 目标型

    # 各路径的子状态
    REVIEWING = "reviewing"  # 🔁 复习中（记忆路径）
    ACTING = "acting"  # 进行中（行动路径）
    COMPLETED = "completed"  # ✔ 完成（行动路径）
    PROGRESSING = "progressing"  # 📈 推进中（目标路径）

    # 复盘与沉淀
    RETROSPECTING = "retrospecting"  # 🪞 复盘中
    ARCHIVED = "archived"  # 🌰 已沉淀/归档

    # 特殊状态
    UNCLEAR = "unclear"  # 不清晰（需要更多观察）


class AlmondType(str, Enum):
    """杏仁类型（分类结果）"""
    MEMORY = "memory"  # 记忆型：需要记忆和复习的内容
    ACTION = "action"  # 行动型：有明确动作和时间要求
    GOAL = "goal"  # 目标型：长期、抽象、可拆解
    UNCLEAR = "unclear"  # 不清晰：无法明确判断


class AnalysisType(str, Enum):
    """分析类型"""
    CLASSIFICATION = "classification"  # 初次分类
    EVOLUTION = "evolution"  # 演化分析
    RETROSPECT = "retrospect"  # 复盘分析
    UNDERSTANDING = "understanding"  # 理解分析


class UserBehavior(str, Enum):
    """用户行为（触发演化的信号）"""
    VIEW = "view"  # 查看
    EDIT = "edit"  # 编辑
    COMPLETE = "complete"  # 标记完成
    DEFER = "defer"  # 延期
    SPLIT = "split"  # 拆分
    MERGE = "merge"  # 合并
    LINK = "link"  # 关联其他杏仁
    REVIEW = "review"  # 复习
    COMMENT = "comment"  # 添加评论


class EvolutionTrigger(str, Enum):
    """演化触发器"""
    TIME_BASED = "time_based"  # 基于时间
    BEHAVIOR_BASED = "behavior_based"  # 基于用户行为
    CONTEXT_CHANGE = "context_change"  # 上下文变化
    MANUAL = "manual"  # 用户手动触发
    AI_SUGGESTION = "ai_suggestion"  # AI 主动建议


class LLMProvider(str, Enum):
    """LLM 提供商"""
    QWEN = "qwen"  # 阿里千问
    OPENAI = "openai"  # OpenAI
    CLAUDE = "claude"  # Anthropic Claude
    DEEPSEEK = "deepseek"  # DeepSeek
    CUSTOM = "custom"  # 自定义