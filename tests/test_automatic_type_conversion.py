"""測試自動類型轉換功能"""

import pytest
from syncmcp.core.config_manager import (
    ClaudeCodeAdapter,
    RooCodeAdapter,
    ClaudeDesktopAdapter,
    GeminiAdapter,
)


class TestClaudeCodeAdapter:
    """測試 Claude Code 適配器的類型轉換"""

    def test_streamable_http_to_http_with_headers(self):
        """streamable-http (有 headers) → http"""
        adapter = ClaudeCodeAdapter()
        config = {
            "test-mcp": {
                "type": "streamable-http",
                "url": "https://example.com",
                "headers": {"API_KEY": "test123"},
            }
        }

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "http"
        assert result["test-mcp"]["url"] == "https://example.com"
        assert result["test-mcp"]["headers"]["API_KEY"] == "test123"

    def test_streamable_http_to_sse_without_headers(self):
        """streamable-http (無 headers) → sse"""
        adapter = ClaudeCodeAdapter()
        config = {
            "test-mcp": {"type": "streamable-http", "url": "https://example.com"}
        }

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "sse"
        assert result["test-mcp"]["url"] == "https://example.com"

    def test_streamable_http_to_sse_with_empty_headers(self):
        """streamable-http (空 headers) → sse"""
        adapter = ClaudeCodeAdapter()
        config = {
            "test-mcp": {
                "type": "streamable-http",
                "url": "https://example.com",
                "headers": {},
            }
        }

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "sse"

    def test_stdio_unchanged(self):
        """stdio 類型保持不變"""
        adapter = ClaudeCodeAdapter()
        config = {
            "test-mcp": {
                "type": "stdio",
                "command": "npx",
                "args": ["test-package"],
            }
        }

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "stdio"
        assert result["test-mcp"]["command"] == "npx"

    def test_http_unchanged(self):
        """http 類型保持不變"""
        adapter = ClaudeCodeAdapter()
        config = {
            "test-mcp": {
                "type": "http",
                "url": "https://example.com",
                "headers": {"API_KEY": "test"},
            }
        }

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "http"

    def test_sse_unchanged(self):
        """sse 類型保持不變"""
        adapter = ClaudeCodeAdapter()
        config = {"test-mcp": {"type": "sse", "url": "https://example.com"}}

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "sse"


class TestRooCodeAdapter:
    """測試 Roo Code 適配器的類型轉換"""

    def test_http_to_streamable_http(self):
        """http → streamable-http"""
        adapter = RooCodeAdapter()
        config = {
            "test-mcp": {
                "type": "http",
                "url": "https://example.com",
                "headers": {"API_KEY": "test"},
            }
        }

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "streamable-http"
        assert result["test-mcp"]["url"] == "https://example.com"
        assert result["test-mcp"]["headers"]["API_KEY"] == "test"

    def test_sse_to_streamable_http(self):
        """sse → streamable-http"""
        adapter = RooCodeAdapter()
        config = {"test-mcp": {"type": "sse", "url": "https://example.com"}}

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "streamable-http"
        assert result["test-mcp"]["url"] == "https://example.com"

    def test_stdio_unchanged(self):
        """stdio 類型保持不變"""
        adapter = RooCodeAdapter()
        config = {
            "test-mcp": {
                "type": "stdio",
                "command": "npx",
                "args": ["test-package"],
            }
        }

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "stdio"

    def test_streamable_http_unchanged(self):
        """streamable-http 類型保持不變"""
        adapter = RooCodeAdapter()
        config = {
            "test-mcp": {"type": "streamable-http", "url": "https://example.com"}
        }

        result = adapter.normalize_config(config)

        assert result["test-mcp"]["type"] == "streamable-http"


class TestClaudeDesktopAdapter:
    """測試 Claude Desktop 適配器的過濾功能"""

    def test_filters_http(self):
        """過濾掉 http 類型"""
        adapter = ClaudeDesktopAdapter()
        config = {
            "stdio-mcp": {"type": "stdio", "command": "npx"},
            "http-mcp": {"type": "http", "url": "https://example.com"},
        }

        result = adapter.normalize_config(config)

        assert "stdio-mcp" in result
        assert "http-mcp" not in result

    def test_filters_sse(self):
        """過濾掉 sse 類型"""
        adapter = ClaudeDesktopAdapter()
        config = {
            "stdio-mcp": {"type": "stdio", "command": "npx"},
            "sse-mcp": {"type": "sse", "url": "https://example.com"},
        }

        result = adapter.normalize_config(config)

        assert "stdio-mcp" in result
        assert "sse-mcp" not in result

    def test_filters_streamable_http(self):
        """過濾掉 streamable-http 類型"""
        adapter = ClaudeDesktopAdapter()
        config = {
            "stdio-mcp": {"type": "stdio", "command": "npx"},
            "streamable-mcp": {
                "type": "streamable-http",
                "url": "https://example.com",
            },
        }

        result = adapter.normalize_config(config)

        assert "stdio-mcp" in result
        assert "streamable-mcp" not in result

    def test_keeps_only_stdio(self):
        """只保留 stdio 類型"""
        adapter = ClaudeDesktopAdapter()
        config = {
            "stdio1": {"type": "stdio", "command": "npx", "args": ["pkg1"]},
            "stdio2": {"type": "stdio", "command": "uv", "args": ["pkg2"]},
            "http": {"type": "http", "url": "https://example.com"},
            "sse": {"type": "sse", "url": "https://example.com"},
            "streamable": {"type": "streamable-http", "url": "https://example.com"},
        }

        result = adapter.normalize_config(config)

        assert len(result) == 2
        assert "stdio1" in result
        assert "stdio2" in result
        assert "http" not in result
        assert "sse" not in result
        assert "streamable" not in result

    def test_handles_transport_field(self):
        """支援 transport 欄位（向後相容）"""
        adapter = ClaudeDesktopAdapter()
        config = {
            "old-format": {"transport": "stdio", "command": "npx"},
            "http-format": {"transport": "http", "url": "https://example.com"},
        }

        result = adapter.normalize_config(config)

        assert "old-format" in result
        assert "http-format" not in result


class TestRoundTripConversion:
    """測試往返轉換（Claude Code ↔ Roo Code）"""

    def test_claude_to_roo_to_claude_http(self):
        """Claude Code → Roo Code → Claude Code (http 類型)"""
        claude_adapter = ClaudeCodeAdapter()
        roo_adapter = RooCodeAdapter()

        # 原始 Claude Code 配置
        original = {
            "test-mcp": {
                "type": "http",
                "url": "https://example.com",
                "headers": {"API_KEY": "test"},
            }
        }

        # Claude → Roo
        roo_config = roo_adapter.normalize_config(original)
        assert roo_config["test-mcp"]["type"] == "streamable-http"

        # Roo → Claude
        claude_config = claude_adapter.normalize_config(roo_config)
        assert claude_config["test-mcp"]["type"] == "http"
        assert claude_config["test-mcp"]["headers"]["API_KEY"] == "test"

    def test_claude_to_roo_to_claude_sse(self):
        """Claude Code → Roo Code → Claude Code (sse 類型)"""
        claude_adapter = ClaudeCodeAdapter()
        roo_adapter = RooCodeAdapter()

        # 原始 Claude Code 配置
        original = {"test-mcp": {"type": "sse", "url": "https://example.com"}}

        # Claude → Roo
        roo_config = roo_adapter.normalize_config(original)
        assert roo_config["test-mcp"]["type"] == "streamable-http"

        # Roo → Claude
        claude_config = claude_adapter.normalize_config(roo_config)
        assert claude_config["test-mcp"]["type"] == "sse"

    def test_stdio_unchanged_across_clients(self):
        """stdio 類型在所有客戶端都保持不變"""
        claude_adapter = ClaudeCodeAdapter()
        roo_adapter = RooCodeAdapter()
        desktop_adapter = ClaudeDesktopAdapter()

        original = {
            "test-mcp": {
                "type": "stdio",
                "command": "npx",
                "args": ["test-package"],
            }
        }

        # 所有客戶端都應該保持 stdio
        assert claude_adapter.normalize_config(original)["test-mcp"]["type"] == "stdio"
        assert roo_adapter.normalize_config(original)["test-mcp"]["type"] == "stdio"
        assert desktop_adapter.normalize_config(original)["test-mcp"]["type"] == "stdio"


class TestRealWorldScenarios:
    """測試真實世界的場景"""

    def test_context7_conversion(self):
        """測試 context7 的實際轉換"""
        # Claude Code 配置
        claude_config = {
            "context7": {
                "type": "http",
                "url": "https://mcp.context7.com/mcp",
                "headers": {"CONTEXT7_API_KEY": "ctx7sk-test"},
            }
        }

        # 轉換到 Roo Code
        roo_adapter = RooCodeAdapter()
        roo_config = roo_adapter.normalize_config(claude_config)

        assert roo_config["context7"]["type"] == "streamable-http"
        assert roo_config["context7"]["url"] == "https://mcp.context7.com/mcp"
        assert roo_config["context7"]["headers"]["CONTEXT7_API_KEY"] == "ctx7sk-test"

    def test_canva_conversion(self):
        """測試 canva 的實際轉換"""
        # Claude Code 配置
        claude_config = {"canva": {"type": "sse", "url": "https://mcp.canva.com/mcp"}}

        # 轉換到 Roo Code
        roo_adapter = RooCodeAdapter()
        roo_config = roo_adapter.normalize_config(claude_config)

        assert roo_config["canva"]["type"] == "streamable-http"
        assert roo_config["canva"]["url"] == "https://mcp.canva.com/mcp"

    def test_mixed_mcp_types(self):
        """測試混合類型的 MCP 配置"""
        config = {
            "stdio-mcp": {
                "type": "stdio",
                "command": "npx",
                "args": ["test-package"],
            },
            "http-mcp": {
                "type": "http",
                "url": "https://example.com",
                "headers": {"API_KEY": "test"},
            },
            "sse-mcp": {"type": "sse", "url": "https://example2.com"},
        }

        # Claude Code → Roo Code
        roo_adapter = RooCodeAdapter()
        roo_config = roo_adapter.normalize_config(config)

        assert roo_config["stdio-mcp"]["type"] == "stdio"
        assert roo_config["http-mcp"]["type"] == "streamable-http"
        assert roo_config["sse-mcp"]["type"] == "streamable-http"

        # Claude Desktop 過濾
        desktop_adapter = ClaudeDesktopAdapter()
        desktop_config = desktop_adapter.normalize_config(config)

        assert len(desktop_config) == 1
        assert "stdio-mcp" in desktop_config
        assert "http-mcp" not in desktop_config
        assert "sse-mcp" not in desktop_config
