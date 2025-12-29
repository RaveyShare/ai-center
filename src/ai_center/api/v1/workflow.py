"""基于 LangGraph 的工作流 API"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json

from ...config import Settings, get_settings
from ...models.requests import ClassificationRequest, EvolutionRequest, RetrospectRequest
from ...models.responses import ClassificationResult, EvolutionResult, RetrospectResult
from ...workflow.graph_builder import AlmondWorkflowManager
from ...workflow.state import AlmondState
from ...utils.logger import get_logger
from .analyze import verify_token

logger = get_logger(__name__)
router = APIRouter()


def _workflow_state_to_classification_result(state: AlmondState) -> ClassificationResult:
    """将工作流状态转换为分类结果"""
    return ClassificationResult(
        success=state.get("error_message") is None,
        classification=state.get("classification", "unclear"),
        confidence=state.get("confidence", 0.0),
        reasoning=state.get("reasoning", ""),
        recommended_status=state.get("recommended_status", "new"),
        model=state.get("model", "qwen-plus"),
        cost_time=state.get("cost_time", 0),
        error_message=state.get("error_message"),
        suggestions=state.get("suggestions")
    )


def _workflow_state_to_evolution_result(state: AlmondState) -> EvolutionResult:
    """将工作流状态转换为演化结果"""
    return EvolutionResult(
        success=state.get("error_message") is None,
        classification=state.get("classification", "unclear"),
        confidence=state.get("confidence", 0.0),
        reasoning=state.get("reasoning", ""),
        recommended_status=state.get("recommended_status", "new"),
        model=state.get("model", "qwen-plus"),
        cost_time=state.get("cost_time", 0),
        error_message=state.get("error_message"),
        should_evolve=state.get("should_evolve", False),
        evolution_reason=state.get("evolution_reason", ""),
        from_type=state.get("from_type", ""),
        to_type=state.get("to_type", ""),
        split_suggestions=state.get("split_suggestions"),
        suggestions=state.get("suggestions")
    )


def _workflow_state_to_retrospect_result(state: AlmondState) -> RetrospectResult:
    """将工作流状态转换为复盘结果"""
    return RetrospectResult(
        success=state.get("error_message") is None,
        classification="completed",
        confidence=state.get("confidence", 0.0),
        reasoning=state.get("reasoning", ""),
        recommended_status="archived",
        model=state.get("model", "qwen-plus"),
        cost_time=state.get("cost_time", 0),
        error_message=state.get("error_message"),
        achievements=state.get("achievements", []),
        learnings=state.get("learnings", []),
        improvements=state.get("improvements", []),
        patterns=state.get("patterns"),
        spawn_almonds=state.get("spawn_almonds"),
        suggestions=state.get("suggestions")
    )


@router.post(
    "/workflow/classify",
    response_model=ClassificationResult,
    summary="使用工作流进行分类",
    description="使用 LangGraph 工作流进行分类分析，支持多阶段决策"
)
async def workflow_classify(
        request: ClassificationRequest,
        settings: Settings = Depends(get_settings),
        _: None = Depends(verify_token)
) -> ClassificationResult:
    """使用工作流进行分类"""
    logger.info(
        f"Workflow classification: task_id={request.task_id}",
        extra={"task_id": request.task_id, "user_id": request.user_id}
    )

    try:
        # 创建工作流管理器
        manager = AlmondWorkflowManager(settings)

        # 构建初始状态
        initial_state: AlmondState = {
            "title": request.title,
            "content": request.content,
            "task_id": request.task_id,
            "user_id": request.user_id,
            "context": request.context,
            "messages": [],
            "confidence": 0.0,
            "behavior_count": 0,
            "completion_times": 0,
            "cost_time": 0,
            "workflow_complete": False,
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

        # 运行工作流
        final_state = await manager.run_classification(initial_state)

        # 转换为响应格式
        result = _workflow_state_to_classification_result(final_state)

        logger.info(
            f"Workflow classification result: {result.classification} (confidence: {result.confidence})",
            extra={
                "task_id": request.task_id,
                "classification": result.classification,
                "confidence": result.confidence
            }
        )

        return result

    except Exception as e:
        logger.error(
            f"Workflow classification failed: {str(e)}",
            extra={"task_id": request.task_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/workflow/evolution",
    response_model=EvolutionResult,
    summary="使用工作流进行演化分析"
)
async def workflow_evolution(
        request: EvolutionRequest,
        settings: Settings = Depends(get_settings),
        _: None = Depends(verify_token)
) -> EvolutionResult:
    """使用工作流进行演化分析"""
    logger.info(
        f"Workflow evolution: task_id={request.task_id}",
        extra={"task_id": request.task_id}
    )

    try:
        manager = AlmondWorkflowManager(settings)

        initial_state: AlmondState = {
            "title": request.title,
            "content": request.content,
            "task_id": request.task_id,
            "user_id": request.user_id,
            "current_state": request.current_state,
            "current_type": request.current_type,
            "user_behavior": request.user_behavior.value,
            "behavior_count": request.behavior_count,
            "created_at": request.created_at,
            "completion_times": request.completion_times,
            "messages": [],
            "confidence": 0.0,
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
            "next_step": None
        }

        final_state = await manager.run_evolution(initial_state)
        result = _workflow_state_to_evolution_result(final_state)

        logger.info(
            f"Workflow evolution result: should_evolve={result.should_evolve}",
            extra={"task_id": request.task_id, "should_evolve": result.should_evolve}
        )

        return result

    except Exception as e:
        logger.error(f"Workflow evolution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/workflow/retrospect",
    response_model=RetrospectResult,
    summary="使用工作流进行复盘"
)
async def workflow_retrospect(
        request: RetrospectRequest,
        settings: Settings = Depends(get_settings),
        _: None = Depends(verify_token)
) -> RetrospectResult:
    """使用工作流进行复盘"""
    logger.info(
        f"Workflow retrospect: task_id={request.task_id}",
        extra={"task_id": request.task_id}
    )

    try:
        manager = AlmondWorkflowManager(settings)

        initial_state: AlmondState = {
            "title": request.title,
            "content": request.content,
            "task_id": request.task_id,
            "user_id": request.user_id,
            "created_at": request.created_at,
            "context": request.completion_data,
            "messages": [],
            "confidence": 0.0,
            "behavior_count": 0,
            "completion_times": 0,
            "cost_time": 0,
            "workflow_complete": False,
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
            "user_behavior": None
        }

        final_state = await manager.run_retrospect(initial_state)
        result = _workflow_state_to_retrospect_result(final_state)

        logger.info(
            f"Workflow retrospect complete: {len(result.achievements)} achievements",
            extra={"task_id": request.task_id}
        )

        return result

    except Exception as e:
        logger.error(f"Workflow retrospect failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/workflow/stream/classify",
    summary="流式执行分类工作流",
    description="实时返回工作流的每个节点执行结果"
)
async def stream_classify(
        request: ClassificationRequest,
        settings: Settings = Depends(get_settings),
        _: None = Depends(verify_token)
):
    """流式执行分类工作流"""

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            manager = AlmondWorkflowManager(settings)

            initial_state: AlmondState = {
                "title": request.title,
                "content": request.content,
                "task_id": request.task_id,
                "user_id": request.user_id,
                "context": request.context,
                "messages": [],
                "confidence": 0.0,
                "behavior_count": 0,
                "completion_times": 0,
                "cost_time": 0,
                "workflow_complete": False,
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

            async for event in manager.stream_workflow("classification", initial_state):
                # 发送 Server-Sent Events
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_event = {"error": str(e)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )