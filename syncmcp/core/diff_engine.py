"""
差異檢測引擎 - 分析配置差異
"""

from dataclasses import dataclass


@dataclass
class DiffItem:
    """差異項目"""

    name: str
    status: str  # 'added', 'removed', 'modified', 'unchanged'
    old_value: dict = None
    new_value: dict = None


class DiffReport:
    """差異報告"""

    def __init__(self):
        self.diffs: dict[str, list[DiffItem]] = {}

    def add_diff(self, client: str, diff_item: DiffItem):
        """新增差異項目"""
        if client not in self.diffs:
            self.diffs[client] = []
        self.diffs[client].append(diff_item)

    def to_text(self) -> str:
        """轉換為文字報告"""
        lines = []
        for client, items in self.diffs.items():
            if not items:
                continue
            lines.append(f"\n{client}:")
            for item in items:
                if item.status == "added":
                    lines.append(f"  + {item.name}")
                elif item.status == "removed":
                    lines.append(f"  - {item.name}")
                elif item.status == "modified":
                    lines.append(f"  ~ {item.name}")
        return "\n".join(lines) if lines else "無差異"

    def has_removals(self) -> bool:
        """檢查是否有配置被移除"""
        for items in self.diffs.values():
            if any(item.status == "removed" for item in items):
                return True
        return False

    def get_removal_count(self, client: str) -> int:
        """獲取特定客戶端的移除數量"""
        if client not in self.diffs:
            return 0
        return sum(1 for item in self.diffs[client] if item.status == "removed")


class DiffEngine:
    """差異檢測引擎"""

    def analyze(self, configs: dict[str, "ClientConfig"]) -> DiffReport:
        """分析配置差異"""
        report = DiffReport()

        # 找出所有 MCP 的聯集
        all_mcps = self._get_all_mcp_names(configs)

        # 確定「源」配置（最新的）
        source = self._select_source(configs)

        if not source:
            return report

        # 對每個客戶端分析差異
        for client_name, config in configs.items():
            if client_name == source.client_name:
                continue  # 跳過源本身

            self._compare_configs(source.mcpServers, config.mcpServers, client_name, report)

        return report

    def _get_all_mcp_names(self, configs: dict) -> set[str]:
        """獲取所有 MCP 名稱"""
        all_names = set()
        for config in configs.values():
            all_names.update(config.mcpServers.keys())
        return all_names

    def _select_source(self, configs: dict) -> "ClientConfig":
        """選擇最新的配置作為源"""
        latest = None
        for config in configs.values():
            if config.last_modified:
                if not latest or config.last_modified > latest.last_modified:
                    latest = config
        return latest

    def _compare_configs(self, source: dict, target: dict, client: str, report: DiffReport):
        """比較兩個配置"""
        source_keys = set(source.keys())
        target_keys = set(target.keys())

        # 新增的
        for name in source_keys - target_keys:
            report.add_diff(client, DiffItem(name=name, status="added", new_value=source[name]))

        # 移除的
        for name in target_keys - source_keys:
            report.add_diff(client, DiffItem(name=name, status="removed", old_value=target[name]))

        # 修改的
        for name in source_keys & target_keys:
            if source[name] != target[name]:
                report.add_diff(
                    client,
                    DiffItem(
                        name=name, status="modified", old_value=target[name], new_value=source[name]
                    ),
                )
