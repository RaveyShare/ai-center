"""阿里千问 LLM 实现"""
import json
import re
import time
from typing import Any, Optional

import dashscope
from dashscope import Generation
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseLLM, LLMConfig, LLMResponse


class QwenLLM(BaseLLM):
    """阿里千问 LLM"""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        dashscope.api_key = config.api_key

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
        if isinstance(model, str) and model.startswith("qwen3-") and "-instruct" in model:
            model = re.sub(r"-instruct(?:-[\w]+)?$", "", model)

        params = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "result_format": "message"
        }
        if isinstance(model, str) and model.startswith("qwen3-"):
            params["enable_thinking"] = False

        try:
            response = Generation.call(**params)

            if response.status_code != 200:
                raise RuntimeError(f"Qwen API error: {response.code} - {response.message}")

            content = response.output.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens
            }

            cost_time = int((time.time() - start_time) * 1000)

            try:
                raw_response = response.to_dict()
            except Exception:
                raw_response = dict(response) if isinstance(response, dict) else {"raw": str(response)}

            return LLMResponse(
                content=content,
                model=params["model"],
                usage=usage,
                cost_time=cost_time,
                raw_response=raw_response
            )

        except Exception as e:
            raise RuntimeError(f"Failed to call Qwen API: {str(e)}") from e

    async def generate_structured(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            response_format: Optional[dict[str, Any]] = None,
            **kwargs: Any
    ) -> LLMResponse:
        """生成结构化响应

        千问不原生支持 response_format，所以在 system_prompt 中要求返回 JSON
        """
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

        response = await self.generate(
            prompt=prompt,
            system_prompt=enhanced_system_prompt,
            **kwargs
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
            raise ValueError(f"LLM returned invalid JSON: {str(e)}\nContent: {response.content}") from e

        return response

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.generate(
                prompt="Hello",
                system_prompt="You are a helpful assistant. Reply with 'OK'."
            )
            return "OK" in response.content or "ok" in response.content.lower()
        except Exception:
            return False
