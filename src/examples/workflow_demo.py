"""LangGraph 工作流使用示例"""
import asyncio
from ai_center.config import Settings
from ai_center.workflow.graph_builder import AlmondWorkflowManager
from ai_center.workflow.state import AlmondState


async def example_classification_workflow():
    """示例：使用工作流进行分类"""
    print("=" * 60)
    print("示例 1：分类工作流")
    print("=" * 60)

    # 初始化配置
    settings = Settings(
        dashscope_api_key="your-api-key",
        llm_provider="qwen",
        llm_model="qwen-plus"
    )

    # 创建工作流管理器
    manager = AlmondWorkflowManager(settings)

    # 准备初始状态
    initial_state: AlmondState = {
        "title": "学习 Python 装饰器",
        "content": "深入理解装饰器的工作原理，包括闭包、@语法糖、带参数的装饰器等",
        "task_id": 12345,
        "user_id": 1001,
        "context": "这是我最近在学习 Python 高级特性时遇到的",
        "messages": [],
        "confidence": 0.0,
        "behavior_count": 0,
        "completion_times": 0,
        "cost_time": 0,
        "workflow_complete": False,
        "current_type": None,
        "current_state": None,
        "classification": None,
        "reasoning": None,
        "recommended_status": None,
        "suggestions": None,
        "should_evolve": None,
        "evolution_reason": None,
        "from_type": None,
        "to_type": None,
        "split_suggestions": None,
        "achievements": None,
        "learnings": None,
        "improvements": None,
        "patterns": None,
        "spawn_almonds": None,
        "model": None,
        "error_message": None,
        "next_step": None,
        "user_behavior": None,
        "created_at": None
    }

    # 运行工作流
    print("\n🚀 启动分类工作流...")
    result = await manager.run_classification(initial_state)

    # 输出结果
    print(f"\n✅ 工作流完成！")
    print(f"📊 分类结果: {result['classification']}")
    print(f"🎯 置信度: {result['confidence']:.2f}")
    print(f"💡 分析理由: {result['reasoning']}")
    print(f"📝 推荐状态: {result['recommended_status']}")
    print(f"⏱️  耗时: {result['cost_time']}ms")

    if result.get('suggestions'):
        print(f"\n💭 AI 建议:")
        for idx, suggestion in enumerate(result['suggestions'], 1):
            print(f"   {idx}. {suggestion}")

    # 查看消息历史
    print(f"\n📜 工作流执行历史:")
    for msg in result.get('messages', []):
        role = "👤 用户" if hasattr(msg, 'type') and msg.type == "human" else "🤖 AI"
        print(f"   {role}: {msg.content[:80]}...")


async def example_streaming_workflow():
    """示例：流式执行工作流"""
    print("\n" + "=" * 60)
    print("示例 2：流式工作流")
    print("=" * 60)

    settings = Settings(
        dashscope_api_key="your-api-key",
        llm_provider="qwen",
        llm_model="qwen-plus"
    )

    manager = AlmondWorkflowManager(settings)

    initial_state: AlmondState = {
        "title": "写项目文档",
        "content": "为新项目编写完整的技术文档，包括架构设计、API 文档、部署指南",
        "task_id": 12346,
        "user_id": 1001,
        "messages": [],
        "confidence": 0.0,
        "behavior_count": 0,
        "completion_times": 0,
        "cost_time": 0,
        "workflow_complete": False,
        "context": None,
        "current_type": None,
        "current_state": None,
        "classification": None,
        "reasoning": None,
        "recommended_status": None,
        "suggestions": None,
        "should_evolve": None,
        "evolution_reason": None,
        "from_type": None,
        "to_type": None,
        "split_suggestions": None,
        "achievements": None,
        "learnings": None,
        "improvements": None,
        "patterns": None,
        "spawn_almonds": None,
        "model": None,
        "error_message": None,
        "next_step": None,
        "user_behavior": None,
        "created_at": None
    }

    print("\n🌊 启动流式工作流...")
    print("💫 实时查看每个节点的执行结果：\n")

    async for event in manager.stream_workflow("classification", initial_state):
        for node_name, node_output in event.items():
            if node_name != "__end__":
                print(f"📍 节点: {node_name}")
                if isinstance(node_output, dict):
                    if node_output.get("classification"):
                        print(f"   分类: {node_output['classification']}")
                    if node_output.get("confidence"):
                        print(f"   置信度: {node_output['confidence']:.2f}")
                    if node_output.get("reasoning"):
                        print(f"   理由: {node_output['reasoning'][:60]}...")
                print()


async def example_evolution_workflow():
    """示例：演化工作流"""
    print("\n" + "=" * 60)
    print("示例 3：演化分析工作流")
    print("=" * 60)

    settings = Settings(
        dashscope_api_key="your-api-key",
        llm_provider="qwen",
        llm_model="qwen-plus"
    )

    manager = AlmondWorkflowManager(settings)

    initial_state: AlmondState = {
        "title": "学习机器学习",
        "content": "系统学习机器学习的理论和实践",
        "task_id": 12347,
        "user_id": 1001,
        "current_state": "action",
        "current_type": "action",
        "user_behavior": "defer",
        "behavior_count": 5,
        "created_at": "2024-12-01",
        "completion_times": 0,
        "messages": [],
        "confidence": 0.0,
        "cost_time": 0,
        "workflow_complete": False,
        "context": None,
        "classification": None,
        "reasoning": None,
        "recommended_status": None,
        "suggestions": None,
        "should_evolve": None,
        "evolution_reason": None,
        "from_type": None,
        "to_type": None,
        "split_suggestions": None,
        "achievements": None,
        "learnings": None,
        "improvements": None,
        "patterns": None,
        "spawn_almonds": None,
        "model": None,
        "error_message": None,
        "next_step": None
    }

    print("\n🔄 启动演化分析...")
    print(f"📌 当前类型: {initial_state['current_type']}")
    print(f"👤 用户行为: {initial_state['user_behavior']} (已发生 {initial_state['behavior_count']} 次)")

    result = await manager.run_evolution(initial_state)

    print(f"\n{'🎯 需要演化！' if result['should_evolve'] else '✅ 保持当前状态'}")

    if result['should_evolve']:
        print(f"📊 演化分析:")
        print(f"   从: {result['from_type']} → 到: {result['to_type']}")
        print(f"   原因: {result['evolution_reason']}")
        print(f"   置信度: {result['confidence']:.2f}")

        if result.get('split_suggestions'):
            print(f"\n💡 拆分建议:")
            for idx, suggestion in enumerate(result['split_suggestions'], 1):
                print(f"   {idx}. {suggestion.get('title', 'N/A')}")
                print(f"      {suggestion.get('content', 'N/A')[:60]}...")


async def example_retrospect_workflow():
    """示例：复盘工作流"""
    print("\n" + "=" * 60)
    print("示例 4：复盘分析工作流")
    print("=" * 60)

    settings = Settings(
        dashscope_api_key="your-api-key",
        llm_provider="qwen",
        llm_model="qwen-plus"
    )

    manager = AlmondWorkflowManager(settings)

    initial_state: AlmondState = {
        "title": "完成项目重构",
        "content": "对旧项目进行全面重构，提升代码质量和性能",
        "task_id": 12348,
        "user_id": 1001,
        "created_at": "2024-11-01",
        "context": '{"duration": "30天", "code_reduction": "20%", "performance_improvement": "40%"}',
        "messages": [],
        "confidence": 0.0,
        "behavior_count": 0,
        "completion_times": 0,
        "cost_time": 0,
        "workflow_complete": False,
        "current_type": None,
        "current_state": None,
        "classification": None,
        "reasoning": None,
        "recommended_status": None,
        "suggestions": None,
        "should_evolve": None,
        "evolution_reason": None,
        "from_type": None,
        "to_type": None,
        "split_suggestions": None,
        "achievements": None,
        "learnings": None,
        "improvements": None,
        "patterns": None,
        "spawn_almonds": None,
        "model": None,
        "error_message": None,
        "next_step": None,
        "user_behavior": None
    }

    print("\n🪞 启动复盘分析...")
    result = await manager.run_retrospect(initial_state)

    print(f"\n✨ 复盘完成！")
    print(f"🎯 置信度: {result['confidence']:.2f}")
    print(f"💭 总体评价: {result['reasoning']}")

    if result.get('achievements'):
        print(f"\n🏆 主要成就:")
        for idx, achievement in enumerate(result['achievements'], 1):
            print(f"   {idx}. {achievement}")

    if result.get('learnings'):
        print(f"\n📚 学习收获:")
        for idx, learning in enumerate(result['learnings'], 1):
            print(f"   {idx}. {learning}")

    if result.get('improvements'):
        print(f"\n🔧 改进建议:")
        for idx, improvement in enumerate(result['improvements'], 1):
            print(f"   {idx}. {improvement}")

    if result.get('spawn_almonds'):
        print(f"\n🌱 建议创建的新杏仁:")
        for idx, almond in enumerate(result['spawn_almonds'], 1):
            print(f"   {idx}. {almond.get('title', 'N/A')}")
            print(f"      类型: {almond.get('type', 'N/A')}")


async def main():
    """运行所有示例"""
    print("\n🌰 杏仁 AI-Center - LangGraph 工作流示例")
    print("基于 LangGraph 0.3.1 和 LangChain 1.0\n")

    try:
        # 示例 1：分类工作流
        await example_classification_workflow()

        # 示例 2：流式工作流
        await example_streaming_workflow()

        # 示例 3：演化工作流
        await example_evolution_workflow()

        # 示例 4：复盘工作流
        await example_retrospect_workflow()

        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        print("💡 提示: 请确保已配置正确的 API Key")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())