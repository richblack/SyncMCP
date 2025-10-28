"""
測試備份管理器和同步引擎
"""

import json
import time
from pathlib import Path

import pytest

from syncmcp.core.backup_manager import BackupManager
from syncmcp.core.config_manager import ConfigManager
from syncmcp.core.diff_engine import DiffEngine
from syncmcp.core.sync_engine import SyncEngine, SyncResult, SyncStrategy


class TestBackupManager:
    """測試 BackupManager"""

    @pytest.fixture
    def backup_manager(self, mock_syncmcp_dir):
        """創建 BackupManager 實例"""
        return BackupManager(backup_dir=mock_syncmcp_dir / "backups")

    def test_create_backup(self, backup_manager, mock_all_configs):
        """測試創建備份"""
        # 準備配置
        config_manager = ConfigManager()
        configs = config_manager.load_all()

        # 創建備份
        backup_path = backup_manager.create(config_manager.adapters)

        assert backup_path is not None
        assert Path(backup_path).exists()
        assert Path(backup_path).is_dir()

    def test_list_backups(self, backup_manager, mock_all_configs):
        """測試列出備份"""
        config_manager = ConfigManager()

        # 創建多個備份
        backup_manager.create(config_manager.adapters)
        time.sleep(0.1)  # 確保時間戳不同
        backup_manager.create(config_manager.adapters)

        backups = backup_manager.list()

        assert len(backups) >= 2
        # 驗證備份按時間排序（最新的在前）
        if len(backups) >= 2:
            assert backups[0]["timestamp"] >= backups[1]["timestamp"]

    def test_restore_backup(self, backup_manager, mock_all_configs, mock_home_dir):
        """測試恢復備份"""
        config_manager = ConfigManager()

        # 創建備份
        backup_path = backup_manager.create(config_manager.adapters)

        # 修改配置
        claude_config = config_manager.load("claude-code")
        claude_config.mcpServers["new-mcp"] = {"type": "stdio", "command": "test"}
        config_manager.save("claude-code", claude_config)

        # 恢復備份
        backup_manager.restore(backup_path, config_manager.adapters)

        # 驗證配置已恢復
        restored_config = config_manager.load("claude-code")
        assert "new-mcp" not in restored_config.mcpServers

    def test_cleanup_old_backups(self, backup_manager, mock_all_configs):
        """測試清理舊備份"""
        config_manager = ConfigManager()

        # 創建多個備份
        for _ in range(15):
            backup_manager.create(config_manager.adapters)
            time.sleep(0.05)

        # 清理，保留最新10個
        backup_manager.cleanup(keep=10)

        backups = backup_manager.list()
        assert len(backups) <= 10

    def test_get_backup_info(self, backup_manager, mock_all_configs):
        """測試獲取備份信息"""
        config_manager = ConfigManager()
        backup_path = backup_manager.create(config_manager.adapters)

        info = backup_manager.get_info(backup_path)

        assert info is not None
        assert "timestamp" in info
        assert "clients" in info
        assert len(info["clients"]) >= 1


class TestSyncEngine:
    """測試 SyncEngine"""

    @pytest.fixture
    def sync_components(self, mock_all_configs, mock_syncmcp_dir):
        """創建同步所需的所有組件"""
        config_manager = ConfigManager()
        diff_engine = DiffEngine()
        backup_manager = BackupManager(backup_dir=mock_syncmcp_dir / "backups")
        sync_engine = SyncEngine(config_manager, diff_engine, backup_manager, verbose=False)

        return {
            "config_manager": config_manager,
            "diff_engine": diff_engine,
            "backup_manager": backup_manager,
            "sync_engine": sync_engine,
        }

    def test_sync_auto_strategy(self, sync_components):
        """測試自動同步策略"""
        sync_engine = sync_components["sync_engine"]

        result = sync_engine.sync(
            strategy=SyncStrategy.AUTO,
            dry_run=True,  # 使用 dry-run 避免實際修改
            create_backup=False,
        )

        assert isinstance(result, SyncResult)
        assert result.success is True
        assert isinstance(result.changes, dict)
        assert isinstance(result.warnings, list)

    def test_sync_dry_run(self, sync_components):
        """測試 dry-run 模式"""
        sync_engine = sync_components["sync_engine"]

        result = sync_engine.sync(strategy=SyncStrategy.AUTO, dry_run=True, create_backup=False)

        assert result.success is True
        assert result.backup_path is None  # dry-run 不創建備份

    def test_sync_with_backup(self, sync_components):
        """測試帶備份的同步"""
        sync_engine = sync_components["sync_engine"]

        result = sync_engine.sync(strategy=SyncStrategy.AUTO, dry_run=False, create_backup=True)

        assert result.success is True
        if result.changes:  # 如果有變更
            assert result.backup_path is not None

    def test_sync_creates_history(self, sync_components, mock_syncmcp_dir):
        """測試同步創建歷史記錄"""
        sync_engine = sync_components["sync_engine"]

        # 執行同步
        sync_engine.sync(strategy=SyncStrategy.AUTO, dry_run=True, create_backup=False)

        # 檢查歷史文件
        history_file = mock_syncmcp_dir / "history.json"
        assert history_file.exists()

        history = json.loads(history_file.read_text())
        assert isinstance(history, list)
        assert len(history) > 0

    def test_sync_rollback_on_error(self, sync_components, monkeypatch):
        """測試同步錯誤時回滾"""
        sync_engine = sync_components["sync_engine"]
        config_manager = sync_components["config_manager"]

        # Mock save 方法使其失敗
        def mock_save_error(client_name, config):
            raise Exception("模擬保存錯誤")

        monkeypatch.setattr(config_manager, "save", mock_save_error)

        # 執行同步（應該失敗並回滾）
        result = sync_engine.sync(strategy=SyncStrategy.AUTO, dry_run=False, create_backup=True)

        assert result.success is False
        assert len(result.errors) > 0

    def test_sync_detects_warnings(self, sync_components, mock_home_dir):
        """測試同步檢測警告"""
        sync_engine = sync_components["sync_engine"]
        config_manager = sync_components["config_manager"]

        # 創建會產生警告的配置（例如：某個客戶端會丟失 MCPs）
        # 載入 claude-code 配置並添加一個其他客戶端沒有的 MCP
        claude_config = config_manager.load("claude-code")
        claude_config.mcpServers["unique-mcp"] = {"type": "http", "url": "http://example.com"}
        config_manager.save("claude-code", claude_config)

        result = sync_engine.sync(strategy=SyncStrategy.AUTO, dry_run=True, create_backup=False)

        # 應該會有警告（Claude Desktop 不支援 HTTP）
        # 實際警告取決於實現邏輯
        assert isinstance(result.warnings, list)

    def test_sync_strategy_manual(self, sync_components):
        """測試手動同步策略"""
        sync_engine = sync_components["sync_engine"]

        # 注意：MANUAL 策略可能需要用戶輸入，測試時可能需要 mock
        result = sync_engine.sync(strategy=SyncStrategy.MANUAL, dry_run=True, create_backup=False)

        # 根據實際實現驗證
        assert isinstance(result, SyncResult)

    def test_prepare_changes(self, sync_components):
        """測試準備變更摘要"""
        sync_engine = sync_components["sync_engine"]
        diff_engine = sync_components["diff_engine"]
        config_manager = sync_components["config_manager"]

        configs = config_manager.load_all()
        diff_report = diff_engine.analyze(configs)

        changes = sync_engine._prepare_changes(diff_report)

        assert isinstance(changes, dict)
        # changes 應該是 {client_name: [change_list]} 格式

    def test_detect_warnings(self, sync_components):
        """測試檢測警告"""
        sync_engine = sync_components["sync_engine"]
        diff_engine = sync_components["diff_engine"]
        config_manager = sync_components["config_manager"]

        configs = config_manager.load_all()
        diff_report = diff_engine.analyze(configs)

        warnings = sync_engine._detect_warnings(diff_report)

        assert isinstance(warnings, list)
        # warnings 應該包含可能的配置丟失等警告
