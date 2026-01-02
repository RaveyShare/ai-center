"""API 请求模型"""
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from .enums import AnalysisType, UserBehavior


class AnalyzeRequest(BaseModel):
    """通用分析请求"""

    # 杏仁基本信息
    title: Optional[str] = Field(None, description="杏仁标题")
    content: Optional[str] = Field(None, description="杏仁内容")
    text: Optional[str] = Field(None, description="用户原始输入（一段话）")
    task_id: Optional[int] = Field(None, description="任务 ID")
    user_id: Optional[int] = Field(None, description="用户 ID")

    # 分析类型
    analysis_type: AnalysisType = Field(
        AnalysisType.CLASSIFICATION,
        description="分析类型"
    )

    # 模型配置
    model: Optional[str] = Field(None, description="指定使用的模型")
    temperature: Optional[float] = Field(None, description="温度参数", ge=0, le=2)
    max_tokens: Optional[int] = Field(None, description="最大 token 数")

    @model_validator(mode="after")
    def validate_input(self):
        if not (self.title or self.content or self.text):
            raise ValueError("title/content/text 至少提供一个")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "title": "学习 Python 装饰器",
                "content": "理解装饰器的工作原理，并能够写出自己的装饰器",
                "task_id": 12345,
                "user_id": 1001,
                "analysis_type": "classification"
            }
        }


class ClassificationRequest(BaseModel):
    """分类请求"""

    title: Optional[str] = Field(None, description="杏仁标题")
    content: Optional[str] = Field(None, description="杏仁内容")
    text: Optional[str] = Field(None, description="用户原始输入（一段话）")
    task_id: Optional[int] = Field(None, description="任务 ID")
    user_id: Optional[int] = Field(None, description="用户 ID")

    # 上下文信息（可选）
    context: Optional[str] = Field(None, description="额外上下文信息")

    # 模型配置（可选）
    model: Optional[str] = Field(None, description="指定使用的模型")
    temperature: Optional[float] = Field(None, description="温度参数", ge=0, le=2)
    max_tokens: Optional[int] = Field(None, description="最大 token 数")

    @model_validator(mode="after")
    def validate_input(self):
        if not (self.title or self.content or self.text):
            raise ValueError("title/content/text 至少提供一个")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "title": "买菜",
                "content": "明天去超市买菜，需要买西红柿、鸡蛋、葱",
                "task_id": 12346,
                "user_id": 1001
            }
        }


class UnderstandingRequest(BaseModel):
    title: Optional[str] = Field(None, description="杏仁标题")
    content: Optional[str] = Field(None, description="杏仁内容")
    text: Optional[str] = Field(None, description="用户原始输入（一段话）")
    task_id: Optional[int] = Field(None, description="任务 ID")
    user_id: Optional[int] = Field(None, description="用户 ID")

    context: Optional[str] = Field(None, description="额外上下文信息")

    model: Optional[str] = Field(None, description="指定使用的模型")
    temperature: Optional[float] = Field(None, description="温度参数", ge=0, le=2)
    max_tokens: Optional[int] = Field(None, description="最大 token 数")

    @model_validator(mode="after")
    def validate_input(self):
        if not (self.title or self.content or self.text):
            raise ValueError("title/content/text 至少提供一个")
        return self


class EvolutionRequest(BaseModel):
    """演化分析请求"""

    title: str = Field(..., description="杏仁标题")
    content: str = Field(..., description="杏仁内容")
    task_id: Optional[int] = Field(None, description="任务 ID")
    user_id: Optional[int] = Field(None, description="用户 ID")

    # 当前状态
    current_state: str = Field(..., description="当前状态")
    current_type: str = Field(..., description="当前类型")

    # 触发信息
    user_behavior: UserBehavior = Field(..., description="用户行为")
    behavior_count: int = Field(default=1, description="该行为发生次数")

    # 历史信息
    created_at: Optional[str] = Field(None, description="创建时间")
    last_updated_at: Optional[str] = Field(None, description="最后更新时间")
    completion_times: int = Field(default=0, description="完成次数")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "学习 Python",
                "content": "系统学习 Python 编程",
                "task_id": 12347,
                "user_id": 1001,
                "current_state": "action",
                "current_type": "action",
                "user_behavior": "defer",
                "behavior_count": 3,
                "completion_times": 0
            }
        }


class RetrospectRequest(BaseModel):
    """复盘请求"""

    title: str = Field(..., description="杏仁标题")
    content: str = Field(..., description="杏仁内容")
    task_id: Optional[int] = Field(None, description="任务 ID")
    user_id: Optional[int] = Field(None, description="用户 ID")

    # 完成信息
    completed_at: str = Field(..., description="完成时间")
    completion_data: Optional[str] = Field(None, description="完成数据（JSON 字符串）")

    # 历史信息
    created_at: str = Field(..., description="创建时间")
    state_history: Optional[list[dict]] = Field(None, description="状态历史")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "完成项目文档",
                "content": "为新项目编写完整的技术文档",
                "task_id": 12348,
                "user_id": 1001,
                "completed_at": "2025-01-15T10:30:00",
                "created_at": "2025-01-10T09:00:00",
                "completion_data": '{"actual_time": 5, "quality": "high"}'
            }
        }
