"""RxNorm API服务 - 用于药物标准化命名和查询"""

from typing import Optional, Dict, Any, List

from app.core.config import get_settings
from app.core.http_client import get_http_client
from app.core.logging import get_logger
from app.services.cache_service import CacheStrategy, get_cache_service

settings = get_settings()
logger = get_logger(__name__)


class RxNormService:
    """RxNorm API适配器"""

    def __init__(self):
        self.base_url = settings.rxnorm_api_base
        self.http_client = get_http_client()
        self.cache = get_cache_service()

    async def get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        通过药物名称获取RxCUI（带缓存和重试）
        """
        cache_key = f"rxnorm:rxcui:{drug_name.lower()}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        url = f"{self.base_url}/rxcui.json"
        params = {"name": drug_name}

        try:
            response = await self.http_client.get(url, params=params)
            data = response.json()

            if "idGroup" in data and "rxnormId" in data["idGroup"]:
                rxnorm_ids = data["idGroup"]["rxnormId"]
                if rxnorm_ids:
                    rxcui = rxnorm_ids[0] if isinstance(rxnorm_ids, list) else rxnorm_ids
                    await self.cache.set(cache_key, rxcui, CacheStrategy.RXNORM_TTL)
                    return rxcui

            return None
        except Exception as e:
            logger.error("Failed to fetch RxCUI", error=str(e), drug=drug_name)
            return None

    async def get_drug_properties(self, rxcui: str) -> Optional[Dict[str, Any]]:
        """
        获取药物的详细属性
        """
        cache_key = f"rxnorm:properties:{rxcui}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        url = f"{self.base_url}/rxcui/{rxcui}/properties.json"

        try:
            response = await self.http_client.get(url)
            data = response.json()

            if "properties" in data:
                await self.cache.set(cache_key, data["properties"], CacheStrategy.RXNORM_TTL)
                return data["properties"]

            return None
        except Exception as e:
            logger.error("Failed to fetch drug properties", error=str(e), rxcui=rxcui)
            return None

    async def get_related_drugs(self, rxcui: str) -> List[Dict[str, Any]]:
        """
        获取相关药物（如通用名、品牌名等）
        """
        cache_key = f"rxnorm:related:{rxcui}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        url = f"{self.base_url}/rxcui/{rxcui}/related.json"
        params = {"tty": "SBD+SBDC+SCD+SCDC+BPCK+GPCK"}  # 各种药物类型

        try:
            response = await self.http_client.get(url, params=params)
            data = response.json()

            related: List[Dict[str, Any]] = []
            if "relatedGroup" in data and "conceptGroup" in data["relatedGroup"]:
                for group in data["relatedGroup"]["conceptGroup"]:
                    if "conceptProperties" in group:
                        related.extend(group["conceptProperties"])

            await self.cache.set(cache_key, related, CacheStrategy.RXNORM_TTL)
            return related
        except Exception as e:
            logger.error("Failed to fetch related drugs", error=str(e), rxcui=rxcui)
            return []

    async def validate_drug_name(self, drug_name: str) -> bool:
        """
        验证药物名称是否在RxNorm中存在
        """
        rxcui = await self.get_rxcui(drug_name)
        return rxcui is not None

    async def get_drug_context(self, drug_name: str) -> Dict[str, Any]:
        """
        获取药物的完整上下文信息（用于AI处理）
        """
        rxcui = await self.get_rxcui(drug_name)

        if not rxcui:
            return {
                "found": False,
                "drug_name": drug_name,
                "error": "Drug not found in RxNorm database",
            }

        properties = await self.get_drug_properties(rxcui)
        related = await self.get_related_drugs(rxcui)

        return {
            "found": True,
            "drug_name": drug_name,
            "rxcui": rxcui,
            "properties": properties,
            "related_drugs": related,
        }
