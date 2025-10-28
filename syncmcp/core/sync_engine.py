"""
同步引擎 - 協調配置同步操作
"""

import time
from dataclasses import dataclass
from enum import Enum

from ..utils import get_history_manager, get_logger


class SyncStrategy(Enum):
    """同步策略"""

    AUTO = "auto"  # 自動選擇最新
    MANUAL = "manual"  # 手動選擇來源


@dataclass
class SyncResult:
    """同步結果"""

    success: bool
    changes: dict[str, list[str]]  # client -> [changes]
    warnings: list[str]
    errors: list[str]
    backup_path: str | None


class SyncEngine:
    """核心同步引擎"""

    def __init__(self, config_manager, diff_engine, backup_manager, verbose: bool = False):
        self.config_manager = config_manager
        self.diff_engine = diff_engine
        self.backup_manager = backup_manager
        self.logger = get_logger(verbose=verbose)
        self.history = get_history_manager()

    def sync(
        self,
        strategy: SyncStrategy = SyncStrategy.AUTO,
        dry_run: bool = False,
        create_backup: bool = True,
    ) -> SyncResult:
        """執行同步操作"""
        start_time = time.time()
        backup_path = None

        try:
            self.logger.info(f"開始同步 (strategy={strategy.value}, dry_run={dry_run})")

            # 1. 載入所有客戶端配置
            self.logger.debug("載入客戶端配置...")
            configs = self.config_manager.load_all()
            self.logger.info(f"載入了 {len(configs)} 個客戶端配置")

            # 2. 分析差異
            self.logger.debug("分析配置差異...")
            diff_report = self.diff_engine.analyze(configs)

            # 3. 檢測警告（配置丟失等）
            warnings = self._detect_warnings(diff_report)
            for warning in warnings:
                self.logger.warning(warning)

            # 4. 準備變更摘要
            changes = self._prepare_changes(diff_report)
            total_changes = sum(len(c) for c in changes.values())
            self.logger.info(f"檢測到 {total_changes} 個變更")

            # 5. 如果是 dry-run，返回預覽
            if dry_run:
                self.logger.info("Dry-run 模式，不執行實際同步")
                return SyncResult(
                    success=True, changes=changes, warnings=warnings, errors=[], backup_path=None
                )

            # 6. 創建備份
            if create_backup:
                self.logger.info("創建備份...")
                backup_path = self.backup_manager.create_backup(configs)
                self.logger.info(f"備份已創建: {backup_path}")

            # 7. 執行同步
            self.logger.info("執行配置同步...")
            source = self._select_source(configs)
            if source:
                self.logger.debug(f"使用 {source.client_name} 作為源配置")
                self.config_manager.sync_all(source)
                self.logger.info("同步完成")
            else:
                self.logger.warning("未找到可用的源配置")

            # 8. 記錄歷史
            duration = time.time() - start_time
            self.history.add_entry(
                success=True,
                strategy=strategy.value,
                changes=changes,
                warnings=warnings,
                errors=[],
                backup_path=backup_path,
                duration_seconds=duration,
            )
            self.logger.info(f"同步成功 (耗時 {duration:.2f}秒)")

            return SyncResult(
                success=True, changes=changes, warnings=warnings, errors=[], backup_path=backup_path
            )

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"同步失敗: {e}")
            self.logger.exception("詳細錯誤信息")

            # 失敗時恢復
            if backup_path and not dry_run:
                try:
                    self.logger.info("嘗試從備份恢復...")
                    self.backup_manager.restore(backup_path, self.config_manager.adapters)
                    self.logger.info("已從備份恢復")
                except Exception as restore_error:
                    self.logger.error(f"恢復失敗: {restore_error}")

            # 記錄失敗歷史
            self.history.add_entry(
                success=False,
                strategy=strategy.value,
                changes={},
                warnings=warnings if "warnings" in locals() else [],
                errors=[str(e)],
                backup_path=backup_path,
                duration_seconds=duration,
            )

            return SyncResult(
                success=False, changes={}, warnings=[], errors=[str(e)], backup_path=backup_path
            )

    def _detect_warnings(self, diff_report) -> list[str]:
        """檢測潛在問題"""
        warnings = []

        # 檢測配置丟失
        if diff_report.has_removals():
            for client, items in diff_report.diffs.items():
                removal_count = diff_report.get_removal_count(client)
                if removal_count > 0:
                    removed_names = [item.name for item in items if item.status == "removed"]
                    warnings.append(
                        f"⚠️  {client} 將失去 {removal_count} 個 MCP 配置: {', '.join(removed_names)}"
                    )

        return warnings

    def _prepare_changes(self, diff_report) -> dict[str, list[str]]:
        """準備變更摘要"""
        changes = {}
        for client, items in diff_report.diffs.items():
            client_changes = []
            for item in items:
                if item.status == "added":
                    client_changes.append(f"+ {item.name}")
                elif item.status == "removed":
                    client_changes.append(f"- {item.name}")
                elif item.status == "modified":
                    client_changes.append(f"~ {item.name}")
            if client_changes:
                changes[client] = client_changes
        return changes

    def _select_source(self, configs):
        """選擇源配置"""
        latest = None
        for config in configs.values():
            if config.last_modified:
                if not latest or config.last_modified > latest.last_modified:
                    latest = config
        return latest
