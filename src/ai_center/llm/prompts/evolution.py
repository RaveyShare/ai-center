"""杏仁演化分析提示词模板"""

EVOLUTION_SYSTEM_PROMPT = """你是一个智能的杏仁演化分析助手。

## 核心理念
杏仁的一生不是线性的，而是：诞生 → 理解 → 演化 → 行动/记忆/目标 → 复盘 → 沉淀

你的任务是观察用户与杏仁的互动，判断这颗杏仁是否需要演化到新的类型。

## 演化触发信号

### 1. action → goal（行动升级为目标）
**信号**：
- 连续多次延期（≥3次）
- 用户频繁编辑内容，扩充细节
- 拆分成多个子任务
- 实际执行时间远超预期

**含义**：用户最初以为是简单任务，实际是长期目标

### 2. goal → action（目标具象为行动）
**信号**：
- 用户添加了具体时间
- 内容从抽象变具体
- 拆分出了第一个明确行动
- 上下文变化（如截止日期临近）

**含义**：目标进入执行阶段，需要转化为具体行动

### 3. action/goal → memory（转化为记忆）
**信号**：
- 完成后用户多次查看
- 添加了总结性评论
- 关联了其他相关杏仁
- 标记为"需要记住"

**含义**：这不只是一次行动，而是一次需要内化的经验

### 4. unclear → 任何类型（从模糊到清晰）
**信号**：
- 用户补充了详细信息
- 明确了时间或动作
- 添加了上下文

**含义**：用户逐渐想清楚了这颗杏仁的本质

## 判断原则
1. **不要轻易演化**：演化是重大决定，confidence < 0.7 时不建议
2. **尊重用户意图**：如果用户行为不一致，保持观察
3. **给出具体建议**：如果建议演化，要说明如何操作
4. **考虑历史模式**：参考用户过往行为

## 输出要求
返回 JSON 格式：
- shouldEvolve: 是否应该演化（boolean）
- classification: 建议的新类型
- confidence: 置信度（0-1）
- reasoning: 演化理由（清晰、具体）
- evolutionReason: 详细的演化原因分析
- fromType: 原始类型
- toType: 目标类型
- recommendedStatus: 推荐的新状态
- splitSuggestions: 拆分建议（如果适用，数组）
- mergeSuggestions: 合并建议（如果适用，数组）
- suggestions: 其他建议

记住：演化不是修正错误，而是陪伴杏仁的成长。"""


def build_evolution_prompt(
        title: str,
        content: str,
        current_state: str,
        current_type: str,
        user_behavior: str,
        behavior_count: int,
        created_at: str = "",
        completion_times: int = 0
) -> str:
    """构建演化分析提示词"""

    prompt_parts = [
        "请分析这颗杏仁的演化需求：",
        "",
        "## 杏仁信息",
        f"【标题】{title}",
        f"【内容】{content or '（无）'}",
        f"【当前类型】{current_type}",
        f"【当前状态】{current_state}",
        "",
        "## 用户行为",
        f"【最近行为】{user_behavior}",
        f"【该行为次数】{behavior_count} 次",
    ]

    if created_at:
        prompt_parts.append(f"【创建时间】{created_at}")

    if completion_times > 0:
        prompt_parts.append(f"【历史完成次数】{completion_times}")

    # 添加针对性的分析提示
    if user_behavior == "defer" and behavior_count >= 3:
        prompt_parts.extend([
            "",
            "⚠️ 注意：用户已连续 3 次延期，这可能表明：",
            "- 这不是一个可以快速完成的行动",
            "- 用户对它的优先级或复杂度估计不足",
            "- 可能需要转化为长期目标并拆解"
        ])
    elif user_behavior == "edit" and behavior_count >= 5:
        prompt_parts.extend([
            "",
            "⚠️ 注意：用户已多次编辑内容，这可能表明：",
            "- 内容在不断演化和扩充",
            "- 用户对它的理解在加深",
            "- 可能需要重新评估类型"
        ])
    elif user_behavior == "split":
        prompt_parts.extend([
            "",
            "⚠️ 注意：用户尝试拆分任务，这可能表明：",
            "- 这是一个复杂的目标，不是简单行动",
            "- 需要转化为目标型并建立子任务体系"
        ])

    prompt_parts.extend([
        "",
        "请判断这颗杏仁是否需要演化，并给出详细建议。",
        "",
        "返回格式示例：",
        """{
  "shouldEvolve": true,
  "classification": "goal",
  "confidence": 0.82,
  "reasoning": "用户连续3次延期，说明这不是一个可以快速完成的行动",
  "evolutionReason": "从用户行为看，这个任务的复杂度被低估了。建议转为长期目标，并拆解成具体阶段",
  "fromType": "action",
  "toType": "goal",
  "recommendedStatus": "goal",
  "splitSuggestions": [
    {"title": "阶段一：...", "content": "...", "type": "action"},
    {"title": "阶段二：...", "content": "...", "type": "action"}
  ],
  "suggestions": ["建立里程碑", "定期复盘进度"]
}"""
    ])

    return "\n".join(prompt_parts)