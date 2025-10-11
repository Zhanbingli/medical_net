"""
自定义异常和错误处理器
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


# 自定义异常类
class MedicalNetException(Exception):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DrugNotFoundException(MedicalNetException):
    """药物未找到异常"""

    def __init__(self, drug_name: str):
        super().__init__(
            message=f"药物 '{drug_name}' 未找到",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"drug_name": drug_name},
        )


class ExternalAPIException(MedicalNetException):
    """外部API调用异常"""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"外部服务 {service} 调用失败: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service, "error": message},
        )


class CacheException(MedicalNetException):
    """缓存操作异常"""

    def __init__(self, operation: str, message: str):
        super().__init__(
            message=f"缓存操作 {operation} 失败: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"operation": operation, "error": message},
        )


class AIServiceException(MedicalNetException):
    """AI服务异常"""

    def __init__(self, provider: str, message: str):
        super().__init__(
            message=f"AI服务 {provider} 调用失败: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"provider": provider, "error": message},
        )


class DatabaseException(MedicalNetException):
    """数据库操作异常"""

    def __init__(self, operation: str, message: str):
        super().__init__(
            message=f"数据库操作 {operation} 失败: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"operation": operation, "error": message},
        )


# 错误处理器
async def medical_net_exception_handler(
    request: Request, exc: MedicalNetException
) -> JSONResponse:
    """处理自定义异常"""
    logger.error(
        "MedicalNet exception",
        path=request.url.path,
        method=request.method,
        error=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """处理HTTP异常"""
    logger.warning(
        "HTTP exception",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "path": str(request.url.path),
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理请求验证异常"""
    errors = exc.errors()

    logger.warning(
        "Validation error",
        path=request.url.path,
        method=request.method,
        errors=errors,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "请求数据验证失败",
            "details": errors,
            "path": str(request.url.path),
        },
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """处理SQLAlchemy异常"""
    logger.error(
        "Database error",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "数据库操作失败",
            "details": {"type": type(exc).__name__},
            "path": str(request.url.path),
        },
    )


async def httpx_exception_handler(
    request: Request, exc: httpx.HTTPError
) -> JSONResponse:
    """处理httpx异常（外部API调用）"""
    logger.error(
        "External API error",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "外部服务暂时不可用",
            "details": {"type": type(exc).__name__},
            "path": str(request.url.path),
        },
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """处理所有未捕获的异常"""
    logger.exception(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "服务器内部错误",
            "message": "请稍后重试或联系技术支持",
            "path": str(request.url.path),
        },
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器

    Args:
        app: FastAPI应用实例
    """
    # 自定义异常
    app.add_exception_handler(MedicalNetException, medical_net_exception_handler)

    # FastAPI异常
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # 第三方库异常
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(httpx.HTTPError, httpx_exception_handler)

    # 通用异常（最后注册）
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")
