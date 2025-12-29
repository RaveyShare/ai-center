"""LangGraph 工作流状态定义"""
from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import add_messages


class AlmondState(TypedDict):
    """杏仁分析工作流状态

    LangGraph 0.3.1 使用 TypedDict 定义状态
    """
    # 基础信息
    title: str
    content: str
    task_id: Optional[int]
    user_id: Optional[int]

    # 当前状态
    current_type: Optional[str]  # memory/action/goal/unclear
    current_state: Optional[str]  # new/understanding/evolving/etc
    confidence: float

    # 分析历史（用于多轮分析）
    messages: Annotated[list, add_messages]

    # 上下文信息
    context: Optional[str]
    user_behavior: Optional[str]
    behavior_count: int
    created_at: Optional[str]
    completion_times: int

    # 分析结果
    classification: Optional[str]
    reasoning: Optional[str]
    recommended_status: Optional[str]
    suggestions: Optional[list[str]]

    # 演化分析特有
    should_evolve: Optional[bool]
    evolution_reason: Optional[str]
    from_type: Optional[str]
    to_type: Optional[str]
    split_suggestions: Optional[list[dict]]

    # 复盘分析特有
    achievements: Optional[list[str]]
    learnings: Optional[list[str]]
    improvements: Optional[list[str]]
    patterns: Optional[dict]
    spawn_almonds: Optional[list[dict]]

    # 元数据
    model: Optional[str]
    cost_time: int
    error_message: Optional[str]

    # 工作流控制
    next_step: Optional[str]  # 下一步操作
    workflow_complete: bool  # 工作流是否完成