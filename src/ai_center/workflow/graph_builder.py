"""LangGraph 工作流构建器（基于 0.3.1）"""
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..config import Settings
from .state import AlmondState
from .notes import AlmondWorkflowNodes


def should_continue(state: AlmondState) -> Literal["classify", "needs_more_info", "complete"]:
    """条件边：根据置信度决定下一步

    LangGraph 0.3.1 使用 Literal 类型提示来约束边的目标
    """
    next_step = state.get("next_step", "complete")

    if next_step == "error":
        return "complete"

    return next_step  # type: ignore


def build_classification_graph(settings: Settings) -> StateGraph:
    """构建分类工作流图

    工作流：
    START -> understand -> [条件判断] -> classify/needs_more_info -> END
    """
    # 创建节点实例
    nodes = AlmondWorkflowNodes(settings)

    # 创建状态图（LangGraph 0.3.1 新语法）
    graph = StateGraph(AlmondState)

    # 添加节点
    graph.add_node("understand", nodes.understand_node)
    graph.add_node("classify", nodes.classify_node)
    graph.add_node("needs_more_info", nodes.needs_more_info_node)
    graph.add_node("error", nodes.error_node)

    # 添加边
    # START -> understand
    graph.add_edge(START, "understand")

    # understand -> [条件判断]
    graph.add_conditional_edges(
        "understand",
        should_continue,
        {
            "classify": "classify",
            "needs_more_info": "needs_more_info",
            "complete": END
        }
    )

    # classify -> END
    graph.add_edge("classify", END)
    graph.add_edge("needs_more_info", END)
    graph.add_edge("error", END)

    return graph


def build_evolution_graph(settings: Settings) -> StateGraph:
    """构建演化分析工作流图

    工作流：
    START -> evolution_analyze -> END
    """
    nodes = AlmondWorkflowNodes(settings)

    graph = StateGraph(AlmondState)

    # 添加节点
    graph.add_node("evolution_analyze", nodes.evolution_analyze_node)
    graph.add_node("error", nodes.error_node)

    # 添加边
    graph.add_edge(START, "evolution_analyze")
    graph.add_edge("evolution_analyze", END)
    graph.add_edge("error", END)

    return graph


def build_retrospect_graph(settings: Settings) -> StateGraph:
    """构建复盘工作流图

    工作流：
    START -> retrospect -> END
    """
    nodes = AlmondWorkflowNodes(settings)

    graph = StateGraph(AlmondState)

    # 添加节点
    graph.add_node("retrospect", nodes.retrospect_node)
    graph.add_node("error", nodes.error_node)

    # 添加边
    graph.add_edge(START, "retrospect")
    graph.add_edge("retrospect", END)
    graph.add_edge("error", END)

    return graph


def build_complete_workflow_graph(settings: Settings) -> StateGraph:
    """构建完整的杏仁生命周期工作流

    这是一个更复杂的工作流，展示了 LangGraph 的强大能力

    工作流：
    START -> understand -> classify -> [monitor] -> evolution_analyze -> retrospect -> END
    """
    nodes = AlmondWorkflowNodes(settings)

    graph = StateGraph(AlmondState)

    # 添加所有节点
    graph.add_node("understand", nodes.understand_node)
    graph.add_node("classify", nodes.classify_node)
    graph.add_node("needs_more_info", nodes.needs_more_info_node)
    graph.add_node("evolution_analyze", nodes.evolution_analyze_node)
    graph.add_node("retrospect", nodes.retrospect_node)
    graph.add_node("error", nodes.error_node)

    # 构建复杂的工作流
    graph.add_edge(START, "understand")

    graph.add_conditional_edges(
        "understand",
        should_continue,
        {
            "classify": "classify",
            "needs_more_info": "needs_more_info",
            "complete": END
        }
    )

    # 这里可以添加更多的条件边来实现复杂的演化逻辑
    # 例如：根据用户行为触发演化分析

    graph.add_edge("classify", END)
    graph.add_edge("needs_more_info", END)
    graph.add_edge("evolution_analyze", END)
    graph.add_edge("retrospect", END)
    graph.add_edge("error", END)

    return graph


class AlmondWorkflowManager:
    """杏仁工作流管理器

    统一管理不同类型的工作流
    """

    def __init__(self, settings: Settings, use_checkpointer: bool = False) -> None:
        self.settings = settings

        # LangGraph 0.3.1 的检查点机制
        # 用于保存中间状态，支持工作流暂停和恢复
        self.checkpointer = MemorySaver() if use_checkpointer else None

        # 预编译的工作流
        self._classification_graph = None
        self._evolution_graph = None
        self._retrospect_graph = None
        self._complete_graph = None

    def get_classification_workflow(self):
        """获取分类工作流"""
        if self._classification_graph is None:
            graph = build_classification_graph(self.settings)
            self._classification_graph = graph.compile(checkpointer=self.checkpointer)
        return self._classification_graph

    def get_evolution_workflow(self):
        """获取演化工作流"""
        if self._evolution_graph is None:
            graph = build_evolution_graph(self.settings)
            self._evolution_graph = graph.compile(checkpointer=self.checkpointer)
        return self._evolution_graph

    def get_retrospect_workflow(self):
        """获取复盘工作流"""
        if self._retrospect_graph is None:
            graph = build_retrospect_graph(self.settings)
            self._retrospect_graph = graph.compile(checkpointer=self.checkpointer)
        return self._retrospect_graph

    def get_complete_workflow(self):
        """获取完整工作流"""
        if self._complete_graph is None:
            graph = build_complete_workflow_graph(self.settings)
            self._complete_graph = graph.compile(checkpointer=self.checkpointer)
        return self._complete_graph

    async def run_classification(self, initial_state: AlmondState) -> AlmondState:
        """运行分类工作流"""
        workflow = self.get_classification_workflow()

        # LangGraph 0.3.1 使用 invoke 方法
        result = await workflow.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": f"task_{initial_state.get('task_id', 0)}"}}
        )

        return result

    async def run_evolution(self, initial_state: AlmondState) -> AlmondState:
        """运行演化工作流"""
        workflow = self.get_evolution_workflow()
        result = await workflow.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": f"task_{initial_state.get('task_id', 0)}"}}
        )
        return result

    async def run_retrospect(self, initial_state: AlmondState) -> AlmondState:
        """运行复盘工作流"""
        workflow = self.get_retrospect_workflow()
        result = await workflow.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": f"task_{initial_state.get('task_id', 0)}"}}
        )
        return result

    async def stream_workflow(self, workflow_type: str, initial_state: AlmondState):
        """流式执行工作流（实时返回中间状态）

        LangGraph 0.3.1 支持流式处理，可以实时看到每个节点的执行结果
        """
        if workflow_type == "classification":
            workflow = self.get_classification_workflow()
        elif workflow_type == "evolution":
            workflow = self.get_evolution_workflow()
        elif workflow_type == "retrospect":
            workflow = self.get_retrospect_workflow()
        else:
            workflow = self.get_complete_workflow()

        # 使用 astream 进行流式处理
        async for event in workflow.astream(
                initial_state,
                config={"configurable": {"thread_id": f"task_{initial_state.get('task_id', 0)}"}}
        ):
            yield event
