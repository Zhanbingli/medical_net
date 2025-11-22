"""
增强的药物相互作用分析API端点

提供详细的副作用和疗效分析
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.drug_interaction_enhanced import DrugInteractionEnhancedService

router = APIRouter()


class DrugInteractionDetailedQuery(BaseModel):
    """详细相互作用查询请求"""
    drug1: str = Field(..., description="第一种药物名称", min_length=1, max_length=100)
    drug2: str = Field(..., description="第二种药物名称", min_length=1, max_length=100)


@router.post("/analyze-detailed", tags=["interaction-analysis"])
async def analyze_drug_interaction_detailed(query: DrugInteractionDetailedQuery):
    """
    详细分析两种药物的相互作用

    包括：
    - 单药的基线副作用
    - 联合用药的新副作用
    - 副作用风险增加的类型
    - 对疗效的影响（增强/减弱）
    - 相互作用机制
    - 严重程度分级
    - 临床管理建议

    这是一个增强版本的相互作用分析，提供比基础版本更详细的信息。
    """
    service = DrugInteractionEnhancedService()

    analysis = await service.analyze_interaction_detailed(
        drug1=query.drug1,
        drug2=query.drug2
    )

    return {
        "success": True,
        "data": analysis,
        "disclaimer": "此分析基于FDA公开数据和AI生成，仅供教育和参考用途。不能替代专业医疗建议。实际用药请咨询医生或药剂师。"
    }


@router.post("/compare-side-effects", tags=["interaction-analysis"])
async def compare_side_effects(query: DrugInteractionDetailedQuery):
    """
    对比单药副作用 vs 联合用药副作用

    显示：
    - Drug1 单独使用的副作用
    - Drug2 单独使用的副作用
    - 联合使用时新增的副作用
    - 联合使用时风险增加的副作用
    """
    service = DrugInteractionEnhancedService()

    analysis = await service.analyze_interaction_detailed(
        drug1=query.drug1,
        drug2=query.drug2
    )

    return {
        "success": True,
        "comparison": {
            "drug1_baseline": {
                "name": analysis["drug1"]["name"],
                "adverse_effects": analysis["drug1"]["baseline_adverse_effects"]
            },
            "drug2_baseline": {
                "name": analysis["drug2"]["name"],
                "adverse_effects": analysis["drug2"]["baseline_adverse_effects"]
            },
            "combined_use": {
                "new_adverse_effects": analysis["interaction"]["new_adverse_effects"],
                "increased_risk_effects": analysis["interaction"]["increased_risk_effects"],
                "combined_adverse_effects": analysis["interaction"]["combined_adverse_effects"]
            }
        },
        "summary": f"联合使用{query.drug1}和{query.drug2}时，除了各自的副作用外，还可能出现新的副作用或增加某些副作用的风险。",
        "disclaimer": "此分析基于FDA公开数据，仅供教育用途。"
    }


@router.post("/efficacy-impact", tags=["interaction-analysis"])
async def analyze_efficacy_impact(query: DrugInteractionDetailedQuery):
    """
    分析药物相互作用对疗效的影响

    返回：
    - Drug1的疗效是否受影响（增强/减弱/改变/无影响）
    - Drug2的疗效是否受影响
    - 详细的影响描述
    - 临床意义
    """
    service = DrugInteractionEnhancedService()

    analysis = await service.analyze_interaction_detailed(
        drug1=query.drug1,
        drug2=query.drug2
    )

    efficacy_impact = analysis["interaction"]["efficacy_impact"]

    return {
        "success": True,
        "efficacy_analysis": {
            "drug1": {
                "name": query.drug1,
                "indication": analysis["drug1"]["indications"][:200] + "..." if len(analysis["drug1"]["indications"]) > 200 else analysis["drug1"]["indications"],
                "efficacy_impact": efficacy_impact["drug1_efficacy"],
                "impact_description": _describe_efficacy_impact(efficacy_impact["drug1_efficacy"])
            },
            "drug2": {
                "name": query.drug2,
                "indication": analysis["drug2"]["indications"][:200] + "..." if len(analysis["drug2"]["indications"]) > 200 else analysis["drug2"]["indications"],
                "efficacy_impact": efficacy_impact["drug2_efficacy"],
                "impact_description": _describe_efficacy_impact(efficacy_impact["drug2_efficacy"])
            },
            "overall_description": efficacy_impact["description"],
            "clinical_significance": analysis["interaction"]["clinical_significance"]
        },
        "recommendations": analysis["interaction"]["management_recommendations"],
        "disclaimer": "疗效影响分析基于FDA数据和已知药理学，实际效果因人而异。"
    }


def _describe_efficacy_impact(impact_type: str) -> str:
    """描述疗效影响类型"""
    descriptions = {
        "enhanced": "疗效可能增强 - 药物作用可能比单独使用时更强",
        "reduced": "疗效可能减弱 - 药物作用可能比单独使用时更弱，可能需要调整剂量",
        "altered": "疗效可能改变 - 药物作用的性质可能发生变化",
        "neutral": "疗效可能无明显影响 - 但仍需医生评估"
    }
    return descriptions.get(impact_type, "影响未知")


@router.get("/severity-guide", tags=["interaction-analysis"])
async def get_severity_guide():
    """
    获取相互作用严重程度分级指南

    返回各个严重程度级别的定义和处理建议
    """
    return {
        "severity_levels": {
            "contraindicated": {
                "level": "禁忌",
                "color": "🔴 红色",
                "definition": "绝对不能同时使用，可能危及生命",
                "action": "避免联合使用，寻求替代药物",
                "examples": "华法林 + 大剂量阿司匹林（极高出血风险）"
            },
            "major": {
                "level": "严重",
                "color": "🔴 红色",
                "definition": "可能导致严重不良后果，需要密切监测或避免联用",
                "action": "仅在医生明确指导下使用，需要密切监测",
                "examples": "单胺氧化酶抑制剂 + SSRI（5-羟色胺综合征风险）"
            },
            "moderate": {
                "level": "中度",
                "color": "🟡 黄色",
                "definition": "可能需要调整剂量或增加监测",
                "action": "告知医生，可能需要调整用药方案",
                "examples": "某些抗生素 + 口服避孕药（可能降低避孕效果）"
            },
            "minor": {
                "level": "轻微",
                "color": "🟢 绿色",
                "definition": "通常不需要特殊干预",
                "action": "告知医生或药剂师，注意观察",
                "examples": "某些维生素 + 某些食物"
            }
        },
        "general_advice": [
            "始终告知医生和药剂师您正在使用的所有药物（包括非处方药和保健品）",
            "不要自行调整药物剂量或停药",
            "如出现任何异常症状，立即联系医疗专业人员",
            "定期复查和监测相关指标"
        ]
    }
