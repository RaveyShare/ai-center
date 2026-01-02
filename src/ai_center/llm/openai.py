"""OpenAI LLM 实现"""
import json
import time
from typing import Any, Optional

import re

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..utils.logger import get_logger
from .base import BaseLLM, LLMConfig, LLMResponse


logger = get_logger(__name__)


class OpenAILLM(BaseLLM):
    """OpenAI LLM (兼容所有 OpenAI API 格式的服务)"""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        
        # 解决本地调试时的代理问题
        # 如果连接的是本地地址，强制设置 NO_PROXY
        if "localhost" in (config.base_url or "") or "127.0.0.1" in (config.base_url or ""):
            import os
            if not os.environ.get("NO_PROXY"):
                os.environ["NO_PROXY"] = "localhost,127.0.0.1"
                logger.info("Set NO_PROXY=localhost,127.0.0.1 for local connection")

        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            **kwargs: Any
    ) -> LLMResponse:
        """生成响应"""
        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 合并配置
        model = kwargs.get("model", self.config.model)
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }
        
        # 支持额外的 OpenAI 参数
        if "response_format" in kwargs:
            params["response_format"] = kwargs["response_format"]
        if "tools" in kwargs:
            params["tools"] = kwargs["tools"]
        if "tool_choice" in kwargs:
            params["tool_choice"] = kwargs["tool_choice"]

        try:
            logger.info(f"Calling OpenAI API with params: {json.dumps(params, ensure_ascii=False, default=str)}")
            response = await self.client.chat.completions.create(**params)

            content = response.choices[0].message.content
            
            # 处理 usage
            usage_dict = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
            if response.usage:
                usage_dict = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }

            cost_time = int((time.time() - start_time) * 1000)
            logger.info(f"OpenAI API call successful. Cost: {cost_time}ms. Usage: {usage_dict}")

            try:
                raw_response = response.model_dump()
            except Exception:
                raw_response = {"raw": str(response)}

            return LLMResponse(
                content=content or "", # content might be null for tool calls, handle gracefully
                model=response.model,
                usage=usage_dict,
                cost_time=cost_time,
                raw_response=raw_response
            )

        except Exception as e:
            logger.exception("Failed to call OpenAI API")
            raise RuntimeError(f"Failed to call OpenAI API: {str(e)}") from e

    async def generate_structured(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            response_format: Optional[dict[str, Any]] = None,
            **kwargs: Any
    ) -> LLMResponse:
        """生成结构化响应"""
        
        # 尝试使用 JSON Mode 如果被明确请求且支持
        # 但为了兼容性，默认使用 Prompt Engineering 方式，同 Qwen 实现
        
        # 构建强制 JSON 输出的 system prompt
        json_instruction = (
            "\n\n你必须返回有效的 JSON 格式，不要包含任何其他文字、解释或 markdown 标记。"
            "只返回纯 JSON 对象。"
        )

        if system_prompt:
            enhanced_system_prompt = system_prompt + json_instruction
        else:
            enhanced_system_prompt = (
                    "你是一个专业的 AI 助手，专门返回结构化的 JSON 数据。" +
                    json_instruction
            )

        # 如果明确传入了 response_format={"type": "json_object"}，则传递给 API
        # 许多本地模型也开始支持 json_object
        call_kwargs = kwargs.copy()
        if response_format:
             # 这里不直接传 response_format 给 OpenAI，因为不同后端实现不同
             # 保持与 Qwen 一致的 Prompt 策略最安全
             pass

        response = await self.generate(
            prompt=prompt,
            system_prompt=enhanced_system_prompt,
            **call_kwargs
        )

        # 验证返回的是否为有效 JSON
        try:
            # 尝试清理可能的 markdown 标记
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # 验证 JSON
            json.loads(content)
            response.content = content

        except json.JSONDecodeError as e:
            # 记录失败的内容以便调试
            logger.error(f"Invalid JSON received: {response.content}")
            raise ValueError(f"LLM returned invalid JSON: {str(e)}\nContent: {response.content}") from e

        return response

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            logger.info("Starting health check...")
            response = await self.generate(
                prompt="Hello",
                system_prompt="You are a helpful assistant. Reply with 'OK'."
            )
            content = response.content.lower()
            logger.info(f"Health check response: {content}")
            return "ok" in content or len(content) < 100 # 宽松检查
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
            content = response.content.lower()
            logger.info(f"Health check response: {content}")
            return "ok" in content or len(content) < 100 # 宽松检查
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
