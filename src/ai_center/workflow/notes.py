"""LangGraph 工作流节点实现"""
import json
import time
from typing import Any

from langchain_core.messages import HumanMessage, AIMessage

from ..config import Settings
from ..llm.base import BaseLLM
from ..llm.factory import LLMFactory
from ..llm.prompts import classification, evolution, retrospect
from .state import AlmondState


class AlmondWorkflowNodes:
    """杏仁工作流节点集合"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._llm: BaseLLM | None = None

    @property
    def llm(self) -> BaseLLM:
        """懒加载 LLM"""
        if self._llm is None:
            self._llm = LLMFactory.get_default(self.settings)
        return self._llm

    async def understand_node(self, state: AlmondState) -> dict[str, Any]:
        """理解节点：初步理解杏仁内容

        这是工作流的第一步，快速判断杏仁的基本属性
        """
        start_time = time.time()

        try:
            # 构建快速分类提示词
            system_prompt = classification.QUICK_CLASSIFICATION_SYSTEM_PROMPT
            user_prompt = classification.build_quick_classification_prompt(
                title=state["title"],
                content=state["content"]
            )

            # 调用 LLM
            response = await self.llm.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt
            )

            result = json.loads(response.content)

            # 更新消息历史
            messages = state.get("messages", [])
            messages.extend([
                HumanMessage(content=f"理解这颗杏仁：{state['title']}"),
                AIMessage(content=f"初步判断为：{result['classification']}")
            ])

            cost_time = int((time.time() - start_time) * 1000)

            # 根据置信度决定下一步
            confidence = float(result["confidence"])
            if confidence < self.settings.classification_confidence_threshold:
                next_step = "needs_more_info"
            else:
                next_step = "classify"

            return {
                "current_type": result["classification"],
                "confidence": confidence,
                "reasoning": result["reasoning"],
                "messages": messages,
                "cost_time": cost_time,
                "next_step": next_step
            }

        except Exception as e:
            return {
                "error_message": str(e),
                "next_step": "error",
                "workflow_complete": True
            }

    async def classify_node(self, state: AlmondState) -> dict[str, Any]:
        """分类节点：详细分类分析"""
        start_time = time.time()

        try:
            system_prompt = classification.CLASSIFICATION_SYSTEM_PROMPT
            user_prompt = classification.build_classification_prompt(
                title=state["title"],
                content=state["content"],
                context=state.get("context", "")
            )

            response = await self.llm.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt
            )

            result = json.loads(response.content)

            messages = state.get("messages", [])
            messages.extend([
                HumanMessage(content="请进行详细的分类分析"),
                AIMessage(content=f"分类结果：{result['classification']}，置信度：{result['confidence']}")
            ])

            cost_time = state.get("cost_time", 0) + int((time.time() - start_time) * 1000)

            return {
                "classification": result["classification"],
                "confidence": float(result["confidence"]),
                "reasoning": result["reasoning"],
                "recommended_status": result.get("recommendedStatus", result["classification"]),
                "suggestions": result.get("suggestions"),
                "messages": messages,
                "cost_time": cost_time,
                "next_step": "complete",
                "workflow_complete": True
            }

        except Exception as e:
            return {
                "error_message": str(e),
                "next_step": "error",
                "workflow_complete": True
            }

    async def evolution_analyze_node(self, state: AlmondState) -> dict[str, Any]:
        """演化分析节点：判断是否需要演化"""
        start_time = time.time()

        try:
            system_prompt = evolution.EVOLUTION_SYSTEM_PROMPT
            user_prompt = evolution.build_evolution_prompt(
                title=state["title"],
                content=state["content"],
                current_state=state.get("current_state", ""),
                current_type=state.get("current_type", ""),
                user_behavior=state.get("user_behavior", ""),
                behavior_count=state.get("behavior_count", 0),
                created_at=state.get("created_at", ""),
                completion_times=state.get("completion_times", 0)
            )

            response = await self.llm.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt
            )

            result = json.loads(response.content)

            messages = state.get("messages", [])
            messages.extend([
                HumanMessage(content=f"分析演化需求，用户行为：{state.get('user_behavior')}"),
                AIMessage(content=f"演化分析：{'需要演化' if result.get('shouldEvolve') else '保持当前状态'}")
            ])

            cost_time = state.get("cost_time", 0) + int((time.time() - start_time) * 1000)

            return {
                "should_evolve": result.get("shouldEvolve", False),
                "classification": result["classification"],
                "confidence": float(result["confidence"]),
                "reasoning": result["reasoning"],
                "evolution_reason": result.get("evolutionReason", ""),
                "from_type": result.get("fromType", state.get("current_type")),
                "to_type": result.get("toType", result["classification"]),
                "recommended_status": result.get("recommendedStatus"),
                "split_suggestions": result.get("splitSuggestions"),
                "suggestions": result.get("suggestions"),
                "messages": messages,
                "cost_time": cost_time,
                "next_step": "complete",
                "workflow_complete": True
            }

        except Exception as e:
            return {
                "error_message": str(e),
                "next_step": "error",
                "workflow_complete": True
            }

    async def retrospect_node(self, state: AlmondState) -> dict[str, Any]:
        """复盘节点：复盘总结"""
        start_time = time.time()

        try:
            system_prompt = retrospect.RETROSPECT_SYSTEM_PROMPT
            user_prompt = retrospect.build_retrospect_prompt(
                title=state["title"],
                content=state["content"],
                completed_at=state.get("created_at", ""),  # 这里应该传入完成时间
                created_at=state.get("created_at", ""),
                completion_data=state.get("context", "")
            )

            response = await self.llm.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt
            )

            result = json.loads(response.content)

            messages = state.get("messages", [])
            messages.extend([
                HumanMessage(content="请帮我复盘这颗杏仁"),
                AIMessage(
                    content=f"复盘完成：{len(result.get('achievements', []))} 项成就，{len(result.get('learnings', []))} 条收获")
            ])

            cost_time = state.get("cost_time", 0) + int((time.time() - start_time) * 1000)

            return {
                "classification": "completed",
                "confidence": float(result["confidence"]),
                "reasoning": result["reasoning"],
                "recommended_status": "archived",
                "achievements": result.get("achievements", []),
                "learnings": result.get("learnings", []),
                "improvements": result.get("improvements", []),
                "patterns": result.get("patterns"),
                "spawn_almonds": result.get("spawnAlmonds"),
                "suggestions": result.get("suggestions"),
                "messages": messages,
                "cost_time": cost_time,
                "next_step": "complete",
                "workflow_complete": True
            }

        except Exception as e:
            return {
                "error_message": str(e),
                "next_step": "error",
                "workflow_complete": True
            }

    async def needs_more_info_node(self, state: AlmondState) -> dict[str, Any]:
        """需要更多信息节点：置信度低时的处理"""
        messages = state.get("messages", [])
        messages.append(
            AIMessage(content="我对这颗杏仁的理解还不够清晰，建议先保持观察，或者补充更多信息")
        )

        return {
            "classification": "unclear",
            "confidence": state.get("confidence", 0.5),
            "reasoning": "信息不足，无法明确分类",
            "recommended_status": "new",
            "suggestions": [
                "补充更多详细信息",
                "观察用户后续行为",
                "暂时保持为新杏仁状态"
            ],
            "messages": messages,
            "next_step": "complete",
            "workflow_complete": True
        }

    async def error_node(self, state: AlmondState) -> dict[str, Any]:
        """错误处理节点"""
        return {
            "classification": "unclear",
            "confidence": 0.0,
            "reasoning": "分析过程出错",
            "recommended_status": "new",
            "workflow_complete": True
        }