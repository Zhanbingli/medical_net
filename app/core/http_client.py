"""
HTTP客户端 - 带重试机制和超时控制的HTTP客户端
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import logging

logger = logging.getLogger(__name__)


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

        # 创建HTTP客户端配置
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
                http2=True,  # 启用HTTP/2支持
            )
        return self._client

    async def close(self):
        """关闭HTTP客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.NetworkError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
    )
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        发送GET请求（带重试）

        Args:
            url: 请求URL
            params: 查询参数
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            HTTP响应对象

        Raises:
            httpx.HTTPError: HTTP错误
        """
        client = await self.get_client()

        try:
            response = await client.get(
                url,
                params=params,
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            # 对于4xx错误，不重试
            if 400 <= e.response.status_code < 500:
                logger.warning(
                    f"Client error {e.response.status_code} for URL: {url}"
                )
                raise
            # 对于5xx错误，让重试机制处理
            logger.error(
                f"Server error {e.response.status_code} for URL: {url}"
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.NetworkError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
    )
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        发送POST请求（带重试）

        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            HTTP响应对象

        Raises:
            httpx.HTTPError: HTTP错误
        """
        client = await self.get_client()

        try:
            response = await client.post(
                url,
                data=data,
                json=json,
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            if 400 <= e.response.status_code < 500:
                logger.warning(
                    f"Client error {e.response.status_code} for URL: {url}"
                )
                raise
            logger.error(
                f"Server error {e.response.status_code} for URL: {url}"
            )
            raise

    async def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        发送GET请求并返回JSON

        Args:
            url: 请求URL
            params: 查询参数
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            解析后的JSON数据
        """
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
        """
        发送POST请求并返回JSON

        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            解析后的JSON数据
        """
        response = await self.post(
            url, data=data, json=json, headers=headers, **kwargs
        )
        return response.json()


# 全局HTTP客户端实例
_http_client: Optional[ResilientHTTPClient] = None


def get_http_client() -> ResilientHTTPClient:
    """获取全局HTTP客户端实例"""
    global _http_client
    if _http_client is None:
        _http_client = ResilientHTTPClient(
            timeout=30.0,
            max_retries=3,
            max_connections=100,
        )
    return _http_client


async def close_http_client():
    """关闭全局HTTP客户端"""
    global _http_client
    if _http_client:
        await _http_client.close()
        _http_client = None
