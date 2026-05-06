"""MCPHand — MCP Server 工具。

通过 MCP 协议调用远程工具服务。
Credential 不经过 Brain，由 MCP proxy 从 vault 获取。

配置示例（agent_config.yaml）:
    hands:
      - type: mcp
        name: feishu_bot
        mcp_url: http://localhost:8080/mcp
        tools: [send_text, create_doc, write_sheet]
"""

from typing import Any

import httpx

from ravey.ai.agent_framework.hands.base import Hand


class MCPHand(Hand):

    def __init__(self, tool_name: str, mcp_url: str, vault_token: str | None = None):
        self._name = tool_name
        self._mcp_url = mcp_url
        self._vault_token = vault_token
        self._schema_cache: dict | None = None

    @property
    def name(self) -> str:
        return self._name

    def execute(self, name: str, input: dict[str, Any]) -> str:
        headers = {}
        if self._vault_token:
            headers["X-Vault-Token"] = self._vault_token

        try:
            resp = httpx.post(
                f"{self._mcp_url}/call",
                json={"tool": name, "input": input},
                headers=headers,
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", str(data))
        except httpx.HTTPError as e:
            return f"MCP Error: {e}"

    def schema(self) -> dict[str, Any]:
        if self._schema_cache:
            return self._schema_cache
        try:
            resp = httpx.get(f"{self._mcp_url}/schema/{self._name}", timeout=10.0)
            self._schema_cache = resp.json()
            return self._schema_cache
        except Exception:
            return {"name": self._name, "description": f"MCP tool: {self._name}", "parameters": {}}
