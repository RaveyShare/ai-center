"""Context compaction 逻辑。

当对话上下文接近 LLM token 限制时，将历史消息压缩为摘要。
压缩事件会记录到 Session，Brain 恢复时从 COMPACTION 事件重建上下文。

此模块提供独立的压缩工具函数，Brain.base 中的 _maybe_compact 是主要调用点。
"""

from langchain_core.messages import BaseMessage, SystemMessage


def estimate_tokens(messages: list[BaseMessage]) -> int:
    """粗略估算消息列表的 token 数。

    使用 1 个中文字符 ≈ 1.5 token、1 个英文单词 ≈ 1.3 token 的经验值。
    这里简化为 content 长度 / 3。
    """
    total = 0
    for msg in messages:
        content = getattr(msg, 'content', '') or ''
        total += len(content) // 3
    return total


def build_compaction_prompt(messages: list[BaseMessage]) -> list[BaseMessage]:
    """构建压缩用的 prompt。"""
    return [
        SystemMessage(content=(
            "请将以下对话压缩为关键信息摘要。保留所有重要事实、决策、待办。"
            "不要遗漏任何关键细节。输出纯文本摘要。"
        )),
        *messages
    ]
