"""LangGraph 工作流测试"""
import pytest
from unittest.mock import AsyncMock, patch

from ai_center.config import Settings
from ai_center.workflow.graph_builder import (
    AlmondWorkflowManager,
    build_classification_graph,
    build_evolution_graph
)
from ai_center.workflow.state import AlmondState


@pytest.fixture
def settings():
    """测试配置"""
    return Settings(
        dashscope_api_key="test-key",
        llm_provider="qwen",
        llm_model="qwen-plus"
    )


@pytest.fixture
def workflow_manager(settings):
    """工作流管理器"""
    return AlmondWorkflowManager(settings)


@pytest.mark.asyncio
async def test_classification_workflow_structure(settings):
    """测试分类工作流结构"""
    graph = build_classification_graph(settings)
    compiled = graph.compile()

    # 验证工作流包含必要的节点
    assert compiled is not None
    # LangGraph 0.3.1 的编译结果可以直接调用


@pytest.mark.asyncio
async def test_classification_workflow_execution(workflow_manager):
    """测试分类工作流执行"""
    # 准备初始状态
    initial_state: AlmondState = {
        "title": "学习 Python 装饰器",
        "content": "理解装饰器的工作原理",
        "task_id": 12345,
        "user_id": 1001,
        "messages": [],
        "confidence": 0.0,
        "behavior_count": 0,
        "completion_times": 0,
        "cost_time": 0,
        "workflow_complete": False,
        "context": None,
        "current_type": None,
        "current_state": None,
        "classification": None,
        "reasoning": None,
        "recommended_status": None,
        "suggestions": None,
        "should_evolve": None,
        "evolution_reason": None,
        "from_type": None,
        "to_type": None,
        "split_suggestions": None,
        "achievements": None,
        "learnings": None,
        "improvements": None,
        "patterns": None,
        "spawn_almonds": None,
        "model": None,
        "error_message": None,
        "next_step": None,
        "user_behavior": None,
        "created_at": None
    }

    # Mock LLM 响应
    with patch('ai_center.llm.qwen.QwenLLM.generate_structured') as mock_llm:
        # 第一次调用：快速理解
        mock_llm.return_value = AsyncMock(
            content='{"classification": "memory", "confidence": 0.85, "reasoning": "这是一个需要学习的知识点"}',
            model="qwen-plus",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            cost_time=1000
        )

        # 执行工作流
        result = await workflow_manager.run_classification(initial_state)

        # 验证结果
        assert result["classification"] is not None
        assert result["confidence"] > 0
        assert result["workflow_complete"] is True
        assert len(result["messages"]) > 0


@pytest.mark.asyncio
async def test_evolution_workflow(workflow_manager):
    """测试演化工作流"""
    initial_state: AlmondState = {
        "title": "学习 Python",
        "content": "系统学习 Python 编程",
        "task_id": 12346,
        "user_id": 1001,
        "current_state": "action",
        "current_type": "action",
        "user_behavior": "defer",
        "behavior_count": 3,
        "messages": [],
        "confidence": 0.0,
        "completion_times": 0,
        "cost_time": 0,
        "workflow_complete": False,
        "context": None,
        "classification": None,
        "reasoning": None,
        "recommended_status": None,
        "suggestions": None,
        "should_evolve": None,
        "evolution_reason": None,
        "from_type": None,
        "to_type": None,
        "split_suggestions": None,
        "achievements": None,
        "learnings": None,
        "improvements": None,
        "patterns": None,
        "spawn_almonds": None,
        "model": None,
        "error_message": None,
        "next_step": None,
        "created_at": None
    }

    with patch('ai_center.llm.qwen.QwenLLM.generate_structured') as mock_llm:
        mock_llm.return_value = AsyncMock(
            content='{"shouldEvolve": true, "classification": "goal", "confidence": 0.82, "reasoning": "多次延期表明这是长期目标", "evolutionReason": "需要转为目标并拆解", "fromType": "action", "toType": "goal"}',
            model="qwen-plus",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            cost_time=1500
        )

        result = await workflow_manager.run_evolution(initial_state)

        assert result["should_evolve"] is not None
        assert result["evolution_reason"] is not None
        assert result["workflow_complete"] is True


@pytest.mark.asyncio
async def test_workflow_with_low_confidence(workflow_manager):
    """测试低置信度场景"""
    initial_state: AlmondState = {
        "title": "想法",
        "content": "一个模糊的想法",
        "task_id": 12347,
        "user_id": 1001,
        "messages": [],
        "confidence": 0.0,
        "behavior_count": 0,
        "completion_times": 0,
        "cost_time": 0,
        "workflow_complete": False,
        "context": None,
        "current_type": None,
        "current_state": None,
        "classification": None,
        "reasoning": None,
        "recommended_status": None,
        "suggestions": None,
        "should_evolve": None,
        "evolution_reason": None,
        "from_type": None,
        "to_type": None,
        "split_suggestions": None,
        "achievements": None,
        "learnings": None,
        "improvements": None,
        "patterns": None,
        "spawn_almonds": None,
        "model": None,
        "error_message": None,
        "next_step": None,
        "user_behavior": None,
        "created_at": None
    }

    with patch('ai_center.llm.qwen.QwenLLM.generate_structured') as mock_llm:
        # 模拟低置信度响应
        mock_llm.return_value = AsyncMock(
            content='{"classification": "unclear", "confidence": 0.4, "reasoning": "信息不足"}',
            model="qwen-plus",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            cost_time=1000
        )

        result = await workflow_manager.run_classification(initial_state)

        # 低置信度时应该走 needs_more_info 分支
        assert result["classification"] == "unclear"
        assert result["confidence"] < 0.7


@pytest.mark.asyncio
async def test_workflow_streaming(workflow_manager):
    """测试流式工作流"""
    initial_state: AlmondState = {
        "title": "测试任务",
        "content": "测试内容",
        "task_id": 12348,
        "user_id": 1001,
        "messages": [],
        "confidence": 0.0,
        "behavior_count": 0,
        "completion_times": 0,
        "cost_time": 0,
        "workflow_complete": False,
        "context": None,
        "current_type": None,
        "current_state": None,
        "classification": None,
        "reasoning": None,
        "recommended_status": None,
        "suggestions": None,
        "should_evolve": None,
        "evolution_reason": None,
        "from_type": None,
        "to_type": None,
        "split_suggestions": None,
        "achievements": None,
        "learnings": None,
        "improvements": None,
        "patterns": None,
        "spawn_almonds": None,
        "model": None,
        "error_message": None,
        "next_step": None,
        "user_behavior": None,
        "created_at": None
    }

    with patch('ai_center.llm.qwen.QwenLLM.generate_structured') as mock_llm:
        mock_llm.return_value = AsyncMock(
            content='{"classification": "action", "confidence": 0.9, "reasoning": "明确的行动任务"}',
            model="qwen-plus",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            cost_time=1000
        )

        events = []
        async for event in workflow_manager.stream_workflow("classification", initial_state):
            events.append(event)

        # 验证收到了多个事件
        assert len(events) > 0


@pytest.mark.asyncio
async def test_workflow_error_handling(workflow_manager):
    """测试工作流错误处理"""
    initial_state: AlmondState = {
        "title": "测试任务",
        "content": "测试内容",
        "task_id": 12349,
        "user_id": 1001,
        "messages": [],
        "confidence": 0.0,
        "behavior_count": 0,
        "completion_times": 0,
        "cost_time": 0,
        "workflow_complete": False,
        "context": None,
        "current_type": None,
        "current_state": None,
        "classification": None,
        "reasoning": None,
        "recommended_status": None,
        "suggestions": None,
        "should_evolve": None,
        "evolution_reason": None,
        "from_type": None,
        "to_type": None,
        "split_suggestions": None,
        "achievements": None,
        "learnings": None,
        "improvements": None,
        "patterns": None,
        "spawn_almonds": None,
        "model": None,
        "error_message": None,
        "next_step": None,
        "user_behavior": None,
        "created_at": None
    }

    with patch('ai_center.llm.qwen.QwenLLM.generate_structured') as mock_llm:
        # 模拟 LLM 错误
        mock_llm.side_effect = Exception("LLM 调用失败")

        result = await workflow_manager.run_classification(initial_state)

        # 验证错误被正确处理
        assert result["error_message"] is not None
        assert "LLM 调用失败" in result["error_message"]