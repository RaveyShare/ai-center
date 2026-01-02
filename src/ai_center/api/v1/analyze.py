"""分析 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from ...config import Settings, get_settings
from ...core.almond_analyzer import AlmondAnalyzer
from ...models.requests import (
    AnalyzeRequest,
    ClassificationRequest,
    UnderstandingRequest,
    EvolutionRequest,
    RetrospectRequest
)
from ...models.responses import (
    ClassificationResult,
    UnderstandingResult,
    EvolutionResult,
    RetrospectResult
)
from ...models.enums import AnalysisType
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def verify_token(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings)
) -> None:
    """验证 API Token"""
    if not settings.api_token:
        return  # 未配置 token，跳过验证
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # 支持 "Bearer {token}" 格式
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if token != settings.api_token:
        raise HTTPException(status_code=403, detail="Invalid token")


@router.post(
    "/analyze",
    response_model=ClassificationResult | EvolutionResult | RetrospectResult,
    summary="通用分析接口",
    description="根据 analysis_type 执行不同类型的分析"
)
async def analyze(
    request: AnalyzeRequest,
    settings: Settings = Depends(get_settings),
    _: None = Depends(verify_token)
):
    """通用分析接口（兼容 Java 服务调用）"""
    analyzer = AlmondAnalyzer(settings)
    
    try:
        if request.analysis_type == AnalysisType.CLASSIFICATION:
            return await analyzer.classify(
                title=request.title,
                content=request.content,
                text=request.text,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        elif request.analysis_type == AnalysisType.UNDERSTANDING:
            return await analyzer.understand(
                title=request.title,
                content=request.content,
                text=request.text,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        
        elif request.analysis_type == AnalysisType.EVOLUTION:
            # 演化分析需要更多参数，这里提供基础支持
            raise HTTPException(
                status_code=400,
                detail="For evolution analysis, please use /analyze/evolution endpoint"
            )
        
        elif request.analysis_type == AnalysisType.RETROSPECT:
            # 复盘分析需要更多参数
            raise HTTPException(
                status_code=400,
                detail="For retrospect analysis, please use /analyze/retrospect endpoint"
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported analysis type: {request.analysis_type}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/analyze/classify",
    response_model=ClassificationResult,
    summary="分类分析",
    description="判断杏仁的类型（memory/action/goal/unclear）"
)
async def classify(
    request: ClassificationRequest,
    settings: Settings = Depends(get_settings),
    _: None = Depends(verify_token)
) -> ClassificationResult:
    """分类分析"""
    logger.info(
        f"Classification request: task_id={request.task_id}, user_id={request.user_id}",
        extra={"task_id": request.task_id, "user_id": request.user_id}
    )
    
    analyzer = AlmondAnalyzer(settings)
    
    try:
        result = await analyzer.classify(
            title=request.title,
            content=request.content,
            text=request.text,
            context=request.context or "",
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        logger.info(
            f"Classification result: {result.classification} (confidence: {result.confidence})",
            extra={
                "task_id": request.task_id,
                "classification": result.classification,
                "confidence": result.confidence
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Classification failed: {str(e)}",
            extra={"task_id": request.task_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/analyze/understanding",
    response_model=UnderstandingResult,
    summary="理解澄清",
    description="为原始输入生成 title、clarified_text、tags，并返回 confidence"
)
async def understanding_api(
    request: UnderstandingRequest,
    settings: Settings = Depends(get_settings),
    _: None = Depends(verify_token)
) -> UnderstandingResult:
    logger.info(
        f"Understanding request: task_id={request.task_id}, user_id={request.user_id}",
        extra={"task_id": request.task_id, "user_id": request.user_id}
    )

    analyzer = AlmondAnalyzer(settings)

    try:
        result = await analyzer.understand(
            title=request.title,
            content=request.content,
            text=request.text,
            context=request.context or "",
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        logger.info(
            f"Understanding result: confidence={result.confidence}",
            extra={"task_id": request.task_id, "confidence": result.confidence}
        )
        return result
    except Exception as e:
        logger.error(
            f"Understanding failed: {str(e)}",
            extra={"task_id": request.task_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/analyze/evolution",
    response_model=EvolutionResult,
    summary="演化分析",
    description="判断杏仁是否需要演化到新类型"
)
async def evolution(
    request: EvolutionRequest,
    settings: Settings = Depends(get_settings),
    _: None = Depends(verify_token)
) -> EvolutionResult:
    """演化分析"""
    logger.info(
        f"Evolution request: task_id={request.task_id}, behavior={request.user_behavior}",
        extra={
            "task_id": request.task_id,
            "current_type": request.current_type,
            "behavior": request.user_behavior,
            "behavior_count": request.behavior_count
        }
    )
    
    analyzer = AlmondAnalyzer(settings)
    
    try:
        result = await analyzer.analyze_evolution(
            title=request.title,
            content=request.content,
            current_state=request.current_state,
            current_type=request.current_type,
            user_behavior=request.user_behavior.value,
            behavior_count=request.behavior_count,
            created_at=request.created_at or "",
            completion_times=request.completion_times
        )
        
        logger.info(
            f"Evolution result: should_evolve={result.should_evolve}, {result.from_type} -> {result.to_type}",
            extra={
                "task_id": request.task_id,
                "should_evolve": result.should_evolve,
                "from_type": result.from_type,
                "to_type": result.to_type
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Evolution analysis failed: {str(e)}",
            extra={"task_id": request.task_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/analyze/retrospect",
    response_model=RetrospectResult,
    summary="复盘分析",
    description="对已完成的杏仁进行复盘总结"
)
async def retrospect(
    request: RetrospectRequest,
    settings: Settings = Depends(get_settings),
    _: None = Depends(verify_token)
) -> RetrospectResult:
    """复盘分析"""
    logger.info(
        f"Retrospect request: task_id={request.task_id}",
        extra={"task_id": request.task_id}
    )
    
    analyzer = AlmondAnalyzer(settings)
    
    try:
        result = await analyzer.retrospect(
            title=request.title,
            content=request.content,
            completed_at=request.completed_at,
            created_at=request.created_at,
            completion_data=request.completion_data or ""
        )
        
        logger.info(
            f"Retrospect complete: {len(result.achievements)} achievements, {len(result.learnings)} learnings",
            extra={
                "task_id": request.task_id,
                "achievements_count": len(result.achievements),
                "learnings_count": len(result.learnings)
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Retrospect analysis failed: {str(e)}",
            extra={"task_id": request.task_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
