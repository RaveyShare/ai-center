"""API 响应模型"""
from typing import Any, Optional

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """分析结果基类"""

    success: bool = Field(..., description="是否成功")
    classification: str = Field(..., description="分类结果")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    reasoning: str = Field(..., description="分析理由")
    recommended_status: str = Field(..., description="推荐状态")

    title: Optional[str] = Field(None, description="最终使用的标题")
    content: Optional[str] = Field(None, description="最终使用的内容")

    # 元数据
    model: str = Field(..., description="使用的模型")
    cost_time: int = Field(..., description="耗时（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息")

    # AI 建议（可选）
    suggestions: Optional[list[str]] = Field(None, description="AI 建议")
    next_actions: Optional[list[str]] = Field(None, description="推荐的下一步行动")


class ClassificationResult(AnalysisResult):
    """分类结果"""

    # 分类特有字段
    time_sensitivity: Optional[str] = Field(None, description="时间敏感度：high/medium/low")
    action_clarity: Optional[str] = Field(None, description="行动明确度：clear/vague")
    complexity: Optional[str] = Field(None, description="复杂度：simple/moderate/complex")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "classification": "action",
                "confidence": 0.85,
                "reasoning": "这是一个有明确时间要求和具体行动的任务",
                "recommended_status": "action",
                "model": "qwen-plus",
                "cost_time": 1200,
                "time_sensitivity": "high",
                "action_clarity": "clear",
                "complexity": "simple",
                "suggestions": ["建议设置提醒", "可以添加子任务清单"]
            }
        }


class UnderstandingCore(BaseModel):
    entity: str = Field("", description="对象/主体")
    action: str = Field("", description="动作/行为")
    context: str = Field("", description="场景/原因/约束")


class UnderstandingResult(BaseModel):
    success: bool = Field(..., description="是否成功")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    reasoning: str = Field(..., description="分析理由")
    recommended_status: str = Field(..., description="推荐状态")

    title: Optional[str] = Field(None, description="生成标题")
    clarified_text: Optional[str] = Field(None, description="澄清文本")
    tags: Optional[list[str]] = Field(None, description="标签列表")
    core: Optional[UnderstandingCore] = Field(None, description="核心信息抽取")

    model: str = Field(..., description="使用的模型")
    cost_time: int = Field(..., description="耗时（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息")


class EvolutionResult(AnalysisResult):
    """演化分析结果"""

    # 演化特有字段
    should_evolve: bool = Field(..., description="是否应该演化")
    evolution_reason: str = Field(..., description="演化原因")
    from_type: str = Field(..., description="原类型")
    to_type: str = Field(..., description="目标类型")

    # 演化建议
    split_suggestions: Optional[list[dict]] = Field(None, description="拆分建议")
    merge_suggestions: Optional[list[int]] = Field(None, description="合并建议（任务 ID）")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "classification": "goal",
                "confidence": 0.78,
                "reasoning": "用户多次延期，表明这不是一个可以快速完成的行动，而是需要长期规划的目标",
                "recommended_status": "goal",
                "model": "qwen-plus",
                "cost_time": 1500,
                "should_evolve": True,
                "evolution_reason": "连续 3 次延期，建议转为目标并拆分",
                "from_type": "action",
                "to_type": "goal",
                "split_suggestions": [
                    {"title": "第一阶段：基础学习", "content": "..."},
                    {"title": "第二阶段：实践项目", "content": "..."}
                ]
            }
        }


class RetrospectResult(AnalysisResult):
    """复盘结果"""

    # 复盘特有字段
    achievements: list[str] = Field(..., description="主要成就")
    learnings: list[str] = Field(..., description="学到的经验")
    improvements: list[str] = Field(..., description="改进建议")

    # 模式识别
    patterns: Optional[dict[str, Any]] = Field(None, description="识别的模式")
    related_almonds: Optional[list[int]] = Field(None, description="相关的杏仁 ID")

    # 生成新杏仁建议
    spawn_almonds: Optional[list[dict]] = Field(None, description="建议生成的新杏仁")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "classification": "completed",
                "confidence": 0.92,
                "reasoning": "任务已按时完成，质量良好",
                "recommended_status": "archived",
                "model": "qwen-plus",
                "cost_time": 1800,
                "achievements": [
                    "按时完成了文档编写",
                    "文档结构清晰，覆盖全面"
                ],
                "learnings": [
                    "提前规划大纲能提高效率",
                    "分段完成比一次性完成更轻松"
                ],
                "improvements": [
                    "下次可以加入更多代码示例",
                    "可以考虑添加流程图"
                ],
                "patterns": {
                    "completion_time_accuracy": 0.9,
                    "work_style": "incremental"
                },
                "spawn_almonds": [
                    {
                        "title": "定期更新文档",
                        "content": "每季度review一次项目文档",
                        "type": "action"
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    llm_provider: str = Field(..., description="LLM 提供商")
    llm_available: bool = Field(..., description="LLM 是否可用")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "llm_provider": "qwen",
                "llm_available": True
            }
        }
