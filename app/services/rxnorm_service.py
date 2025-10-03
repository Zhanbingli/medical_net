"""RxNorm API服务 - 用于药物标准化命名和查询"""

import httpx
from typing import Optional, Dict, Any, List
from app.core.config import get_settings

settings = get_settings()


class RxNormService:
    """RxNorm API适配器"""

    def __init__(self):
        self.base_url = settings.rxnorm_api_base
        self.timeout = 10.0

    async def get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        通过药物名称获取RxCUI（RxNorm概念唯一标识符）

        Args:
            drug_name: 药物名称

        Returns:
            RxCUI字符串，如果未找到返回None
        """
        url = f"{self.base_url}/rxcui.json"
        params = {"name": drug_name}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # 检查是否有结果
                if "idGroup" in data and "rxnormId" in data["idGroup"]:
                    rxnorm_ids = data["idGroup"]["rxnormId"]
                    if rxnorm_ids:
                        # 返回第一个匹配的RxCUI
                        return rxnorm_ids[0] if isinstance(rxnorm_ids, list) else rxnorm_ids

                return None
        except Exception as e:
            print(f"Error fetching RxCUI for {drug_name}: {e}")
            return None

    async def get_drug_properties(self, rxcui: str) -> Optional[Dict[str, Any]]:
        """
        获取药物的详细属性

        Args:
            rxcui: RxNorm概念唯一标识符

        Returns:
            包含药物属性的字典
        """
        url = f"{self.base_url}/rxcui/{rxcui}/properties.json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if "properties" in data:
                    return data["properties"]

                return None
        except Exception as e:
            print(f"Error fetching drug properties for RxCUI {rxcui}: {e}")
            return None

    async def get_related_drugs(self, rxcui: str) -> List[Dict[str, Any]]:
        """
        获取相关药物（如通用名、品牌名等）

        Args:
            rxcui: RxNorm概念唯一标识符

        Returns:
            相关药物列表
        """
        url = f"{self.base_url}/rxcui/{rxcui}/related.json"
        params = {"tty": "SBD+SBDC+SCD+SCDC+BPCK+GPCK"}  # 各种药物类型

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                related = []
                if "relatedGroup" in data and "conceptGroup" in data["relatedGroup"]:
                    for group in data["relatedGroup"]["conceptGroup"]:
                        if "conceptProperties" in group:
                            related.extend(group["conceptProperties"])

                return related
        except Exception as e:
            print(f"Error fetching related drugs for RxCUI {rxcui}: {e}")
            return []

    async def validate_drug_name(self, drug_name: str) -> bool:
        """
        验证药物名称是否在RxNorm中存在

        Args:
            drug_name: 药物名称

        Returns:
            True如果药物存在，False否则
        """
        rxcui = await self.get_rxcui(drug_name)
        return rxcui is not None

    async def get_drug_context(self, drug_name: str) -> Dict[str, Any]:
        """
        获取药物的完整上下文信息（用于AI处理）

        Args:
            drug_name: 药物名称

        Returns:
            包含药物详细信息的字典
        """
        rxcui = await self.get_rxcui(drug_name)

        if not rxcui:
            return {
                "found": False,
                "drug_name": drug_name,
                "error": "Drug not found in RxNorm database"
            }

        # 获取药物属性
        properties = await self.get_drug_properties(rxcui)
        related = await self.get_related_drugs(rxcui)

        return {
            "found": True,
            "drug_name": drug_name,
            "rxcui": rxcui,
            "properties": properties,
            "related_drugs": related
        }
