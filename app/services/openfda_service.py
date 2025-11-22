"""OpenFDA API服务 - 用于获取FDA药品标签、警告和不良事件信息"""

from typing import Optional, Dict, Any, List

from app.core.config import get_settings
from app.core.http_client import get_http_client
from app.core.logging import get_logger
from app.services.cache_service import CacheStrategy, get_cache_service

settings = get_settings()
logger = get_logger(__name__)


class OpenFDAService:
    """OpenFDA API适配器"""

    def __init__(self):
        self.base_url = settings.openfda_api_base
        self.http_client = get_http_client()
        self.cache = get_cache_service()

    async def get_drug_label(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        获取FDA批准的药品标签信息（带缓存与重试）
        """
        cache_key = f"openfda:label:{drug_name.lower()}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/drug/label.json"
        params = {
            "search": f"openfda.brand_name:{drug_name} OR openfda.generic_name:{drug_name}",
            "limit": 1,
        }

        try:
            response = await self.http_client.get(url, params=params)
            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                label = data["results"][0]
                await self.cache.set(cache_key, label, CacheStrategy.OPENFDA_TTL)
                return label

            return None
        except Exception as e:
            logger.error(
                "Failed to fetch FDA label",
                error=str(e),
                drug=drug_name,
            )
            return None

    async def get_warnings_and_precautions(self, drug_name: str) -> Dict[str, Any]:
        """
        获取药物的警告和注意事项
        """
        label = await self.get_drug_label(drug_name)

        if not label:
            return {
                "found": False,
                "drug_name": drug_name,
                "warnings": [],
                "precautions": [],
                "contraindications": [],
            }

        # 提取相关字段
        warnings = label.get("warnings", [])
        precautions = label.get("precautions", [])
        contraindications = label.get("contraindications", [])
        boxed_warning = label.get("boxed_warning", [])

        return {
            "found": True,
            "drug_name": drug_name,
            "warnings": warnings if isinstance(warnings, list) else [warnings],
            "precautions": precautions if isinstance(precautions, list) else [precautions],
            "contraindications": contraindications
            if isinstance(contraindications, list)
            else [contraindications],
            "boxed_warning": boxed_warning if isinstance(boxed_warning, list) else [boxed_warning],
        }

    async def get_adverse_events(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取药物不良事件报告（FAERS数据）
        """
        url = f"{self.base_url}/drug/event.json"
        params = {
            "search": f"patient.drug.openfda.brand_name:{drug_name}",
            "limit": limit,
        }

        try:
            response = await self.http_client.get(url, params=params)
            data = response.json()

            if "results" in data:
                return data["results"]

            return []
        except Exception as e:
            logger.error(
                "Failed to fetch adverse events",
                error=str(e),
                drug=drug_name,
            )
            return []

    async def get_drug_context(self, drug_name: str) -> Dict[str, Any]:
        """
        获取药物的完整FDA上下文信息（用于AI处理）
        """
        label = await self.get_drug_label(drug_name)

        if not label:
            return {
                "found": False,
                "drug_name": drug_name,
                "error": "Drug not found in FDA database",
            }

        # 提取关键信息
        warnings = label.get("warnings", ["无警告信息"])
        if isinstance(warnings, list) and warnings:
            warnings_text = warnings[0][:500]  # 限制长度
        else:
            warnings_text = str(warnings)[:500] if warnings else "无警告信息"

        indications = label.get("indications_and_usage", ["无适应症信息"])
        if isinstance(indications, list) and indications:
            indications_text = indications[0][:500]
        else:
            indications_text = str(indications)[:500] if indications else "无适应症信息"

        adverse_reactions = label.get("adverse_reactions", ["无不良反应信息"])
        if isinstance(adverse_reactions, list) and adverse_reactions:
            adverse_reactions_text = adverse_reactions[0][:500]
        else:
            adverse_reactions_text = str(adverse_reactions)[:500] if adverse_reactions else "无不良反应信息"

        dosage = label.get("dosage_and_administration", ["无剂量信息"])
        if isinstance(dosage, list) and dosage:
            dosage_text = dosage[0][:300]
        else:
            dosage_text = str(dosage)[:300] if dosage else "无剂量信息"

        return {
            "found": True,
            "drug_name": drug_name,
            "warnings": warnings_text,
            "indications": indications_text,
            "adverse_reactions": adverse_reactions_text,
            "dosage": dosage_text,
            "openfda": label.get("openfda", {}),
            "manufacturer": label.get("openfda", {}).get("manufacturer_name", ["未知制造商"])[0]
            if label.get("openfda", {}).get("manufacturer_name")
            else "未知制造商",
        }

    async def check_drug_interactions_fda(self, drug_name: str) -> List[str]:
        """
        从FDA标签中提取药物相互作用信息
        """
        label = await self.get_drug_label(drug_name)

        if not label:
            return []

        drug_interactions = label.get("drug_interactions", [])

        if isinstance(drug_interactions, list):
            return drug_interactions
        if isinstance(drug_interactions, str):
            return [drug_interactions]
        return []
