"""杏仁核心分析器"""
import json
import time
from typing import Optional

from ..config import Settings
from ..llm.base import BaseLLM
from ..llm.factory import LLMFactory
from ..llm.prompts import classification, evolution, retrospect, enrichment, understanding
from ..models.enums import AnalysisType
from ..models.responses import (
    ClassificationResult,
    EvolutionResult,
    RetrospectResult,
    UnderstandingResult,
    UnderstandingCore
)


class AlmondAnalyzer:
    """杏仁分析器 - 核心业务逻辑"""
    
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm: Optional[BaseLLM] = None
    
    def _get_llm(self, model: Optional[str] = None) -> BaseLLM:
        """获取 LLM 实例（懒加载）"""
        if self.llm is None or model:
            self.llm = LLMFactory.create(
                provider=self.settings.llm_provider,
                settings=self.settings,
                model=model
            )
        return self.llm
    
    async def classify(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None,
        text: Optional[str] = None,
        context: str = "",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ClassificationResult:
        """分类分析
        
        Args:
            title: 杏仁标题
            content: 杏仁内容
            context: 额外上下文
            model: 指定模型
            temperature: 温度参数
            max_tokens: 最大 token
            
        Returns:
            分类结果
        """
        start_time = time.time()
        
        try:
            source_text = (text or content or title or "").strip()
            resolved_title = (title or "").strip()
            resolved_content = (content or "").strip()

            llm = self._get_llm(model)

            if (not resolved_title) or (not resolved_content):
                enrich_response = await llm.generate_structured(
                    prompt=enrichment.build_enrich_title_content_prompt(source_text),
                    system_prompt=enrichment.ENRICH_TITLE_CONTENT_SYSTEM_PROMPT,
                    temperature=0.2,
                    max_tokens=300
                )
                enrich_dict = json.loads(enrich_response.content)
                if not resolved_title:
                    resolved_title = str(enrich_dict.get("title", "")).strip() or source_text[:16]
                if not resolved_content:
                    resolved_content = str(enrich_dict.get("content", "")).strip() or source_text
            
            # 构建提示词
            system_prompt = classification.CLASSIFICATION_SYSTEM_PROMPT
            user_prompt = classification.build_classification_prompt(
                title=resolved_title,
                content=resolved_content,
                context=context
            )
            
            # 调用 LLM
            response = await llm.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 解析响应
            result_dict = json.loads(response.content)
            
            # 构建返回结果
            cost_time = int((time.time() - start_time) * 1000)
            
            return ClassificationResult(
                success=True,
                classification=result_dict.get("classification", "unclear"),
                confidence=float(result_dict.get("confidence", 0.5)),
                reasoning=result_dict.get("reasoning", ""),
                recommended_status=result_dict.get("recommendedStatus", "new"),
                title=resolved_title,
                content=resolved_content,
                model=response.model,
                cost_time=cost_time,
                time_sensitivity=result_dict.get("timeSensitivity"),
                action_clarity=result_dict.get("actionClarity"),
                complexity=result_dict.get("complexity"),
                suggestions=result_dict.get("suggestions")
            )
            
        except Exception as e:
            cost_time = int((time.time() - start_time) * 1000)
            root_error = e
            try:
                from tenacity import RetryError

                if isinstance(e, RetryError) and e.last_attempt and e.last_attempt.exception():
                    root_error = e.last_attempt.exception()
            except Exception:
                pass
            return ClassificationResult(
                success=False,
                classification="unclear",
                confidence=0.0,
                reasoning="分析失败",
                recommended_status="new",
                title=(title or "").strip() or (text or "").strip()[:16] or None,
                content=(content or "").strip() or (text or "").strip() or None,
                model=model or self.settings.llm_model,
                cost_time=cost_time,
                error_message=str(root_error)
            )

    async def understand(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None,
        text: Optional[str] = None,
        context: str = "",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> UnderstandingResult:
        start_time = time.time()

        try:
            source_text = (text or content or title or "").strip()
            resolved_title = (title or "").strip()
            resolved_content = (content or "").strip()

            llm = self._get_llm(model)

            if (not resolved_title) or (not resolved_content):
                enrich_response = await llm.generate_structured(
                    prompt=enrichment.build_enrich_title_content_prompt(source_text),
                    system_prompt=enrichment.ENRICH_TITLE_CONTENT_SYSTEM_PROMPT,
                    temperature=0.2,
                    max_tokens=300
                )
                enrich_dict = json.loads(enrich_response.content)
                if not resolved_title:
                    resolved_title = str(enrich_dict.get("title", "")).strip() or source_text[:16]
                if not resolved_content:
                    resolved_content = str(enrich_dict.get("content", "")).strip() or source_text

            response = await llm.generate_structured(
                prompt=understanding.build_understanding_prompt(source_text),
                system_prompt=None,
                temperature=temperature if temperature is not None else 0.2,
                max_tokens=max_tokens if max_tokens is not None else 400
            )
            result_dict = json.loads(response.content)

            cost_time = int((time.time() - start_time) * 1000)

            core_dict = result_dict.get("core") or {}
            core = UnderstandingCore(
                entity=str(core_dict.get("entity", "") or ""),
                action=str(core_dict.get("action", "") or ""),
                context=str(core_dict.get("context", "") or "")
            )

            return UnderstandingResult(
                success=True,
                confidence=float(result_dict.get("confidence", 0.5)),
                reasoning=str(result_dict.get("reasoning", "") or ""),
                recommended_status="understood",
                title=str(result_dict.get("title", "") or resolved_title).strip() or None,
                clarified_text=str(result_dict.get("clarified_text", "") or "").strip() or None,
                tags=result_dict.get("tags"),
                core=core,
                model=response.model,
                cost_time=cost_time
            )

        except Exception as e:
            cost_time = int((time.time() - start_time) * 1000)
            return UnderstandingResult(
                success=False,
                confidence=0.0,
                reasoning="分析失败",
                recommended_status="new",
                title=(title or "").strip() or (text or "").strip()[:16] or None,
                clarified_text=None,
                tags=None,
                core=None,
                model=model or self.settings.llm_model,
                cost_time=cost_time,
                error_message=str(e)
            )
    
    async def analyze_evolution(
        self,
        title: str,
        content: str,
        current_state: str,
        current_type: str,
        user_behavior: str,
        behavior_count: int,
        created_at: str = "",
        completion_times: int = 0,
        model: Optional[str] = None
    ) -> EvolutionResult:
        """演化分析"""
        start_time = time.time()
        
        try:
            llm = self._get_llm(model)
            
            # 构建提示词
            system_prompt = evolution.EVOLUTION_SYSTEM_PROMPT
            user_prompt = evolution.build_evolution_prompt(
                title=title,
                content=content,
                current_state=current_state,
                current_type=current_type,
                user_behavior=user_behavior,
                behavior_count=behavior_count,
                created_at=created_at,
                completion_times=completion_times
            )
            
            # 调用 LLM
            response = await llm.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            # 解析响应
            result_dict = json.loads(response.content)
            
            cost_time = int((time.time() - start_time) * 1000)
            
            return EvolutionResult(
                success=True,
                classification=result_dict.get("classification", current_type),
                confidence=float(result_dict.get("confidence", 0.5)),
                reasoning=result_dict.get("reasoning", ""),
                recommended_status=result_dict.get("recommendedStatus", current_state),
                model=response.model,
                cost_time=cost_time,
                should_evolve=result_dict.get("shouldEvolve", False),
                evolution_reason=result_dict.get("evolutionReason", ""),
                from_type=result_dict.get("fromType", current_type),
                to_type=result_dict.get("toType", current_type),
                split_suggestions=result_dict.get("splitSuggestions"),
                merge_suggestions=result_dict.get("mergeSuggestions"),
                suggestions=result_dict.get("suggestions")
            )
            
        except Exception as e:
            cost_time = int((time.time() - start_time) * 1000)
            return EvolutionResult(
                success=False,
                classification=current_type,
                confidence=0.0,
                reasoning="分析失败",
                recommended_status=current_state,
                model=model or self.settings.llm_model,
                cost_time=cost_time,
                error_message=str(e),
                should_evolve=False,
                evolution_reason="",
                from_type=current_type,
                to_type=current_type
            )
    
    async def retrospect(
        self,
        title: str,
        content: str,
        completed_at: str,
        created_at: str,
        completion_data: str = "",
        model: Optional[str] = None
    ) -> RetrospectResult:
        """复盘分析"""
        start_time = time.time()
        
        try:
            llm = self._get_llm(model)
            
            # 构建提示词
            system_prompt = retrospect.RETROSPECT_SYSTEM_PROMPT
            user_prompt = retrospect.build_retrospect_prompt(
                title=title,
                content=content,
                completed_at=completed_at,
                created_at=created_at,
                completion_data=completion_data
            )
            
            # 调用 LLM
            response = await llm.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            # 解析响应
            result_dict = json.loads(response.content)
            
            cost_time = int((time.time() - start_time) * 1000)
            
            return RetrospectResult(
                success=True,
                classification="completed",
                confidence=float(result_dict.get("confidence", 0.9)),
                reasoning=result_dict.get("reasoning", ""),
                recommended_status="archived",
                model=response.model,
                cost_time=cost_time,
                achievements=result_dict.get("achievements", []),
                learnings=result_dict.get("learnings", []),
                improvements=result_dict.get("improvements", []),
                patterns=result_dict.get("patterns"),
                related_almonds=result_dict.get("relatedAlmonds"),
                spawn_almonds=result_dict.get("spawnAlmonds"),
                suggestions=result_dict.get("suggestions")
            )
            
        except Exception as e:
            cost_time = int((time.time() - start_time) * 1000)
            return RetrospectResult(
                success=False,
                classification="completed",
                confidence=0.0,
                reasoning="分析失败",
                recommended_status="archived",
                model=model or self.settings.llm_model,
                cost_time=cost_time,
                error_message=str(e),
                achievements=[],
                learnings=[],
                improvements=[]
            )
