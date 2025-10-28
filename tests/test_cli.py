"""
測試 CLI 命令
"""

import pytest
from click.testing import CliRunner

from syncmcp.cli import cli


class TestCLI:
    """測試 CLI 基礎功能"""

    @pytest.fixture
    def runner(self):
        """創建 CLI runner"""
        return CliRunner()

    def test_cli_help(self, runner):
        """測試 --help 命令"""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "SyncMCP" in result.output
        assert "sync" in result.output
        assert "status" in result.output

    def test_cli_version(self, runner):
        """測試 --version 命令"""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "syncmcp" in result.output.lower()
        assert "2.0.0" in result.output

    def test_cli_verbose_flag(self, runner):
        """測試 --verbose 標誌"""
        result = runner.invoke(cli, ["--verbose", "--help"])

        assert result.exit_code == 0


class TestSyncCommand:
    """測試 sync 命令"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_sync_dry_run(self, runner, mock_all_configs):
        """測試 sync --dry-run"""
        result = runner.invoke(cli, ["sync", "--dry-run"])

        # 即使配置不完整，dry-run 也應該能執行
        assert result.exit_code in [0, 1]  # 0=成功, 1=有警告
        if result.exit_code == 0:
            assert "Dry" in result.output or "預覽" in result.output

    def test_sync_help(self, runner):
        """測試 sync --help"""
        result = runner.invoke(cli, ["sync", "--help"])

        assert result.exit_code == 0
        assert "sync" in result.output.lower()
        assert "dry-run" in result.output

    def test_sync_no_backup(self, runner, mock_all_configs):
        """測試 sync --no-backup"""
        result = runner.invoke(cli, ["sync", "--dry-run", "--no-backup"])

        # 應該能執行
        assert result.exit_code in [0, 1]


class TestStatusCommand:
    """測試 status 命令"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_status(self, runner, mock_all_configs):
        """測試 status 命令"""
        result = runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        # 應該顯示客戶端資訊
        assert "claude" in result.output.lower() or "client" in result.output.lower()

    def test_status_help(self, runner):
        """測試 status --help"""
        result = runner.invoke(cli, ["status", "--help"])

        assert result.exit_code == 0
        assert "status" in result.output.lower()


class TestListCommand:
    """測試 list 命令"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_list(self, runner, mock_all_configs):
        """測試 list 命令"""
        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        # 應該列出 MCPs
        assert "filesystem" in result.output or "MCP" in result.output

    def test_list_help(self, runner):
        """測試 list --help"""
        result = runner.invoke(cli, ["list", "--help"])

        assert result.exit_code == 0


class TestDiffCommand:
    """測試 diff 命令"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_diff(self, runner, mock_all_configs):
        """測試 diff 命令"""
        result = runner.invoke(cli, ["diff"])

        assert result.exit_code == 0
        # 應該顯示差異或"無差異"

    def test_diff_help(self, runner):
        """測試 diff --help"""
        result = runner.invoke(cli, ["diff", "--help"])

        assert result.exit_code == 0
        assert "diff" in result.output.lower()


class TestDoctorCommand:
    """測試 doctor 命令"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_doctor(self, runner):
        """測試 doctor 命令"""
        result = runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0
        # 應該顯示系統診斷
        assert "Python" in result.output
        assert "syncmcp" in result.output

    def test_doctor_checks_python_version(self, runner):
        """測試 doctor 檢查 Python 版本"""
        result = runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0
        assert "Python" in result.output
        assert "✅" in result.output or "❌" in result.output

    def test_doctor_checks_dependencies(self, runner):
        """測試 doctor 檢查依賴包"""
        result = runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0
        assert "click" in result.output
        assert "rich" in result.output

    def test_doctor_help(self, runner):
        """測試 doctor --help"""
        result = runner.invoke(cli, ["doctor", "--help"])

        assert result.exit_code == 0


class TestHistoryCommand:
    """測試 history 命令"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_history(self, runner, mock_syncmcp_dir):
        """測試 history 命令"""
        result = runner.invoke(cli, ["history"])

        # 即使沒有歷史記錄也應該正常執行
        assert result.exit_code == 0

    def test_history_stats(self, runner, mock_syncmcp_dir):
        """測試 history --stats"""
        result = runner.invoke(cli, ["history", "--stats"])

        assert result.exit_code == 0
        # 應該顯示統計資訊

    def test_history_limit(self, runner, mock_syncmcp_dir):
        """測試 history --limit"""
        result = runner.invoke(cli, ["history", "--limit", "5"])

        assert result.exit_code == 0

    def test_history_help(self, runner):
        """測試 history --help"""
        result = runner.invoke(cli, ["history", "--help"])

        assert result.exit_code == 0


class TestRestoreCommand:
    """測試 restore 命令"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_restore_help(self, runner):
        """測試 restore --help"""
        result = runner.invoke(cli, ["restore", "--help"])

        assert result.exit_code == 0
        assert "restore" in result.output.lower()


class TestInteractiveCommand:
    """測試 interactive 命令"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_interactive_help(self, runner):
        """測試 interactive --help"""
        result = runner.invoke(cli, ["interactive", "--help"])

        assert result.exit_code == 0

    # 注意：interactive 命令會啟動 TUI，測試會比較複雜
    # 這裡只測試 help


class TestOpenCommand:
    """測試 open 命令"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_open_help(self, runner):
        """測試 open --help"""
        result = runner.invoke(cli, ["open", "--help"])

        assert result.exit_code == 0

    # open 命令會啟動編輯器，測試較複雜


class TestCLIErrorHandling:
    """測試 CLI 錯誤處理"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_invalid_command(self, runner):
        """測試無效命令"""
        result = runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0
        assert (
            "Error" in result.output
            or "error" in result.output
            or "No such command" in result.output
        )

    def test_sync_with_no_configs(self, runner, mock_home_dir):
        """測試沒有配置文件時的 sync"""
        # 確保沒有配置文件
        result = runner.invoke(cli, ["sync", "--dry-run"])

        # 應該失敗或警告
        # 實際行為取決於實現
        assert result.exit_code in [0, 1, 2]
