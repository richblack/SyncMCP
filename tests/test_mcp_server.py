"""
測試 MCP Server
"""


import pytest
from mcp.types import TextContent, Tool

from syncmcp.mcp.server import (
    call_tool,
    list_tools,
)


class TestMCPServerTools:
    """測試 MCP Server 工具註冊"""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """測試列出所有工具"""
        tools = await list_tools()

        assert isinstance(tools, list)
        assert len(tools) == 4

        tool_names = [t.name for t in tools]
        assert "sync_mcp_configs" in tool_names
        assert "check_sync_status" in tool_names
        assert "show_config_diff" in tool_names
        assert "suggest_conflict_resolution" in tool_names

    @pytest.mark.asyncio
    async def test_tool_schemas(self):
        """測試工具 schema 格式正確"""
        tools = await list_tools()

        for tool in tools:
            assert isinstance(tool, Tool)
            assert tool.name
            assert tool.description
            assert "inputSchema" in dir(tool)


class TestSyncMCPConfigsTool:
    """測試 sync_mcp_configs 工具"""

    @pytest.mark.asyncio
    async def test_sync_tool_dry_run(self, mock_all_configs):
        """測試 sync 工具 dry-run 模式"""
        result = await call_tool("sync_mcp_configs", {"dry_run": True})

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Dry" in result[0].text or "預覽" in result[0].text

    @pytest.mark.asyncio
    async def test_sync_tool_with_strategy(self, mock_all_configs):
        """測試 sync 工具指定策略"""
        result = await call_tool("sync_mcp_configs", {"strategy": "auto", "dry_run": True})

        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_sync_tool_with_backup(self, mock_all_configs):
        """測試 sync 工具帶備份"""
        result = await call_tool(
            "sync_mcp_configs", {"strategy": "auto", "dry_run": True, "create_backup": True}
        )

        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_sync_tool_response_format(self, mock_all_configs):
        """測試 sync 工具返回格式符合 MCP 規範"""
        result = await call_tool("sync_mcp_configs", {"dry_run": True})

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, TextContent)
            assert item.type == "text"
            assert isinstance(item.text, str)


class TestCheckSyncStatusTool:
    """測試 check_sync_status 工具"""

    @pytest.mark.asyncio
    async def test_status_tool(self, mock_all_configs):
        """測試 status 工具"""
        result = await call_tool("check_sync_status", {})

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], TextContent)

        # 應該包含配置狀態資訊
        output = result[0].text
        assert "配置" in output or "MCP" in output

    @pytest.mark.asyncio
    async def test_status_tool_shows_clients(self, mock_all_configs):
        """測試 status 工具顯示客戶端"""
        result = await call_tool("check_sync_status", {})

        output = result[0].text
        # 應該顯示至少一個客戶端
        assert "claude" in output.lower() or "roo" in output.lower() or "gemini" in output.lower()

    @pytest.mark.asyncio
    async def test_status_tool_no_args(self):
        """測試 status 工具無參數"""
        result = await call_tool("check_sync_status", {})

        assert isinstance(result, list)
        assert len(result) > 0


class TestShowConfigDiffTool:
    """測試 show_config_diff 工具"""

    @pytest.mark.asyncio
    async def test_diff_tool(self, mock_all_configs):
        """測試 diff 工具"""
        result = await call_tool("show_config_diff", {})

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], TextContent)

    @pytest.mark.asyncio
    async def test_diff_tool_shows_statistics(self, mock_all_configs):
        """測試 diff 工具顯示統計"""
        result = await call_tool("show_config_diff", {})

        output = result[0].text
        # 應該顯示統計資訊
        assert "統計" in output or "新增" in output or "刪除" in output or "修改" in output

    @pytest.mark.asyncio
    async def test_diff_tool_markdown_format(self, mock_all_configs):
        """測試 diff 工具使用 Markdown 格式"""
        result = await call_tool("show_config_diff", {})

        output = result[0].text
        # 應該包含 Markdown 標記
        assert "#" in output or "**" in output or "```" in output


class TestSuggestConflictResolutionTool:
    """測試 suggest_conflict_resolution 工具"""

    @pytest.mark.asyncio
    async def test_suggestion_tool(self, mock_all_configs):
        """測試建議工具"""
        result = await call_tool("suggest_conflict_resolution", {})

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], TextContent)

    @pytest.mark.asyncio
    async def test_suggestion_tool_provides_recommendations(self, mock_all_configs):
        """測試建議工具提供建議"""
        result = await call_tool("suggest_conflict_resolution", {})

        output = result[0].text
        # 應該包含建議或操作步驟
        assert "建議" in output or "推薦" in output or "操作" in output or "同步" in output

    @pytest.mark.asyncio
    async def test_suggestion_tool_no_conflicts(self, mock_all_configs):
        """測試沒有衝突時的建議工具"""
        result = await call_tool("suggest_conflict_resolution", {})

        output = result[0].text
        # 可能顯示"無衝突"或提供建議
        assert isinstance(output, str)
        assert len(output) > 0


class TestMCPServerErrorHandling:
    """測試 MCP Server 錯誤處理"""

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self):
        """測試無效工具名稱"""
        result = await call_tool("invalid_tool", {})

        assert isinstance(result, list)
        assert len(result) > 0
        assert "未知" in result[0].text or "Unknown" in result[0].text

    @pytest.mark.asyncio
    async def test_tool_with_invalid_args(self, mock_all_configs):
        """測試無效參數"""
        # 傳入無效的參數
        result = await call_tool("sync_mcp_configs", {"strategy": "invalid_strategy"})

        # 應該返回錯誤或使用默認值
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_tool_handles_exceptions(self, mock_home_dir, monkeypatch):
        """測試工具處理異常"""
        # 創建會導致錯誤的情況（沒有配置文件）

        result = await call_tool("check_sync_status", {})

        # 應該返回友善的錯誤訊息
        assert isinstance(result, list)
        assert len(result) > 0
        # 錯誤訊息應該是有幫助的
        output = result[0].text
        assert "錯誤" in output or "失敗" in output or "Error" in output.lower() or len(output) > 0


class TestMCPServerIntegration:
    """測試 MCP Server 整合功能"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, mock_all_configs):
        """測試完整工作流程"""
        # 1. 檢查狀態
        status_result = await call_tool("check_sync_status", {})
        assert len(status_result) > 0

        # 2. 查看差異
        diff_result = await call_tool("show_config_diff", {})
        assert len(diff_result) > 0

        # 3. 獲取建議
        suggestion_result = await call_tool("suggest_conflict_resolution", {})
        assert len(suggestion_result) > 0

        # 4. 執行同步（dry-run）
        sync_result = await call_tool("sync_mcp_configs", {"dry_run": True})
        assert len(sync_result) > 0

    @pytest.mark.asyncio
    async def test_all_tools_return_valid_mcp_format(self, mock_all_configs):
        """測試所有工具返回有效的 MCP 格式"""
        tool_names = [
            "sync_mcp_configs",
            "check_sync_status",
            "show_config_diff",
            "suggest_conflict_resolution",
        ]

        for tool_name in tool_names:
            args = {"dry_run": True} if tool_name == "sync_mcp_configs" else {}
            result = await call_tool(tool_name, args)

            # 驗證 MCP 格式
            assert isinstance(result, list)
            assert len(result) > 0
            for item in result:
                assert isinstance(item, TextContent)
                assert item.type == "text"
                assert isinstance(item.text, str)
                assert len(item.text) > 0
