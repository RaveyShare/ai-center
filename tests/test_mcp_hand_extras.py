"""MCPHand 网络成功路径覆盖。"""

from unittest.mock import MagicMock, patch

from ravey.ai.agent_framework.hands.mcp_hand import MCPHand


class TestMCPHandSuccess:

    def test_execute_with_vault_token(self):
        hand = MCPHand("send_text", "http://mcp.local", vault_token="secret-token")
        with patch(
            "ravey.ai.agent_framework.hands.mcp_hand.httpx.post"
        ) as post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"result": "sent"}
            post.return_value = mock_resp

            result = hand.execute("send_text", {"text": "hello"})

        assert result == "sent"
        # vault token 写到 header
        called_kwargs = post.call_args.kwargs
        assert called_kwargs["headers"]["X-Vault-Token"] == "secret-token"

    def test_execute_returns_full_data_when_no_result_key(self):
        hand = MCPHand("send_text", "http://mcp.local")
        with patch(
            "ravey.ai.agent_framework.hands.mcp_hand.httpx.post"
        ) as post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"status": "ok"}
            post.return_value = mock_resp

            result = hand.execute("send_text", {})

        assert "status" in result
        assert "ok" in result

    def test_schema_success_caches_response(self):
        hand = MCPHand("send_text", "http://mcp.local")
        with patch(
            "ravey.ai.agent_framework.hands.mcp_hand.httpx.get"
        ) as get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"name": "send_text", "parameters": {"text": "string"}}
            get.return_value = mock_resp

            schema_a = hand.schema()
            schema_b = hand.schema()  # 第二次走缓存

        assert schema_a == schema_b
        assert schema_a["name"] == "send_text"
        # httpx.get 只被调用了一次（第二次走缓存）
        assert get.call_count == 1
