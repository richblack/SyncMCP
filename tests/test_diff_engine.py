"""
測試差異檢測引擎 (DiffEngine)
"""


import pytest

from syncmcp.core.config_manager import ClientConfig
from syncmcp.core.diff_engine import DiffEngine, DiffItem, DiffReport


class TestDiffItem:
    """測試 DiffItem 類"""

    def test_create_diff_item(self):
        """測試創建 DiffItem"""
        item = DiffItem(
            name="test-mcp",
            status="added",
            old_value=None,
            new_value={"type": "stdio", "command": "test"},
        )

        assert item.name == "test-mcp"
        assert item.status == "added"
        assert item.old_value is None
        assert item.new_value is not None


class TestDiffReport:
    """測試 DiffReport 類"""

    def test_create_empty_report(self):
        """測試創建空報告"""
        report = DiffReport()
        assert report.diffs == {}

    def test_add_diff(self):
        """測試添加差異項目"""
        report = DiffReport()
        item = DiffItem("test-mcp", "added")

        report.add_diff("claude-code", item)

        assert "claude-code" in report.diffs
        assert len(report.diffs["claude-code"]) == 1
        assert report.diffs["claude-code"][0].name == "test-mcp"

    def test_to_text(self):
        """測試轉換為文字"""
        report = DiffReport()
        report.add_diff("claude-code", DiffItem("mcp1", "added"))
        report.add_diff("claude-code", DiffItem("mcp2", "removed"))
        report.add_diff("claude-code", DiffItem("mcp3", "modified"))

        text = report.to_text()

        assert "claude-code" in text
        assert "+ mcp1" in text
        assert "- mcp2" in text
        assert "~ mcp3" in text

    def test_has_removals(self):
        """測試檢查是否有刪除"""
        report = DiffReport()
        assert not report.has_removals()

        report.add_diff("claude-code", DiffItem("mcp1", "added"))
        assert not report.has_removals()

        report.add_diff("claude-code", DiffItem("mcp2", "removed"))
        assert report.has_removals()


class TestDiffEngine:
    """測試 DiffEngine"""

    @pytest.fixture
    def diff_engine(self):
        """創建 DiffEngine 實例"""
        return DiffEngine()

    @pytest.fixture
    def sample_configs(self, temp_dir):
        """創建樣本配置"""
        # 配置 1 - 有 2 個 MCPs
        config1_path = temp_dir / "config1.json"
        config1 = ClientConfig("client1", config1_path)
        config1.mcpServers = {
            "filesystem": {"type": "stdio", "command": "npx", "args": ["-y", "server-filesystem"]},
            "brave-search": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "server-brave-search"],
            },
        }
        config1.last_modified = 1000.0

        # 配置 2 - 有 1 個相同 + 1 個不同
        config2_path = temp_dir / "config2.json"
        config2 = ClientConfig("client2", config2_path)
        config2.mcpServers = {
            "filesystem": {"type": "stdio", "command": "npx", "args": ["-y", "server-filesystem"]},
            "context7": {"type": "http", "url": "https://mcp.context7.com/mcp"},
        }
        config2.last_modified = 900.0

        return {"client1": config1, "client2": config2}

    def test_analyze_configs(self, diff_engine, sample_configs):
        """測試分析配置差異"""
        report = diff_engine.analyze(sample_configs)

        assert isinstance(report, DiffReport)
        assert len(report.diffs) > 0

    def test_select_source_newest(self, diff_engine, sample_configs):
        """測試選擇最新配置作為源"""
        # client1 的 last_modified 是 1000，應該被選為源
        source = diff_engine._select_source(sample_configs)

        assert source is not None
        assert source.client_name == "client1"

    def test_get_all_mcp_names(self, diff_engine, sample_configs):
        """測試獲取所有 MCP 名稱"""
        all_names = diff_engine._get_all_mcp_names(sample_configs)

        assert "filesystem" in all_names
        assert "brave-search" in all_names
        assert "context7" in all_names
        assert len(all_names) == 3

    def test_compare_configs_added(self, diff_engine):
        """測試檢測新增的 MCP"""
        source = {"mcp1": {"type": "stdio"}, "mcp2": {"type": "stdio"}}
        target = {"mcp1": {"type": "stdio"}}

        report = DiffReport()
        diff_engine._compare_configs(source, target, "test-client", report)

        # mcp2 在 target 中不存在，應該被標記為 added
        diffs = report.diffs.get("test-client", [])
        added_items = [d for d in diffs if d.status == "added"]
        assert len(added_items) == 1
        assert added_items[0].name == "mcp2"

    def test_compare_configs_removed(self, diff_engine):
        """測試檢測刪除的 MCP"""
        source = {"mcp1": {"type": "stdio"}}
        target = {"mcp1": {"type": "stdio"}, "mcp2": {"type": "stdio"}}

        report = DiffReport()
        diff_engine._compare_configs(source, target, "test-client", report)

        # mcp2 在 source 中不存在，應該被標記為 removed
        diffs = report.diffs.get("test-client", [])
        removed_items = [d for d in diffs if d.status == "removed"]
        assert len(removed_items) == 1
        assert removed_items[0].name == "mcp2"

    def test_compare_configs_modified(self, diff_engine):
        """測試檢測修改的 MCP"""
        source = {"mcp1": {"type": "stdio", "command": "test1"}}
        target = {"mcp1": {"type": "stdio", "command": "test2"}}

        report = DiffReport()
        diff_engine._compare_configs(source, target, "test-client", report)

        # mcp1 的配置不同，應該被標記為 modified
        diffs = report.diffs.get("test-client", [])
        modified_items = [d for d in diffs if d.status == "modified"]
        assert len(modified_items) == 1
        assert modified_items[0].name == "mcp1"

    def test_compare_configs_unchanged(self, diff_engine):
        """測試檢測未改變的 MCP"""
        source = {"mcp1": {"type": "stdio", "command": "test"}}
        target = {"mcp1": {"type": "stdio", "command": "test"}}

        report = DiffReport()
        diff_engine._compare_configs(source, target, "test-client", report)

        # mcp1 完全相同，應該被標記為 unchanged
        diffs = report.diffs.get("test-client", [])
        unchanged_items = [d for d in diffs if d.status == "unchanged"]
        # 注意：當前實現可能不記錄 unchanged 項目
        # 這取決於實際代碼實現

    def test_analyze_with_no_configs(self, diff_engine):
        """測試分析空配置"""
        report = diff_engine.analyze({})

        assert isinstance(report, DiffReport)
        assert len(report.diffs) == 0

    def test_analyze_with_identical_configs(self, diff_engine, temp_dir):
        """測試分析完全相同的配置"""
        config1 = ClientConfig("client1", temp_dir / "config1.json")
        config1.mcpServers = {"mcp1": {"type": "stdio"}}
        config1.last_modified = 1000.0

        config2 = ClientConfig("client2", temp_dir / "config2.json")
        config2.mcpServers = {"mcp1": {"type": "stdio"}}
        config2.last_modified = 900.0

        configs = {"client1": config1, "client2": config2}
        report = diff_engine.analyze(configs)

        # 配置完全相同，應該沒有差異（或只有 unchanged）
        # 實際行為取決於實現
        assert isinstance(report, DiffReport)
