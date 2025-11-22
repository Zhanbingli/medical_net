"""药物咨询和相互作用检查的API端点"""

from fastapi import APIRouter, HTTPException, Depends
from app.schemas.medication import (
    MedicationQuery,
    MedicationResponse,
    DrugInteractionQuery,
    DrugInteractionResponse,
    MedicalDisclaimer,
    SeverityLevel
)
from app.services.ai_agent_service import AIAgentService

router = APIRouter()


@router.post("/ask-medication", response_model=MedicationResponse, tags=["medication"])
async def ask_medication(query: MedicationQuery):
    """
    用药咨询端点 - 提供基于AI的药物信息和建议

    符合FDA CDS非医疗器械标准：
    - 提供信息而非医疗建议
    - 列出选项而非单一建议
    - 引导用户咨询医疗专业人员
    - 提供透明的信息来源
    """
    agent = AIAgentService()
    result = await agent.ask_medication(
        drug_name=query.drug_name,
        question=query.question
    )

    if not result["success"]:
        return MedicationResponse(
            success=False,
            error=result.get("error", "未知错误"),
            disclaimer=result.get("disclaimer", "此信息仅供教育用途")
        )

    return MedicationResponse(
        success=True,
        drug_name=result["drug_name"],
        question=result["question"],
        answer=result["answer"],
        disclaimer=result["disclaimer"],
        severity=SeverityLevel.INFO
    )


@router.post("/check-interaction", response_model=DrugInteractionResponse, tags=["medication"])
async def check_drug_interaction(query: DrugInteractionQuery):
    """
    药物相互作用检查端点

    检查两种药物之间的潜在相互作用
    数据来源：FDA药品标签
    """
    agent = AIAgentService()

    # 验证两种药物
    validation1 = await agent.validate_drug_input(query.drug1)
    validation2 = await agent.validate_drug_input(query.drug2)

    if not validation1["valid"]:
        return DrugInteractionResponse(
            success=False,
            error=validation1["error"]
        )

    if not validation2["valid"]:
        return DrugInteractionResponse(
            success=False,
            error=validation2["error"]
        )

    # 检查相互作用
    interaction_result = await agent.check_drug_interactions(
        drug1=validation1["cleaned_name"],
        drug2=validation2["cleaned_name"]
    )

    return DrugInteractionResponse(
        success=True,
        drug1=validation1["cleaned_name"],
        drug2=validation2["cleaned_name"],
        found_interactions=interaction_result["found_interactions"],
        interactions=interaction_result["interactions"],
        recommendation=interaction_result["recommendation"]
    )


@router.get("/disclaimer", response_model=MedicalDisclaimer, tags=["medication"])
async def get_disclaimer():
    """
    获取医疗免责声明

    应在首次使用时强制显示
    """
    return MedicalDisclaimer()


@router.post("/validate-drug", tags=["medication"])
async def validate_drug(drug_name: str):
    """
    验证药物名称是否在RxNorm数据库中存在

    Args:
        drug_name: 药物名称

    Returns:
        验证结果
    """
    agent = AIAgentService()
    validation = await agent.validate_drug_input(drug_name)

    return {
        "valid": validation["valid"],
        "drug_name": drug_name,
        "cleaned_name": validation.get("cleaned_name"),
        "error": validation.get("error")
    }


@router.get("/drug-info/{drug_name}", tags=["medication"])
async def get_drug_info(drug_name: str):
    """
    获取药物的基本信息（不使用AI）

    数据来源：RxNorm + OpenFDA
    """
    agent = AIAgentService()

    # 验证药物
    validation = await agent.validate_drug_input(drug_name)

    if not validation["valid"]:
        raise HTTPException(status_code=404, detail=validation["error"])

    # 获取RxNorm和FDA信息
    rxnorm_context = await agent.rxnorm_service.get_drug_context(validation["cleaned_name"])
    fda_context = await agent.openfda_service.get_drug_context(validation["cleaned_name"])

    return {
        "drug_name": validation["cleaned_name"],
        "rxnorm": rxnorm_context,
        "fda": fda_context,
        "disclaimer": "此信息仅供教育用途，不能替代专业医疗建议"
    }
