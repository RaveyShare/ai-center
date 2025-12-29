"""配置管理模块"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 应用基础配置
    app_name: str = "Almond AI Center"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # API 配置
    api_prefix: str = "/v1"
    api_token: str = Field(default="", description="API 访问令牌")
    
    # 大模型配置
    llm_provider: Literal["qwen", "openai", "claude"] = "qwen"
    llm_model: str = "qwen-plus"  # qwen-plus, qwen-turbo, qwen-max
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1000
    
    # 阿里云千问配置
    dashscope_api_key: str = Field(default="", description="阿里云 DashScope API Key")
    
    # OpenAI 配置（预留）
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI Base URL")
    
    # Redis 配置（缓存）
    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_ttl: int = 3600  # 缓存过期时间（秒）
    
    # 数据库配置（可选）
    database_url: str = Field(default="", description="数据库连接 URL")
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json 或 text
    
    # 性能配置
    max_concurrent_requests: int = 100
    request_timeout: int = 30
    
    # 杏仁特定配置
    classification_confidence_threshold: float = 0.7  # 分类置信度阈值
    evolution_trigger_threshold: int = 3  # 触发演化分析的行为次数
    
    @property
    def redis_url(self) -> str:
        """构建 Redis 连接 URL"""
        if not self.redis_enabled:
            return ""
        
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()