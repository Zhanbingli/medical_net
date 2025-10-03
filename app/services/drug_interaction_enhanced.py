"""
增强的药物相互作用服务 - 详细的疗效和副作用分析

功能：
1. 详细的相互作用副作用分析
2. 疗效增强/减弱的评估
3. 分级的严重程度和风险评估
4. 临床意义和管理建议
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from app.services.openfda_service import OpenFDAService
from app.services.rxnorm_service import RxNormService
from app.services.ai_agent_service import AIAgentService


class InteractionSeverity(str, Enum):
    """相互作用严重程度"""
    CONTRAINDICATED = "contraindicated"  # 禁忌 - 绝对不能同时使用
    MAJOR = "major"  # 严重 - 可能危及生命
    MODERATE = "moderate"  # 中度 - 可能需要调整剂量
    MINOR = "minor"  # 轻微 - 通常不需要干预


class InteractionEffect(str, Enum):
    """相互作用对疗效的影响"""
    ENHANCED = "enhanced"  # 疗效增强
    REDUCED = "reduced"  # 疗效减弱
    ALTERED = "altered"  # 疗效改变
    NEUTRAL = "neutral"  # 无明显影响


class DrugInteractionEnhancedService:
    """增强的药物相互作用服务"""

    def __init__(self):
        self.openfda_service = OpenFDAService()
        self.rxnorm_service = RxNormService()
        self.ai_agent = AIAgentService()

    async def analyze_interaction_detailed(
        self,
        drug1: str,
        drug2: str
    ) -> Dict[str, Any]:
        """
        详细分析两种药物的相互作用，包括疗效和副作用

        Args:
            drug1: 第一种药物名称
            drug2: 第二种药物名称

        Returns:
            详细的相互作用分析
        """
        # 1. 获取两种药物的完整信息
        drug1_context = await self.openfda_service.get_drug_context(drug1)
        drug2_context = await self.openfda_service.get_drug_context(drug2)

        # 2. 获取FDA标签中的相互作用信息
        drug1_interactions = await self.openfda_service.check_drug_interactions_fda(drug1)
        drug2_interactions = await self.openfda_service.check_drug_interactions_fda(drug2)

        # 3. 提取单药的副作用（基线）
        drug1_adverse_effects = await self._extract_adverse_effects(drug1)
        drug2_adverse_effects = await self._extract_adverse_effects(drug2)

        # 4. 分析相互作用
        interaction_analysis = await self._analyze_interaction(
            drug1, drug2,
            drug1_interactions, drug2_interactions,
            drug1_context, drug2_context
        )

        # 5. 使用AI生成详细的副作用和疗效分析
        ai_analysis = await self._generate_ai_analysis(
            drug1, drug2,
            drug1_context, drug2_context,
            interaction_analysis
        )

        return {
            "drug1": {
                "name": drug1,
                "baseline_adverse_effects": drug1_adverse_effects,
                "indications": drug1_context.get("indications", "无数据")
            },
            "drug2": {
                "name": drug2,
                "baseline_adverse_effects": drug2_adverse_effects,
                "indications": drug2_context.get("indications", "无数据")
            },
            "interaction": {
                "found": interaction_analysis["found"],
                "severity": interaction_analysis["severity"],
                "description": interaction_analysis["description"],
                "mechanism": interaction_analysis.get("mechanism", "未知"),

                # 新增：副作用分析
                "combined_adverse_effects": interaction_analysis.get("combined_adverse_effects", []),
                "new_adverse_effects": interaction_analysis.get("new_adverse_effects", []),
                "increased_risk_effects": interaction_analysis.get("increased_risk_effects", []),

                # 新增：疗效分析
                "efficacy_impact": {
                    "drug1_efficacy": interaction_analysis.get("drug1_efficacy_impact", InteractionEffect.NEUTRAL),
                    "drug2_efficacy": interaction_analysis.get("drug2_efficacy_impact", InteractionEffect.NEUTRAL),
                    "description": interaction_analysis.get("efficacy_description", "")
                },

                # 临床意义
                "clinical_significance": interaction_analysis.get("clinical_significance", ""),
                "management_recommendations": interaction_analysis.get("management", [])
            },
            "ai_analysis": ai_analysis,
            "disclaimer": "此分析基于FDA公开数据和AI生成，仅供参考。实际用药请咨询医疗专业人员。"
        }

    async def _extract_adverse_effects(self, drug_name: str) -> Dict[str, Any]:
        """
        提取单个药物的副作用信息

        Args:
            drug_name: 药物名称

        Returns:
            分类的副作用信息
        """
        context = await self.openfda_service.get_drug_context(drug_name)

        if not context.get("found"):
            return {
                "common": [],
                "serious": [],
                "warnings": []
            }

        # 从FDA标签获取详细副作用
        label = await self.openfda_service.get_drug_label(drug_name)

        if not label:
            return {
                "common": [],
                "serious": [],
                "warnings": []
            }

        # 提取不同类型的副作用
        adverse_reactions = label.get("adverse_reactions", [])
        warnings = label.get("warnings", [])
        boxed_warning = label.get("boxed_warning", [])

        return {
            "common": adverse_reactions if isinstance(adverse_reactions, list) else [adverse_reactions],
            "serious": boxed_warning if isinstance(boxed_warning, list) else [boxed_warning],
            "warnings": warnings if isinstance(warnings, list) else [warnings]
        }

    async def _analyze_interaction(
        self,
        drug1: str,
        drug2: str,
        drug1_interactions: List[str],
        drug2_interactions: List[str],
        drug1_context: Dict[str, Any],
        drug2_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析相互作用的详细信息

        Args:
            drug1: 第一种药物
            drug2: 第二种药物
            drug1_interactions: drug1的相互作用列表
            drug2_interactions: drug2的相互作用列表
            drug1_context: drug1的上下文
            drug2_context: drug2的上下文

        Returns:
            相互作用分析结果
        """
        # 检查是否存在相互作用
        found_interaction = False
        interaction_text = ""

        # 在drug1的相互作用中查找drug2
        for interaction in drug1_interactions:
            if drug2.lower() in interaction.lower():
                found_interaction = True
                interaction_text = interaction
                break

        # 在drug2的相互作用中查找drug1
        if not found_interaction:
            for interaction in drug2_interactions:
                if drug1.lower() in interaction.lower():
                    found_interaction = True
                    interaction_text = interaction
                    break

        if not found_interaction:
            return {
                "found": False,
                "severity": InteractionSeverity.MINOR,
                "description": "FDA标签中未发现明确的相互作用记录。这不代表绝对安全，建议咨询医生。",
                "combined_adverse_effects": [],
                "new_adverse_effects": [],
                "increased_risk_effects": [],
                "clinical_significance": "未知 - 需要医疗专业人员评估"
            }

        # 评估严重程度（基于关键词）
        severity = self._assess_severity(interaction_text)

        # 分析可能的新副作用和增加的风险
        combined_effects = self._analyze_combined_effects(
            interaction_text,
            drug1_context,
            drug2_context
        )

        # 分析对疗效的影响
        efficacy_impact = self._analyze_efficacy_impact(interaction_text)

        return {
            "found": True,
            "severity": severity,
            "description": interaction_text[:1000],  # 限制长度
            "mechanism": self._extract_mechanism(interaction_text),
            "combined_adverse_effects": combined_effects["combined"],
            "new_adverse_effects": combined_effects["new"],
            "increased_risk_effects": combined_effects["increased"],
            "drug1_efficacy_impact": efficacy_impact["drug1"],
            "drug2_efficacy_impact": efficacy_impact["drug2"],
            "efficacy_description": efficacy_impact["description"],
            "clinical_significance": self._assess_clinical_significance(severity, interaction_text),
            "management": self._generate_management_recommendations(severity, interaction_text)
        }

    def _assess_severity(self, interaction_text: str) -> InteractionSeverity:
        """
        评估相互作用的严重程度

        Args:
            interaction_text: 相互作用描述文本

        Returns:
            严重程度级别
        """
        text_lower = interaction_text.lower()

        # 禁忌关键词
        if any(keyword in text_lower for keyword in [
            "contraindicated", "do not use", "should not be used",
            "禁忌", "不得使用", "严禁"
        ]):
            return InteractionSeverity.CONTRAINDICATED

        # 严重关键词
        if any(keyword in text_lower for keyword in [
            "life-threatening", "fatal", "death", "serious",
            "severe", "major", "危及生命", "致命", "严重"
        ]):
            return InteractionSeverity.MAJOR

        # 中度关键词
        if any(keyword in text_lower for keyword in [
            "moderate", "significant", "caution", "monitor",
            "中度", "显著", "谨慎", "监测"
        ]):
            return InteractionSeverity.MODERATE

        return InteractionSeverity.MINOR

    def _analyze_combined_effects(
        self,
        interaction_text: str,
        drug1_context: Dict[str, Any],
        drug2_context: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        分析联合用药的副作用

        Args:
            interaction_text: 相互作用描述
            drug1_context: drug1上下文
            drug2_context: drug2上下文

        Returns:
            分类的副作用
        """
        combined = []
        new = []
        increased = []

        text_lower = interaction_text.lower()

        # 常见的相互作用副作用模式
        if "bleeding" in text_lower or "hemorrhage" in text_lower or "出血" in text_lower:
            increased.append("出血风险增加")

        if "serotonin syndrome" in text_lower or "5-羟色胺综合征" in text_lower:
            new.append("5-羟色胺综合征（可能致命）")

        if "qt" in text_lower or "cardiac" in text_lower or "心脏" in text_lower:
            increased.append("心脏节律异常风险")

        if "hypotension" in text_lower or "低血压" in text_lower:
            increased.append("低血压风险")

        if "sedation" in text_lower or "cns depression" in text_lower or "镇静" in text_lower:
            increased.append("中枢神经系统抑制（嗜睡、意识模糊）")

        if "toxicity" in text_lower or "毒性" in text_lower:
            increased.append("药物毒性增加")

        if "renal" in text_lower or "kidney" in text_lower or "肾" in text_lower:
            increased.append("肾功能损害风险")

        if "liver" in text_lower or "hepatic" in text_lower or "肝" in text_lower:
            increased.append("肝功能损害风险")

        return {
            "combined": combined,
            "new": new,
            "increased": increased
        }

    def _analyze_efficacy_impact(self, interaction_text: str) -> Dict[str, Any]:
        """
        分析相互作用对疗效的影响

        Args:
            interaction_text: 相互作用描述

        Returns:
            疗效影响分析
        """
        text_lower = interaction_text.lower()

        drug1_impact = InteractionEffect.NEUTRAL
        drug2_impact = InteractionEffect.NEUTRAL
        description = ""

        # 疗效增强
        if any(keyword in text_lower for keyword in [
            "increased effect", "potentiate", "enhance",
            "增强", "加强", "提高疗效"
        ]):
            drug1_impact = InteractionEffect.ENHANCED
            drug2_impact = InteractionEffect.ENHANCED
            description = "两种药物可能相互增强疗效，但也可能增加副作用风险"

        # 疗效减弱
        elif any(keyword in text_lower for keyword in [
            "decreased effect", "reduce", "diminish", "antagonize",
            "减弱", "降低", "拮抗"
        ]):
            drug1_impact = InteractionEffect.REDUCED
            drug2_impact = InteractionEffect.REDUCED
            description = "两种药物可能相互减弱疗效，可能需要调整剂量"

        # 疗效改变
        elif any(keyword in text_lower for keyword in [
            "altered", "modified", "changed",
            "改变", "修改"
        ]):
            drug1_impact = InteractionEffect.ALTERED
            drug2_impact = InteractionEffect.ALTERED
            description = "两种药物可能改变彼此的疗效，需要密切监测"

        else:
            description = "目前数据不足以评估对疗效的具体影响"

        return {
            "drug1": drug1_impact,
            "drug2": drug2_impact,
            "description": description
        }

    def _extract_mechanism(self, interaction_text: str) -> str:
        """提取相互作用机制"""
        text_lower = interaction_text.lower()

        mechanisms = []

        if "cyp" in text_lower or "cytochrome" in text_lower:
            mechanisms.append("细胞色素P450酶代谢途径")

        if "absorption" in text_lower or "吸收" in text_lower:
            mechanisms.append("影响药物吸收")

        if "protein binding" in text_lower or "蛋白结合" in text_lower:
            mechanisms.append("血浆蛋白结合竞争")

        if "renal" in text_lower or "肾" in text_lower:
            mechanisms.append("肾脏排泄途径")

        if "pharmacodynamic" in text_lower or "药效学" in text_lower:
            mechanisms.append("药效学相互作用")

        return "; ".join(mechanisms) if mechanisms else "机制未明确说明"

    def _assess_clinical_significance(self, severity: InteractionSeverity, interaction_text: str) -> str:
        """评估临床意义"""
        if severity == InteractionSeverity.CONTRAINDICATED:
            return "🔴 极高临床意义 - 禁忌联合使用，可能危及生命"
        elif severity == InteractionSeverity.MAJOR:
            return "🔴 高临床意义 - 可能导致严重不良后果，需要密切监测或避免联用"
        elif severity == InteractionSeverity.MODERATE:
            return "🟡 中等临床意义 - 可能需要调整剂量或增加监测"
        else:
            return "🟢 低临床意义 - 通常不需要特殊干预，但仍建议告知医生"

    def _generate_management_recommendations(self, severity: InteractionSeverity, interaction_text: str) -> List[str]:
        """生成管理建议"""
        recommendations = []

        if severity == InteractionSeverity.CONTRAINDICATED:
            recommendations.extend([
                "❌ 避免同时使用这两种药物",
                "🏥 立即咨询医生讨论替代方案",
                "⚠️ 如已同时使用，请紧急联系医疗专业人员"
            ])
        elif severity == InteractionSeverity.MAJOR:
            recommendations.extend([
                "⚠️ 仅在医生明确指导下使用",
                "📊 需要密切监测相关副作用",
                "💊 可能需要调整药物剂量",
                "🏥 定期复查相关指标（如血液检查）"
            ])
        elif severity == InteractionSeverity.MODERATE:
            recommendations.extend([
                "👨‍⚕️ 告知医生您正在使用这两种药物",
                "📋 注意监测可能的副作用",
                "⏰ 可能需要调整服药时间间隔"
            ])
        else:
            recommendations.extend([
                "ℹ️ 告知医生或药剂师您的完整用药清单",
                "👀 留意任何异常症状"
            ])

        recommendations.append("📞 如有任何疑问或出现不适，请立即咨询医疗专业人员")

        return recommendations

    async def _generate_ai_analysis(
        self,
        drug1: str,
        drug2: str,
        drug1_context: Dict[str, Any],
        drug2_context: Dict[str, Any],
        interaction_analysis: Dict[str, Any]
    ) -> str:
        """
        使用AI生成详细的副作用和疗效分析

        Args:
            drug1: 药物1
            drug2: 药物2
            drug1_context: 药物1上下文
            drug2_context: 药物2上下文
            interaction_analysis: 相互作用分析

        Returns:
            AI生成的详细分析
        """
        # 构建详细的上下文
        context = f"""
请分析以下两种药物联合使用的情况：

【药物1】: {drug1}
- 适应症: {drug1_context.get('indications', '无数据')[:200]}
- 单药副作用: {drug1_context.get('adverse_reactions', '无数据')[:200]}

【药物2】: {drug2}
- 适应症: {drug2_context.get('indications', '无数据')[:200]}
- 单药副作用: {drug2_context.get('adverse_reactions', '无数据')[:200]}

【相互作用信息】:
- 严重程度: {interaction_analysis.get('severity', '未知')}
- 描述: {interaction_analysis.get('description', '无')[:300]}
- 机制: {interaction_analysis.get('mechanism', '未知')}

请详细分析：
1. 联合用药可能产生哪些新的副作用或增强哪些现有副作用？
2. 对两种药物各自疗效的影响（增强/减弱/无影响）？
3. 具体的临床监测建议？

请以清晰、专业但易懂的方式回答，并提醒这是教育信息，实际用药请咨询医生。
"""

        try:
            ai_response = await self.ai_agent.generate_ai_response(
                context=context,
                user_question="请提供详细的副作用和疗效分析"
            )
            return ai_response
        except Exception as e:
            return f"AI分析暂时不可用: {str(e)}"
