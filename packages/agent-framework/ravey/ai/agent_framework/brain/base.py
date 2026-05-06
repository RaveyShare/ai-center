"""Brain 基类 — 无状态 Agent 循环。

核心生命周期:
    1. wake(session_id) — 从 Session 事件日志恢复 messages
    2. step() — 一步: LLM 推理 → 工具路由 → 记录事件
    3. run() — 循环 step() 直到 LLM 不再调用工具
    4. 崩溃 → 新实例 wake() → 继续（cattle, not pet）

Brain 是无状态的:
    - 不持久化任何东西（Session Store 负责）
    - 不持有 credential（Hand 负责）
    - 崩溃后可以从任意 Session 恢复
"""

from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from ravey.ai.agent_framework.session.store import SessionStore
from ravey.ai.agent_framework.session.events import Event, EventType
from ravey.ai.agent_framework.hands.base import Hand


@dataclass
class BrainConfig:
    agent_name: str
    system_prompt: str
    llm_provider: str = "dashscope"
    llm_model: str = "qwen3-coder-plus"
    max_tool_calls: int = 10
    compaction_threshold: int = 80000      # 估算 token 数超过此值触发压缩


class Brain:
    """无状态 Agent Brain。"""

    def __init__(
        self,
        config: BrainConfig,
        session_store: SessionStore,
        hands: dict[str, Hand],
    ):
        self.config = config
        self.session_store = session_store
        self.hands = hands
        self._llm = None
        self._session_id: str | None = None
        self._messages: list = []

    # ====== 生命周期 ======

    def wake(self, session_id: str) -> None:
        """从 Session 事件日志恢复上下文。"""
        self._session_id = session_id
        events = self.session_store.get_events(session_id)
        self._messages = self._rebuild_messages(events)

        self.session_store.emit_event(session_id, Event(
            event_type=EventType.SYSTEM,
            payload={"action": "brain_wake", "events_replayed": len(events)}
        ))

    def step(self) -> bool:
        """执行一步 Agent 循环。

        Returns:
            True 表示还需要继续（有工具调用），False 表示任务完成
        """
        sid = self._session_id
        llm = self._get_llm()

        # 1. 构建 prompt
        full_messages = [SystemMessage(content=self.config.system_prompt)] + self._messages

        # 2. 调 LLM（绑定工具 schema）
        tools_lc = [h.as_langchain_tool() for h in self.hands.values()]
        llm_with_tools = llm.bind_tools(tools_lc) if tools_lc else llm

        self.session_store.emit_event(sid, Event(
            event_type=EventType.LLM_REQUEST,
            payload={"model": self.config.llm_model, "message_count": len(full_messages)}
        ))

        response: AIMessage = llm_with_tools.invoke(full_messages)

        self.session_store.emit_event(sid, Event(
            event_type=EventType.LLM_RESPONSE,
            payload={
                "content": response.content or "",
                "tool_calls": response.tool_calls or [],
            }
        ))
        self._messages.append(response)

        # 3. 无工具调用 → 完成
        if not response.tool_calls:
            return False

        # 4. 路由到 Hand
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_input = tc["args"]
            tool_call_id = tc["id"]

            self.session_store.emit_event(sid, Event(
                event_type=EventType.TOOL_CALL,
                payload={"name": tool_name, "input": tool_input, "tool_call_id": tool_call_id}
            ))

            hand = self.hands.get(tool_name)
            if hand is None:
                result = f"Error: unknown tool '{tool_name}'"
            else:
                try:
                    result = hand.execute(tool_name, tool_input)
                except Exception as e:
                    result = f"Error: {type(e).__name__}: {e}"
                    self.session_store.emit_event(sid, Event(
                        event_type=EventType.ERROR,
                        payload={"tool": tool_name, "error": result}
                    ))

            self.session_store.emit_event(sid, Event(
                event_type=EventType.TOOL_RESULT,
                payload={"tool_call_id": tool_call_id, "name": tool_name, "result": result}
            ))
            self._messages.append(ToolMessage(content=result, tool_call_id=tool_call_id))

        # 5. 检查 context compaction
        self._maybe_compact()

        return True

    def run(self) -> str:
        """循环执行直到完成。返回最终回复。"""
        calls = 0
        while calls < self.config.max_tool_calls:
            should_continue = self.step()
            if not should_continue:
                break
            calls += 1

        self.session_store.update_status(self._session_id, "completed")

        # 返回最后一条 AI 消息
        for msg in reversed(self._messages):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
        return ""

    # ====== 内部方法 ======

    def _rebuild_messages(self, events: list[Event]) -> list:
        """从事件日志重建 LangChain messages。

        如果遇到 COMPACTION 事件，用压缩摘要替代之前的所有消息。
        """
        messages = []
        for event in events:
            match event.event_type:
                case EventType.COMPACTION:
                    messages = [SystemMessage(content=event.payload["summary"])]
                case EventType.USER_MESSAGE:
                    messages.append(HumanMessage(content=event.payload["content"]))
                case EventType.LLM_RESPONSE:
                    msg = AIMessage(content=event.payload.get("content", ""))
                    if event.payload.get("tool_calls"):
                        msg.tool_calls = event.payload["tool_calls"]
                    messages.append(msg)
                case EventType.TOOL_RESULT:
                    messages.append(ToolMessage(
                        content=event.payload["result"],
                        tool_call_id=event.payload["tool_call_id"]
                    ))
        return messages

    def _maybe_compact(self) -> None:
        """Context 接近上限时压缩。

        关键: 压缩后 Session 仍保留完整事件日志。
        Brain 随时可以从 Session getEvents() 重新加载任意范围。
        """
        estimated_tokens = sum(len(getattr(m, 'content', '') or '') // 3 for m in self._messages)
        if estimated_tokens < self.config.compaction_threshold:
            return

        llm = self._get_llm()
        summary_messages = [
            SystemMessage(content="请将以下对话压缩为关键信息摘要。保留所有重要事实、决策、待办。不要遗漏任何关键细节。"),
            *self._messages
        ]
        summary = llm.invoke(summary_messages)

        self.session_store.emit_event(self._session_id, Event(
            event_type=EventType.COMPACTION,
            payload={
                "summary": summary.content,
                "compacted_count": len(self._messages),
                "estimated_tokens_before": estimated_tokens,
            }
        ))
        self._messages = [SystemMessage(content=summary.content)]

    def _get_llm(self):
        if self._llm is None:
            from ravey.ai.agent_framework.llm import LLMFactory
            factory = LLMFactory(self.config.__dict__)
            self._llm = factory.create(self.config.llm_provider, model=self.config.llm_model)
        return self._llm

    def set_llm(self, llm):
        """注入 LLM 实例（用于测试或自定义场景）。"""
        self._llm = llm
