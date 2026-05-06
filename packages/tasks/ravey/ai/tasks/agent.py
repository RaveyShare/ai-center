"""TaskPlannerAgent —— 任务规划 Agent。

基于 v3 Brain/Hand/Session 架构：
  - Brain：无状态推理循环，由 LLM 决定何时调用哪个工具
  - Hand：本模块的 build_hands() 提供五个规划工具
  - Session：所有事件追加到 SessionStore，崩溃可恢复
"""

from __future__ import annotations

from ravey.ai.agent_framework.brain import Brain, BrainConfig
from ravey.ai.agent_framework.hands import Hand
from ravey.ai.agent_framework.session import SessionStore

from ravey.ai.tasks.tools import build_hands


AGENT_NAME = "task-planner"


SYSTEM_PROMPT = """你是 TaskPlannerAgent，一个严谨的任务规划助手。

## 你的职责
把用户输入的自然语言需求拆成可执行的任务树，估算工时，并排入工作日历。

## 工作流程
1. 调用 parse_requirement 从用户文本里提取原始任务列表
2. 对每个任务调用 split_task 按模板展开成子任务（命中模板才拆，叶子任务保留）
3. 对结果调用 estimate_effort 递归填充工时
4. 调用 schedule_tasks 沿工作日历分配 start_date / due_date
5. 调用 save_task_tree 把最终任务树落到 JSON
6. 用一段简短摘要给用户回复，包括任务总数、总工时、起止日期、输出文件路径

## 注意事项
- 工具的输出本身已经是结构化数据，不要重复加工
- 单一调用链路（5 个工具按顺序），不需要循环重试
- 输入参数务必使用前一步工具的输出格式（dict / list[dict]）
- 不要凭空编造任务；用户没说的就不要补
"""


def make_brain_config(
    *,
    llm_provider: str = "dashscope",
    llm_model: str = "qwen-plus",
    max_tool_calls: int = 30,
) -> BrainConfig:
    """构造 TaskPlannerAgent 的 BrainConfig。"""
    return BrainConfig(
        agent_name=AGENT_NAME,
        system_prompt=SYSTEM_PROMPT,
        llm_provider=llm_provider,
        llm_model=llm_model,
        max_tool_calls=max_tool_calls,
    )


def build_brain(
    session_store: SessionStore,
    *,
    llm_provider: str = "dashscope",
    llm_model: str = "qwen-plus",
    extra_hands: dict[str, Hand] | None = None,
) -> Brain:
    """组装一个 TaskPlanner Brain。

    Args:
        session_store: 会话存储后端
        llm_provider: LLM 提供商
        llm_model: 具体模型
        extra_hands: 业务方追加的额外工具
    """
    hands: dict[str, Hand] = build_hands()
    if extra_hands:
        hands.update(extra_hands)

    config = make_brain_config(llm_provider=llm_provider, llm_model=llm_model)
    return Brain(config=config, session_store=session_store, hands=hands)
