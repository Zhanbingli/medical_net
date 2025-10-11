"""AI Agent服务 - 药物相互作用和用药建议的核心AI引擎"""

import openai
from anthropic import Anthropic
from typing import Dict, Any, List, Optional
from app.core.config import get_settings
from app.core.logging import get_logger, log_execution_time
from app.core.exceptions import AIServiceException
from app.services.rxnorm_service import RxNormService
from app.services.openfda_service import OpenFDAService
from app.services.cache_service import get_cache_service, CacheStrategy

settings = get_settings()
logger = get_logger(__name__)


class AIAgentService:
    """药物相互作用AI Agent"""

    # 系统提示词 - 符合FDA CDS非医疗器械标准
    SYSTEM_PROMPT = """你是一个用药信息助手。你的职责是：

1. 基于FDA批准的药品标签提供事实性信息
2. 解释药物相互作用、副作用和使用说明
3. 始终建议用户就医疗决策咨询医疗保健提供者
4. 绝不提供医疗诊断或治疗建议
5. 尽可能引用信息来源（FDA标签、临床指南）

重要约束：
- 你是信息工具，不能替代医疗专业人员
- 提供选项列表而非单一建议
- 不要提供具体的预防/诊断/治疗输出或指令
- 不要支持时间紧迫的决策
- 确保医疗保健专业人员能够独立审查你的建议依据

请记住：你提供的是教育信息，不是医疗建议。"""

    def __init__(self):
        self.rxnorm_service = RxNormService()
        self.openfda_service = OpenFDAService()
        self.cache = get_cache_service()

        # 初始化AI客户端
        if settings.ai_model.startswith("gpt"):
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured")
            openai.api_key = settings.openai_api_key
            self.ai_provider = "openai"
        elif settings.ai_model.startswith("claude"):
            if not settings.anthropic_api_key:
                logger.warning("Anthropic API key not configured")
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
            self.ai_provider = "anthropic"
        else:
            self.ai_provider = "openai"  # 默认使用OpenAI

        logger.info(f"AI Agent initialized with provider: {self.ai_provider}")

    async def validate_drug_input(self, drug_name: str) -> Dict[str, Any]:
        """
        预AI验证 - 验证药物名称的合法性

        Args:
            drug_name: 药物名称

        Returns:
            验证结果字典
        """
        # 清理和消毒输入
        cleaned_name = drug_name.strip()

        if not cleaned_name:
            return {
                "valid": False,
                "error": "药物名称不能为空"
            }

        if len(cleaned_name) > 100:
            return {
                "valid": False,
                "error": "药物名称过长"
            }

        # 通过RxNorm验证药物是否存在
        is_valid = await self.rxnorm_service.validate_drug_name(cleaned_name)

        if not is_valid:
            return {
                "valid": False,
                "error": f"药物 '{cleaned_name}' 在RxNorm数据库中未找到"
            }

        return {
            "valid": True,
            "cleaned_name": cleaned_name
        }

    async def get_drug_context(self, drug_name: str) -> str:
        """
        获取药物的完整上下文信息（从多个数据源）

        Args:
            drug_name: 药物名称

        Returns:
            格式化的上下文字符串
        """
        # 从RxNorm获取标准化信息
        rxnorm_context = await self.rxnorm_service.get_drug_context(drug_name)

        # 从OpenFDA获取官方标签信息
        fda_context = await self.openfda_service.get_drug_context(drug_name)

        # 构建上下文
        context = f"""
药物名称: {drug_name}

=== RxNorm信息 ===
"""

        if rxnorm_context.get("found"):
            context += f"RxCUI: {rxnorm_context.get('rxcui', 'N/A')}\n"
            if rxnorm_context.get("properties"):
                props = rxnorm_context["properties"]
                context += f"通用名: {props.get('name', 'N/A')}\n"
                context += f"药物类型: {props.get('tty', 'N/A')}\n"
        else:
            context += "RxNorm中未找到此药物\n"

        context += "\n=== FDA官方信息 ===\n"

        if fda_context.get("found"):
            context += f"警告信息: {fda_context.get('warnings', '无')}\n\n"
            context += f"适应症: {fda_context.get('indications', '无')}\n\n"
            context += f"不良反应: {fda_context.get('adverse_reactions', '无')}\n\n"
            context += f"制造商: {fda_context.get('manufacturer', '未知')}\n"
        else:
            context += "FDA数据库中未找到此药物的详细信息\n"

        context += "\n请基于上述FDA官方信息提供准确的药物说明。\n"

        return context

    @log_execution_time
    async def generate_ai_response(self, context: str, user_question: str) -> str:
        """
        使用AI生成响应（带缓存）

        Args:
            context: 药物上下文信息
            user_question: 用户问题

        Returns:
            AI生成的响应
        """
        # 生成缓存键
        cache_key = f"ai_response:{hash(context + user_question)}"

        # 尝试从缓存获取
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            logger.info("AI response retrieved from cache")
            return cached_response

        user_message = f"{context}\n\n用户问题: {user_question}"

        try:
            if self.ai_provider == "openai":
                logger.info("Calling OpenAI API", model=settings.ai_model)
                response = openai.chat.completions.create(
                    model=settings.ai_model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=settings.ai_temperature,
                    max_tokens=settings.ai_max_tokens,
                )
                ai_response = response.choices[0].message.content

            elif self.ai_provider == "anthropic":
                logger.info("Calling Anthropic API", model=settings.ai_model)
                response = self.anthropic_client.messages.create(
                    model=settings.ai_model,
                    max_tokens=settings.ai_max_tokens,
                    system=self.SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": user_message}
                    ],
                    temperature=settings.ai_temperature
                )
                ai_response = response.content[0].text

            else:
                logger.error("AI provider not configured")
                raise AIServiceException("unknown", "AI服务未配置")

            # 缓存响应
            await self.cache.set(cache_key, ai_response, CacheStrategy.AI_RESPONSE_TTL)

            logger.info("AI response generated successfully")
            return ai_response

        except openai.OpenAIError as e:
            logger.error("OpenAI API error", error=str(e), error_type=type(e).__name__)
            raise AIServiceException("openai", str(e))

        except Exception as e:
            logger.error("AI generation error", error=str(e), error_type=type(e).__name__)
            raise AIServiceException(self.ai_provider, str(e))

    async def check_drug_interactions(
        self,
        drug1: str,
        drug2: str
    ) -> Dict[str, Any]:
        """
        后AI验证 - 检查两种药物之间的相互作用

        Args:
            drug1: 第一种药物名称
            drug2: 第二种药物名称

        Returns:
            相互作用信息
        """
        # 从FDA获取相互作用信息
        interactions1 = await self.openfda_service.check_drug_interactions_fda(drug1)
        interactions2 = await self.openfda_service.check_drug_interactions_fda(drug2)

        # 简单的文本匹配检查
        potential_interactions = []

        for interaction in interactions1:
            if drug2.lower() in interaction.lower():
                potential_interactions.append({
                    "drug": drug1,
                    "interacts_with": drug2,
                    "description": interaction,
                    "severity": "中度",  # 默认严重程度
                    "source": "FDA Label"
                })

        for interaction in interactions2:
            if drug1.lower() in interaction.lower():
                potential_interactions.append({
                    "drug": drug2,
                    "interacts_with": drug1,
                    "description": interaction,
                    "severity": "中度",
                    "source": "FDA Label"
                })

        return {
            "found_interactions": len(potential_interactions) > 0,
            "interactions": potential_interactions,
            "recommendation": "请与您的医疗保健提供者讨论这些药物的联合使用。" if potential_interactions else "未在FDA标签中发现明确的相互作用，但仍建议咨询医生。"
        }

    async def ask_medication(
        self,
        drug_name: str,
        question: str
    ) -> Dict[str, Any]:
        """
        用药咨询的完整流程（预AI验证 → AI生成 → 后AI验证）

        Args:
            drug_name: 药物名称
            question: 用户问题

        Returns:
            完整的响应字典
        """
        # 第1层：预AI验证
        validation = await self.validate_drug_input(drug_name)

        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "disclaimer": "此信息仅供教育用途，不能替代专业医疗建议"
            }

        # 第2层：获取上下文并生成AI响应
        context = await self.get_drug_context(validation["cleaned_name"])
        ai_answer = await self.generate_ai_response(context, question)

        # 第3层：后AI验证和安全检查
        # （这里可以添加更多验证逻辑）

        return {
            "success": True,
            "drug_name": validation["cleaned_name"],
            "question": question,
            "answer": ai_answer,
            "disclaimer": "此信息仅供教育用途，不能替代专业医疗建议。对于任何关于医疗状况或药物的问题，请始终咨询您的医生或其他合格的医疗保健提供者。"
        }
