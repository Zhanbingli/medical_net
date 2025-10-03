"""药物咨询相关的Pydantic模型"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class SeverityLevel(str, Enum):
    """严重程度级别"""
    CRITICAL = "critical"  # 红色/严重 - 立即咨询医生
    MODERATE = "moderate"  # 黄色/中度 - 与医生讨论
    MILD = "mild"  # 绿色/轻微 - 低风险
    INFO = "info"  # 灰色/信息性 - 一般教育内容


class MedicationQuery(BaseModel):
    """用药咨询请求"""
    drug_name: str = Field(..., description="药物名称（品牌名或通用名）", min_length=1, max_length=100)
    question: str = Field(..., description="用户问题", min_length=1, max_length=500)


class DrugInteractionQuery(BaseModel):
    """药物相互作用查询请求"""
    drug1: str = Field(..., description="第一种药物名称", min_length=1, max_length=100)
    drug2: str = Field(..., description="第二种药物名称", min_length=1, max_length=100)


class MedicationResponse(BaseModel):
    """用药咨询响应"""
    success: bool = Field(..., description="请求是否成功")
    drug_name: Optional[str] = Field(None, description="药物名称")
    question: Optional[str] = Field(None, description="用户问题")
    answer: Optional[str] = Field(None, description="AI生成的回答")
    error: Optional[str] = Field(None, description="错误信息（如果失败）")
    disclaimer: str = Field(..., description="医疗免责声明")
    severity: SeverityLevel = Field(default=SeverityLevel.INFO, description="警告严重程度")
    sources: List[str] = Field(default_factory=lambda: ["FDA Drug Label", "RxNorm"], description="信息来源")


class DrugInteraction(BaseModel):
    """药物相互作用详情"""
    drug: str = Field(..., description="药物名称")
    interacts_with: str = Field(..., description="相互作用的药物")
    description: str = Field(..., description="相互作用描述")
    severity: str = Field(..., description="严重程度")
    source: str = Field(..., description="信息来源")


class DrugInteractionResponse(BaseModel):
    """药物相互作用响应"""
    success: bool = Field(..., description="请求是否成功")
    drug1: Optional[str] = Field(None, description="第一种药物")
    drug2: Optional[str] = Field(None, description="第二种药物")
    found_interactions: bool = Field(default=False, description="是否发现相互作用")
    interactions: List[DrugInteraction] = Field(default_factory=list, description="相互作用列表")
    recommendation: Optional[str] = Field(None, description="建议")
    error: Optional[str] = Field(None, description="错误信息")
    disclaimer: str = Field(
        default="此信息仅供教育用途，不能替代专业医疗建议。请与您的医疗保健提供者讨论任何药物相互作用。",
        description="医疗免责声明"
    )


class DrugInfo(BaseModel):
    """药物基本信息"""
    drug_name: str = Field(..., description="药物名称")
    rxcui: Optional[str] = Field(None, description="RxNorm唯一标识符")
    generic_name: Optional[str] = Field(None, description="通用名")
    brand_names: List[str] = Field(default_factory=list, description="品牌名列表")
    manufacturer: Optional[str] = Field(None, description="制造商")
    drug_class: Optional[str] = Field(None, description="药物分类")


class WarningInfo(BaseModel):
    """警告信息"""
    level: SeverityLevel = Field(..., description="严重程度级别")
    title: str = Field(..., description="警告标题")
    description: str = Field(..., description="警告描述")
    action_required: str = Field(..., description="需要采取的行动")
    urgency: str = Field(..., description="紧迫性（立即/今天/常规）")


class MedicalDisclaimer(BaseModel):
    """医疗免责声明"""
    text: str = Field(
        default="""医疗免责声明

本应用提供的信息仅供教育和参考用途。它不旨在替代专业医疗建议、诊断或治疗。

对于任何关于医疗状况或药物的问题，请始终咨询您的医生或其他合格的医疗保健提供者。

本应用不：
✗ 诊断医疗状况
✗ 开处方药
✗ 替代您的医生建议
✗ 提供紧急医疗服务

如遇紧急情况，请立即拨打911。

本应用使用可能出错的人工智能。所有信息应与您的医疗保健提供者核实。""",
        description="完整的医疗免责声明"
    )
    accepted: bool = Field(default=False, description="用户是否已接受免责声明")
