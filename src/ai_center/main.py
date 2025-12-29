"""AI Center FastAPI 应用"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1 import analyze, health, workflow
from .config import get_settings
from .utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version}",
        extra={
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model
        }
    )
    yield
    logger.info("Shutting down AI Center")


# 创建 FastAPI 应用
app = FastAPI(
    title="Almond AI Center",
    description="杏仁 AI 分析中心 - 智能任务分类、演化分析与复盘服务",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()

    # 记录请求
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None
        }
    )

    # 处理请求
    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录响应
        logger.info(
            f"Response: {response.status_code}",
            extra={
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s"
            }
        )

        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {str(e)}",
            extra={
                "error": str(e),
                "process_time": f"{process_time:.3f}s"
            },
            exc_info=True
        )
        raise


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc) if get_settings().debug else "An error occurred"
        }
    )


# 注册路由
app.include_router(
    health.router,
    prefix="/v1",
    tags=["health"]
)

app.include_router(
    analyze.router,
    prefix="/v1/ai",
    tags=["analysis"]
)

app.include_router(
    workflow.router,
    prefix="/v1/ai",
    tags=["workflow"]
)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/v1/health"
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "ai_center.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )