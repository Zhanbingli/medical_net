"""OpenFDA API服务 - 用于获取FDA药品标签、警告和不良事件信息"""

import httpx
from typing import Optional, Dict, Any, List
from app.core.config import get_settings

settings = get_settings()


class OpenFDAService:
    """OpenFDA API适配器"""

    def __init__(self):
        self.base_url = settings.openfda_api_base
        self.timeout = 15.0

    async def get_drug_label(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        获取FDA批准的药品标签信息

        Args:
            drug_name: 药物名称（品牌名或通用名）

        Returns:
            包含药品标签信息的字典
        """
        url = f"{self.base_url}/drug/label.json"
        params = {
            "search": f"openfda.brand_name:{drug_name} OR openfda.generic_name:{drug_name}",
            "limit": 1
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if "results" in data and len(data["results"]) > 0:
                    return data["results"][0]

                return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            print(f"HTTP error fetching drug label for {drug_name}: {e}")
            return None
        except Exception as e:
            print(f"Error fetching drug label for {drug_name}: {e}")
            return None

    async def get_warnings_and_precautions(self, drug_name: str) -> Dict[str, Any]:
        """
        获取药物的警告和注意事项

        Args:
            drug_name: 药物名称

        Returns:
            包含警告、注意事项和禁忌症的字典
        """
        label = await self.get_drug_label(drug_name)

        if not label:
            return {
                "found": False,
                "drug_name": drug_name,
                "warnings": [],
                "precautions": [],
                "contraindications": []
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
            "contraindications": contraindications if isinstance(contraindications, list) else [contraindications],
            "boxed_warning": boxed_warning if isinstance(boxed_warning, list) else [boxed_warning]
        }

    async def get_adverse_events(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取药物不良事件报告（FAERS数据）

        Args:
            drug_name: 药物名称
            limit: 返回结果数量限制

        Returns:
            不良事件列表
        """
        url = f"{self.base_url}/drug/event.json"
        params = {
            "search": f"patient.drug.openfda.brand_name:{drug_name}",
            "limit": limit
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if "results" in data:
                    return data["results"]

                return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            print(f"HTTP error fetching adverse events for {drug_name}: {e}")
            return []
        except Exception as e:
            print(f"Error fetching adverse events for {drug_name}: {e}")
            return []

    async def get_drug_context(self, drug_name: str) -> Dict[str, Any]:
        """
        获取药物的完整FDA上下文信息（用于AI处理）

        Args:
            drug_name: 药物名称

        Returns:
            包含FDA官方信息的字典
        """
        label = await self.get_drug_label(drug_name)

        if not label:
            return {
                "found": False,
                "drug_name": drug_name,
                "error": "Drug not found in FDA database"
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
            "manufacturer": label.get("openfda", {}).get("manufacturer_name", ["未知制造商"])[0] if label.get("openfda", {}).get("manufacturer_name") else "未知制造商"
        }

    async def check_drug_interactions_fda(self, drug_name: str) -> List[str]:
        """
        从FDA标签中提取药物相互作用信息

        Args:
            drug_name: 药物名称

        Returns:
            药物相互作用列表
        """
        label = await self.get_drug_label(drug_name)

        if not label:
            return []

        drug_interactions = label.get("drug_interactions", [])

        if isinstance(drug_interactions, list):
            return drug_interactions
        elif isinstance(drug_interactions, str):
            return [drug_interactions]
        else:
            return []
