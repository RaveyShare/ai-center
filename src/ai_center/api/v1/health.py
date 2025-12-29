"""健康检查 API"""
from fastapi import APIRouter, Depends

from ...config import Settings, get_settings
from ...llm.factory import LLMFactory
from ...models.responses import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查服务和 LLM 的健康状态"
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """健康检查"""
    
    # 检查 LLM 可用性
    llm_available = False
    try:
        llm = LLMFactory.get_default(settings)
        llm_available = await llm.health_check()
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy" if llm_available else "degraded",
        version=settings.app_version,
        llm_provider=settings.llm_provider,
        llm_available=llm_available
    )


@router.get(
    "/ready",
    summary="就绪检查",
    description="检查服务是否就绪"
)
async def readiness_check():
    """就绪检查（K8s）"""
    return {"ready": True}


@router.get(
    "/live",
    summary="存活检查",
    description="检查服务是否存活"
)
async def liveness_check():
    """存活检查（K8s）"""
    return {"alive": True}