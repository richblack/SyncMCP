"""
同步歷史記錄 - 記錄每次同步的結果
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class SyncHistoryEntry:
    """同步歷史記錄項"""

    timestamp: str  # ISO 格式時間戳
    success: bool
    strategy: str
    changes: dict[str, list[str]]  # 客戶端 -> 變更列表
    warnings: list[str]
    errors: list[str]
    backup_path: str | None = None
    duration_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """轉換為字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SyncHistoryEntry":
        """從字典創建"""
        return cls(**data)


class SyncHistoryManager:
    """同步歷史管理器"""

    def __init__(self, history_file: Path | None = None):
        """
        初始化歷史管理器

        Args:
            history_file: 歷史文件路徑（預設 ~/.syncmcp/history.json）
        """
        if history_file is None:
            history_file = Path.home() / ".syncmcp" / "history.json"

        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # 確保文件存在
        if not self.history_file.exists():
            self._save_history([])

    def add_entry(
        self,
        success: bool,
        strategy: str,
        changes: dict[str, list[str]],
        warnings: list[str],
        errors: list[str],
        backup_path: str | None = None,
        duration_seconds: float | None = None,
    ):
        """
        添加新的同步記錄

        Args:
            success: 是否成功
            strategy: 同步策略
            changes: 變更內容
            warnings: 警告列表
            errors: 錯誤列表
            backup_path: 備份路徑
            duration_seconds: 執行時間（秒）
        """
        entry = SyncHistoryEntry(
            timestamp=datetime.now().isoformat(),
            success=success,
            strategy=strategy,
            changes=changes,
            warnings=warnings,
            errors=errors,
            backup_path=backup_path,
            duration_seconds=duration_seconds,
        )

        history = self._load_history()
        history.append(entry.to_dict())

        # 保留最近 100 條記錄
        if len(history) > 100:
            history = history[-100:]

        self._save_history(history)

    def get_history(self, limit: int = 10) -> list[SyncHistoryEntry]:
        """
        獲取歷史記錄

        Args:
            limit: 返回的記錄數量（預設 10 條）

        Returns:
            歷史記錄列表（最新的在前）
        """
        history = self._load_history()
        recent = history[-limit:] if limit else history
        return [SyncHistoryEntry.from_dict(entry) for entry in reversed(recent)]

    def get_last_sync(self) -> SyncHistoryEntry | None:
        """
        獲取最後一次同步記錄

        Returns:
            最後一次同步記錄，如果沒有則返回 None
        """
        history = self._load_history()
        if not history:
            return None
        return SyncHistoryEntry.from_dict(history[-1])

    def get_statistics(self) -> dict[str, Any]:
        """
        獲取統計信息

        Returns:
            統計數據字典
        """
        history = self._load_history()

        if not history:
            return {
                "total_syncs": 0,
                "successful_syncs": 0,
                "failed_syncs": 0,
                "success_rate": 0.0,
                "total_changes": 0,
                "total_warnings": 0,
                "total_errors": 0,
            }

        total = len(history)
        successful = sum(1 for entry in history if entry.get("success", False))
        failed = total - successful

        total_changes = sum(
            len(changes) for entry in history for changes in entry.get("changes", {}).values()
        )

        total_warnings = sum(len(entry.get("warnings", [])) for entry in history)
        total_errors = sum(len(entry.get("errors", [])) for entry in history)

        return {
            "total_syncs": total,
            "successful_syncs": successful,
            "failed_syncs": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0.0,
            "total_changes": total_changes,
            "total_warnings": total_warnings,
            "total_errors": total_errors,
        }

    def clear_history(self):
        """清空歷史記錄"""
        self._save_history([])

    def _load_history(self) -> list[dict[str, Any]]:
        """載入歷史記錄"""
        try:
            with open(self.history_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_history(self, history: list[dict[str, Any]]):
        """保存歷史記錄"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # 寫入失敗不應該中斷程序
            print(f"Warning: Failed to save history: {e}")

    def format_entry_summary(self, entry: SyncHistoryEntry) -> str:
        """
        格式化單條記錄摘要

        Args:
            entry: 歷史記錄項

        Returns:
            格式化的摘要文字
        """
        timestamp = datetime.fromisoformat(entry.timestamp)
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        status = "✓ 成功" if entry.success else "✗ 失敗"
        status_color = "green" if entry.success else "red"

        changes_count = sum(len(c) for c in entry.changes.values())

        lines = [
            f"[{status_color}]{status}[/{status_color}] - {time_str}",
            f"  策略: {entry.strategy}",
            f"  變更: {changes_count} 項",
        ]

        if entry.warnings:
            lines.append(f"  警告: {len(entry.warnings)} 項")

        if entry.errors:
            lines.append(f"  錯誤: {len(entry.errors)} 項")

        if entry.duration_seconds:
            lines.append(f"  耗時: {entry.duration_seconds:.2f} 秒")

        if entry.backup_path:
            lines.append(f"  備份: {Path(entry.backup_path).name}")

        return "\n".join(lines)


# 全局歷史管理器實例
_history_manager: SyncHistoryManager | None = None


def get_history_manager() -> SyncHistoryManager:
    """
    獲取全局歷史管理器實例

    Returns:
        SyncHistoryManager 實例
    """
    global _history_manager
    if _history_manager is None:
        _history_manager = SyncHistoryManager()
    return _history_manager
