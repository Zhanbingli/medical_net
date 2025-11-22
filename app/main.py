from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.deps import get_db_session
from app.api.v1.routes import api_router
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.exceptions import register_exception_handlers
from app.db import session as db_session
from app.services.cache_service import get_cache_service
from app.core.http_client import close_http_client

settings = get_settings()
logger = get_logger(__name__)

# 速率限制器（可配置）
if settings.rate_limit_enabled:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[
            f"{settings.rate_limit_per_minute}/minute",
            f"{settings.rate_limit_per_hour}/hour",
        ],
    )
else:
    # 保持接口一致的空实现
    class _NoopLimiter:
        def limit(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

    limiter = _NoopLimiter()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("Application starting", app_name=settings.app_name)

    # 预热缓存连接
    try:
        cache = get_cache_service()
        await cache.get_redis()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning("Failed to connect to Redis", error=str(e))

    yield

    # 关闭
    logger.info("Application shutting down")

    # 清理资源
    try:
        cache = get_cache_service()
        await cache.close()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error("Error closing Redis connection", error=str(e))

    try:
        await close_http_client()
        logger.info("HTTP client closed")
    except Exception as e:
        logger.error("Error closing HTTP client", error=str(e))


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    debug=settings.debug,
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,  # 生产环境禁用文档
    redoc_url="/redoc" if settings.debug else None,
)

# 注册全局异常处理器
register_exception_handlers(app)

# 添加速率限制器
if settings.rate_limit_enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS配置 - 使用白名单而非 "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # 使用配置的白名单
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # 明确允许的方法
    allow_headers=["*"],
    max_age=3600,  # 预检请求缓存时间
)


@app.middleware("http")
async def add_db_to_context(request: Request, call_next):
    """数据库会话中间件"""
    response = JSONResponse({"detail": "Internal server error"}, status_code=500)
    try:
        request.state.db = db_session.SessionLocal()
        response = await call_next(request)
    except Exception as e:
        logger.error(
            "Request failed",
            path=request.url.path,
            method=request.method,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
    finally:
        if hasattr(request.state, "db"):
            request.state.db.close()
    return response


@app.get("/health", tags=["health"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")  # 健康检查也限流，防止滥用
async def health_check(request: Request, db: Session = Depends(get_db_session)):
    """
    健康检查端点

    返回系统健康状态，包括数据库连接
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": "1.0.0",
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": "Database connection failed",
            },
        )


app.include_router(api_router, prefix=settings.api_prefix)
if settings.enable_graphql:
    # 延迟导入以便可配置关闭 GraphQL
    from starlette_graphene3 import GraphQLApp
    from app.graphql_api.schema import schema

    app.add_route(
        settings.graphql_path,
        GraphQLApp(
            schema=schema,
            context_value=lambda request: {"db": request.state.db},
            on_get=True,
        ),
    )
