"""
Redis缓存服务 - 提供统一的缓存接口和策略
"""

from __future__ import annotations

import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()


class CacheService:
    """Redis缓存服务"""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def get_redis(self) -> aioredis.Redis:
        """获取Redis连接（懒加载）"""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=True,
                max_connections=10,
            )
        return self._redis

    async def close(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键

        Args:
            prefix: 缓存键前缀
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存键字符串
        """
        # 创建参数的哈希值
        params_str = json.dumps(
            {"args": args, "kwargs": sorted(kwargs.items())},
            sort_keys=True,
            default=str,
        )
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:{params_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，如果不存在返回None
        """
        redis = await self.get_redis()
        try:
            data = await redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"缓存读取错误: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: int = 3600
    ) -> bool:
        """
        设置缓存数据

        Args:
            key: 缓存键
            value: 要缓存的数据
            ttl: 过期时间（秒），默认1小时

        Returns:
            是否设置成功
        """
        redis = await self.get_redis()
        try:
            serialized = json.dumps(value, default=str)
            await redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"缓存写入错误: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        redis = await self.get_redis()
        try:
            await redis.delete(key)
            return True
        except Exception as e:
            print(f"缓存删除错误: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有缓存键

        Args:
            pattern: 匹配模式，如 "drug:*"

        Returns:
            删除的键数量
        """
        redis = await self.get_redis()
        try:
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"批量删除缓存错误: {e}")
            return 0

    def cached(
        self, prefix: str, ttl: int = 3600
    ) -> Callable:
        """
        缓存装饰器

        Args:
            prefix: 缓存键前缀
            ttl: 过期时间（秒）

        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_cache_key(prefix, *args, **kwargs)

                # 尝试从缓存获取
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # 执行函数
                result = await func(*args, **kwargs)

                # 保存到缓存
                await self.set(cache_key, result, ttl)

                return result

            return wrapper

        return decorator


# 全局缓存实例
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """获取全局缓存服务实例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# 预定义的缓存策略
class CacheStrategy:
    """缓存策略常量"""

    # RxNorm API - 药物信息变化较少
    RXNORM_TTL = 86400  # 24小时

    # OpenFDA API - FDA标签更新不频繁
    OPENFDA_TTL = 43200  # 12小时

    # 药物相互作用分析 - 基于固定数据的分析结果
    INTERACTION_TTL = 7200  # 2小时

    # AI生成内容 - 同样的输入应得到一致的结果
    AI_RESPONSE_TTL = 3600  # 1小时

    # 药物搜索结果
    SEARCH_TTL = 1800  # 30分钟

    # 健康检查
    HEALTH_CHECK_TTL = 60  # 1分钟
