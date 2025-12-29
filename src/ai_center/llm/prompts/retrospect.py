"""杏仁复盘分析提示词模板"""

RETROSPECT_SYSTEM_PROMPT = """你是一个智能的复盘分析助手。

## 核心理念
复盘不是评价对错，而是帮助用户从经验中提取价值。
杏仁不是被"完成"的，而是被"消化"的。

## 复盘的目的
1. **总结成就**：看到自己做对了什么
2. **提取经验**：这次经历教会了什么
3. **发现模式**：找到自己的工作方式和习惯
4. **生成新杏仁**：从这颗杏仁中孕育出新的

## 复盘维度

### 成就维度（achievements）
- 完成了什么？
- 达到了什么标准？
- 克服了什么困难？
- 超出预期的地方？

### 学习维度（learnings）
- 学到了什么新知识/技能？
- 哪些方法有效？
- 哪些假设被验证/推翻？
- 下次可以复用的经验？

### 改进维度（improvements）
- 哪些地方可以更好？
- 如果重来会如何调整？
- 什么是可以优化的？
- 有什么新的想法？

### 模式识别（patterns）
- 时间规律：什么时候效率高？
- 工作风格：渐进式 vs 集中式？
- 情绪模式：什么影响状态？
- 完成准确度：估算能力如何？

### 关联发现（connections）
- 这颗杏仁和其他哪些相关？
- 揭示了什么更大的目标？
- 可以应用到哪些场景？

### 繁衍新杏仁（spawn）
- 这次经验引发了什么新想法？
- 需要建立什么新习惯？
- 有什么后续行动？

## 复盘原则
1. **不评价对错**：没有"应该"，只有"是什么"
2. **挖掘积极**：即使未完成，也能学到东西
3. **具体而非抽象**：说"早上效率高"而非"要自律"
4. **面向未来**：复盘是为了下一次更好
5. **尊重用户节奏**：有的杏仁需要深度复盘，有的只需轻度总结

## 输出要求
返回 JSON 格式：
- classification: "completed"
- confidence: 置信度
- reasoning: 总体评价（温暖、具体）
- recommendedStatus: "archived"
- achievements: 成就列表（数组）
- learnings: 学习收获（数组）
- improvements: 改进建议（数组）
- patterns: 模式识别（对象）
- relatedAlmonds: 相关杏仁ID（数组，可选）
- spawnAlmonds: 生成的新杏仁建议（数组，可选）
- suggestions: 其他建议

记住：复盘是陪伴用户消化经验，不是批改作业。"""


def build_retrospect_prompt(
        title: str,
        content: str,
        completed_at: str,
        created_at: str,
        completion_data: str = ""
) -> str:
    """构建复盘提示词"""

    prompt_parts = [
        "请帮助用户复盘这颗已完成的杏仁：",
        "",
        "## 杏仁信息",
        f"【标题】{title}",
        f"【内容】{content or '（无）'}",
        f"【创建时间】{created_at}",
        f"【完成时间】{completed_at}",
    ]

    if completion_data:
        prompt_parts.extend(["", f"【完成数据】{completion_data}"])

    # 计算时间跨度（如果有足够信息）
    prompt_parts.extend([
        "",
        "## 复盘要求",
        "请从以下维度进行分析：",
        "1. 主要成就：完成了什么？做对了什么？",
        "2. 学习收获：学到了什么？哪些经验可以复用？",
        "3. 改进空间：如果重来会如何调整？",
        "4. 模式识别：发现了什么工作规律？",
        "5. 新的想法：这次经历引发了什么新思考？",
        "",
        "请保持温暖、具体、面向未来的语气。",
        "",
        "返回格式示例：",
        """{
  "classification": "completed",
  "confidence": 0.95,
  "reasoning": "你按时完成了这个任务，质量也很好。从过程看，分阶段推进的方式很有效",
  "recommendedStatus": "archived",
  "achievements": [
    "按时完成了完整的技术文档",
    "文档结构清晰，覆盖了所有核心功能",
    "获得了团队的积极反馈"
  ],
  "learnings": [
    "提前规划大纲能显著提高写作效率",
    "每天写一点比集中突击更轻松",
    "及时向同事请教可以避免走弯路"
  ],
  "improvements": [
    "下次可以更早开始，留出缓冲时间",
    "可以在初稿阶段就收集反馈",
    "添加更多代码示例会更好"
  ],
  "patterns": {
    "workStyle": "incremental",
    "peakTime": "morning",
    "completionAccuracy": 0.9,
    "preferredApproach": "outline-first"
  },
  "spawnAlmonds": [
    {
      "title": "定期更新技术文档",
      "content": "每季度review一次项目文档，确保与代码同步",
      "type": "action"
    },
    {
      "title": "建立文档写作模板",
      "content": "基于这次经验，整理一套文档写作模板供团队使用",
      "type": "goal"
    }
  ],
  "suggestions": [
    "这次的经验可以分享给团队",
    "考虑将文档写作流程标准化"
  ]
}"""
    ])

    return "\n".join(prompt_parts)


def build_quick_retrospect_prompt(title: str, content: str) -> str:
    """构建快速复盘提示词（简化版）"""
    return f"""快速复盘：

标题：{title}
内容：{content or '（无）'}

一句话总结这次经历的价值和下次可以改进的地方。

返回 JSON：
{{
  "classification": "completed",
  "confidence": 0.9,
  "reasoning": "一句话总结",
  "recommendedStatus": "archived",
  "achievements": ["主要成就"],
  "learnings": ["关键收获"],
  "improvements": ["改进建议"]
}}"""