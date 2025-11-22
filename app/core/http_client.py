"""
HTTP客户端 - 带重试机制和超时控制的HTTP客户端
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import httpx
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
    after_log,
)
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _should_retry(exc: BaseException) -> bool:
    """判定是否需要重试"""
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return exc.response.status_code >= 500
    return False


class ResilientHTTPClient:
    """
    具有弹性的HTTP客户端

    特性：
    - 自动重试
    - 指数退避
    - 超时控制
    - 连接池管理
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        max_connections: int = 100,
    ):
        """
        初始化HTTP客户端

        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            max_connections: 最大连接数
        """
        self.timeout = timeout
        self.max_retries = max_retries

        self.limits = httpx.Limits(
            max_keepalive_connections=max_connections,
            max_connections=max_connections,
            keepalive_expiry=30.0,
        )

        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """获取或创建HTTP客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=self.limits,
                follow_redirects=True,
                http2=True,
            )
        return self._client

    async def close(self):
        """关闭HTTP客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> httpx.Response:
        """统一请求入口，使用可配置的重试次数"""
        client = await self.get_client()

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception(_should_retry),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True,
        ):
            with attempt:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    data=data,
                    json=json,
                    **kwargs,
                )

                if response.status_code >= 400:
                    response.raise_for_status()

                return response

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """发送GET请求（带重试）"""
        try:
            return await self._request(
                "GET", url, params=params, headers=headers, **kwargs
            )
        except httpx.HTTPStatusError as e:
            if 400 <= e.response.status_code < 500:
                logger.warning("Client error for GET", status=e.response.status_code, url=url)
                raise
            logger.error("Server error for GET", status=e.response.status_code, url=url)
            raise

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """发送POST请求（带重试）"""
        try:
            return await self._request(
                "POST",
                url,
                data=data,
                json=json,
                headers=headers,
                **kwargs,
            )
        except httpx.HTTPStatusError as e:
            if 400 <= e.response.status_code < 500:
                logger.warning("Client error for POST", status=e.response.status_code, url=url)
                raise
            logger.error("Server error for POST", status=e.response.status_code, url=url)
            raise

    async def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """发送GET请求并返回JSON"""
        response = await self.get(url, params=params, headers=headers, **kwargs)
        return response.json()

    async def post_json(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """发送POST请求并返回JSON"""
        response = await self.post(
            url, data=data, json=json, headers=headers, **kwargs
        )
        return response.json()


_http_client: Optional[ResilientHTTPClient] = None


def get_http_client() -> ResilientHTTPClient:
    """获取全局HTTP客户端实例"""
    global _http_client
    if _http_client is None:
        _http_client = ResilientHTTPClient(
            timeout=settings.http_timeout_seconds,
            max_retries=settings.http_max_retries,
            max_connections=settings.http_max_connections,
        )
    return _http_client


async def close_http_client():
    """关闭全局HTTP客户端"""
    global _http_client
    if _http_client:
        await _http_client.close()
        _http_client = None
