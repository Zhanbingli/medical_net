"""
AI Agent快速测试脚本

使用方法:
1. 确保已安装依赖: pip install -r requirements/base.txt
2. 配置.env文件中的API密钥
3. 运行: python test_ai_agent.py
"""

import asyncio
import sys
from app.services.ai_agent_service import AIAgentService
from app.services.rxnorm_service import RxNormService
from app.services.openfda_service import OpenFDAService


async def test_rxnorm():
    """测试RxNorm API"""
    print("\n" + "="*60)
    print("测试1: RxNorm API")
    print("="*60)

    service = RxNormService()

    # 测试药物名称
    test_drugs = ["aspirin", "ibuprofen", "metformin"]

    for drug in test_drugs:
        print(f"\n查询药物: {drug}")
        rxcui = await service.get_rxcui(drug)

        if rxcui:
            print(f"  ✓ RxCUI: {rxcui}")

            # 获取药物属性
            props = await service.get_drug_properties(rxcui)
            if props:
                print(f"  ✓ 通用名: {props.get('name', 'N/A')}")
                print(f"  ✓ 类型: {props.get('tty', 'N/A')}")
        else:
            print(f"  ✗ 未找到药物")


async def test_openfda():
    """测试OpenFDA API"""
    print("\n" + "="*60)
    print("测试2: OpenFDA API")
    print("="*60)

    service = OpenFDAService()

    # 测试药物
    drug = "aspirin"

    print(f"\n查询药物: {drug}")
    context = await service.get_drug_context(drug)

    if context.get("found"):
        print(f"  ✓ 药物名称: {context.get('drug_name')}")
        print(f"  ✓ 制造商: {context.get('manufacturer', 'N/A')}")
        print(f"  ✓ 警告: {context.get('warnings', 'N/A')[:100]}...")
        print(f"  ✓ 适应症: {context.get('indications', 'N/A')[:100]}...")
    else:
        print(f"  ✗ 未找到药物: {context.get('error')}")


async def test_ai_agent():
    """测试AI Agent完整流程"""
    print("\n" + "="*60)
    print("测试3: AI Agent用药咨询")
    print("="*60)

    agent = AIAgentService()

    # 测试用药咨询
    print("\n用药咨询测试:")
    print("-" * 60)

    result = await agent.ask_medication(
        drug_name="aspirin",
        question="What are the common side effects of this medication?"
    )

    if result["success"]:
        print(f"✓ 药物名称: {result['drug_name']}")
        print(f"✓ 问题: {result['question']}")
        print(f"\n✓ AI回答:\n{result['answer']}")
        print(f"\n✓ 免责声明: {result['disclaimer'][:100]}...")
    else:
        print(f"✗ 错误: {result.get('error')}")


async def test_drug_interaction():
    """测试药物相互作用检查"""
    print("\n" + "="*60)
    print("测试4: 药物相互作用检查")
    print("="*60)

    agent = AIAgentService()

    # 测试相互作用
    drug1 = "warfarin"
    drug2 = "aspirin"

    print(f"\n检查相互作用: {drug1} + {drug2}")
    print("-" * 60)

    result = await agent.check_drug_interactions(drug1, drug2)

    print(f"✓ 发现相互作用: {result['found_interactions']}")

    if result['interactions']:
        for interaction in result['interactions']:
            print(f"\n  药物: {interaction['drug']}")
            print(f"  相互作用药物: {interaction['interacts_with']}")
            print(f"  严重程度: {interaction['severity']}")
            print(f"  描述: {interaction['description'][:100]}...")

    print(f"\n✓ 建议: {result['recommendation']}")


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("AI Agent系统测试")
    print("="*60)

    try:
        # 运行测试
        await test_rxnorm()
        await test_openfda()
        await test_ai_agent()
        await test_drug_interaction()

        print("\n" + "="*60)
        print("✓ 所有测试完成！")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())
