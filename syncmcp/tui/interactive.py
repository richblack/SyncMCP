"""
Terminal 互動式介面 (TUI)
使用 InquirerPy 和 Rich 提供友善的使用者體驗
"""

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

from ..core.backup_manager import BackupManager
from ..core.config_manager import ConfigManager
from ..core.diff_engine import DiffEngine
from ..core.sync_engine import SyncEngine, SyncStrategy


class SyncMCPTUI:
    """互動式 Terminal UI"""

    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager()
        self.backup_manager = BackupManager()
        self.diff_engine = DiffEngine()
        self.sync_engine = SyncEngine(self.config_manager, self.diff_engine, self.backup_manager)

    def show_welcome(self):
        """顯示歡迎訊息"""
        welcome_text = Text()
        welcome_text.append("SyncMCP ", style="bold cyan")
        welcome_text.append("- MCP 配置同步工具\n", style="bold white")
        welcome_text.append("智能化管理多個 AI 客戶端的 MCP 配置", style="dim")

        panel = Panel(welcome_text, border_style="cyan", box=box.ROUNDED)
        self.console.print("\n")
        self.console.print(panel)
        self.console.print()

    def show_main_menu(self) -> str:
        """顯示主選單並返回用戶選擇"""
        choices = [
            Choice(value="sync", name="🔄 同步配置"),
            Choice(value="status", name="📊 查看狀態"),
            Choice(value="diff", name="🔍 查看差異"),
            Choice(value="history", name="📜 同步歷史"),
            Choice(value="restore", name="⏮️  恢復備份"),
            Separator(),
            Choice(value="exit", name="❌ 退出"),
        ]

        action = inquirer.select(
            message="請選擇操作:", choices=choices, default="sync", pointer="❯"
        ).execute()

        return action

    def run_sync_flow(self):
        """執行互動式同步流程"""
        self.console.print("\n[bold cyan]🔄 同步配置[/bold cyan]\n")

        # 1. 先執行 dry-run 顯示差異
        self.console.print("[dim]正在分析配置差異...[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("載入配置...", total=None)
            dry_run_result = self.sync_engine.sync(dry_run=True, create_backup=False)
            progress.update(task, completed=True)

        # 2. 顯示變更預覽
        if dry_run_result.changes:
            self.console.print("\n[bold yellow]📋 將執行以下變更:[/bold yellow]\n")
            self._display_changes(dry_run_result.changes)
        else:
            self.console.print("[green]✓ 所有客戶端配置已同步，無需變更[/green]")
            return

        # 3. 顯示警告
        if dry_run_result.warnings:
            self.console.print("\n[bold yellow]⚠️  警告:[/bold yellow]")
            for warning in dry_run_result.warnings:
                self.console.print(f"  {warning}")

        # 4. 詢問確認
        self.console.print()
        confirm = inquirer.confirm(message="確定要執行同步嗎？", default=True).execute()

        if not confirm:
            self.console.print("[yellow]已取消同步[/yellow]")
            return

        # 5. 執行實際同步
        self.console.print("\n[dim]正在同步配置...[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("同步中...", total=100)

            # 模擬進度（實際上 sync_engine 應該提供進度回調）
            for i in range(0, 100, 20):
                progress.update(task, completed=i)

            # 執行同步
            result = self.sync_engine.sync(
                strategy=SyncStrategy.AUTO, dry_run=False, create_backup=True
            )

            progress.update(task, completed=100)

        # 6. 顯示結果
        self.console.print()
        if result.success:
            self.console.print("[bold green]✓ 同步成功！[/bold green]\n")

            if result.backup_path:
                self.console.print(f"[dim]備份已保存: {result.backup_path}[/dim]")

            if result.changes:
                self._display_changes(result.changes)
        else:
            self.console.print("[bold red]✗ 同步失敗[/bold red]\n")
            if result.errors:
                for error in result.errors:
                    self.console.print(f"[red]  • {error}[/red]")

        self._wait_for_continue()

    def show_status(self):
        """顯示配置狀態"""
        self.console.print("\n[bold cyan]📊 配置狀態[/bold cyan]\n")

        # 載入所有客戶端配置
        configs = self.config_manager.load_all()

        # 創建狀態表格
        table = Table(
            title="MCP 客戶端配置狀態", box=box.ROUNDED, show_header=True, header_style="bold cyan"
        )

        table.add_column("客戶端", style="cyan", no_wrap=True)
        table.add_column("配置文件", style="dim")
        table.add_column("MCP 數量", justify="center")
        table.add_column("狀態", justify="center")
        table.add_column("最後修改", style="dim")

        for name, config in configs.items():
            # 檢查配置文件是否存在
            exists = config.file_path.exists()
            status = "✓" if exists else "✗"
            status_style = "green" if exists else "red"

            # MCP 數量
            mcp_count = len(config.mcpServers) if exists else 0

            # 最後修改時間
            if exists and config.last_modified:
                from datetime import datetime

                mod_time = datetime.fromtimestamp(config.last_modified)
                time_str = mod_time.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = "-"

            table.add_row(
                name,
                str(config.file_path),
                str(mcp_count),
                f"[{status_style}]{status}[/{status_style}]",
                time_str,
            )

        self.console.print(table)

        # 詢問是否查看詳細信息
        self.console.print()
        view_detail = inquirer.confirm(
            message="查看特定客戶端的 MCP 列表？", default=False
        ).execute()

        if view_detail:
            self._show_client_details(configs)
        else:
            self._wait_for_continue()

    def _show_client_details(self, configs):
        """顯示特定客戶端的詳細配置"""
        # 選擇客戶端
        choices = [
            Choice(value=name, name=f"{name} ({len(config.mcpServers)} MCPs)")
            for name, config in configs.items()
            if config.file_path.exists()
        ]

        if not choices:
            self.console.print("[yellow]沒有可用的配置[/yellow]")
            self._wait_for_continue()
            return

        client = inquirer.select(
            message="選擇客戶端:",
            choices=choices,
        ).execute()

        config = configs[client]

        # 顯示 MCP 列表
        self.console.print(f"\n[bold cyan]{client} 的 MCP 配置:[/bold cyan]\n")

        if not config.mcpServers:
            self.console.print("[dim]無 MCP 配置[/dim]")
        else:
            table = Table(box=box.SIMPLE)
            table.add_column("名稱", style="cyan")
            table.add_column("類型")
            table.add_column("配置", style="dim")

            for name, server_config in config.mcpServers.items():
                config_type = server_config.get("type", "stdio")

                # 簡化配置顯示
                if "command" in server_config:
                    detail = f"command: {server_config['command']}"
                elif "url" in server_config:
                    detail = f"url: {server_config['url']}"
                else:
                    detail = "-"

                table.add_row(name, config_type, detail)

            self.console.print(table)

        self._wait_for_continue()

    def show_diff(self):
        """顯示配置差異"""
        self.console.print("\n[bold cyan]🔍 配置差異分析[/bold cyan]\n")

        self.console.print("[dim]正在分析差異...[/dim]")

        dry_run_result = self.sync_engine.sync(dry_run=True, create_backup=False)

        if dry_run_result.changes:
            self._display_changes(dry_run_result.changes)
        else:
            self.console.print("[green]✓ 所有客戶端配置已同步[/green]")

        if dry_run_result.warnings:
            self.console.print("\n[bold yellow]⚠️  警告:[/bold yellow]")
            for warning in dry_run_result.warnings:
                self.console.print(f"  {warning}")

        self._wait_for_continue()

    def show_history(self):
        """顯示同步歷史"""
        self.console.print("\n[bold cyan]📜 同步歷史[/bold cyan]\n")
        self.console.print("[dim]此功能尚未實現[/dim]")
        self._wait_for_continue()

    def run_restore_flow(self):
        """執行恢復備份流程"""
        self.console.print("\n[bold cyan]⏮️  恢復備份[/bold cyan]\n")
        self.console.print("[dim]此功能尚未實現[/dim]")
        self._wait_for_continue()

    def _display_changes(self, changes: dict):
        """顯示變更摘要"""
        for client, change_list in changes.items():
            if not change_list:
                continue

            self.console.print(f"[bold]{client}:[/bold]")
            for change in change_list:
                if change.startswith("+"):
                    self.console.print(f"  [green]{change}[/green]")
                elif change.startswith("-"):
                    self.console.print(f"  [red]{change}[/red]")
                elif change.startswith("~"):
                    self.console.print(f"  [yellow]{change}[/yellow]")
                else:
                    self.console.print(f"  {change}")
            self.console.print()

    def _wait_for_continue(self):
        """等待用戶按任意鍵繼續"""
        self.console.print()
        inquirer.text(
            message="按 Enter 繼續...", default="", validate=lambda x: True, invalid_message=""
        ).execute()

    def run(self):
        """運行互動式介面主循環"""
        self.show_welcome()

        while True:
            action = self.show_main_menu()

            if action == "sync":
                self.run_sync_flow()
            elif action == "status":
                self.show_status()
            elif action == "diff":
                self.show_diff()
            elif action == "history":
                self.show_history()
            elif action == "restore":
                self.run_restore_flow()
            elif action == "exit":
                self.console.print("\n[cyan]感謝使用 SyncMCP！[/cyan]\n")
                break


def main():
    """TUI 入口點"""
    tui = SyncMCPTUI()
    try:
        tui.run()
    except KeyboardInterrupt:
        tui.console.print("\n\n[yellow]已取消操作[/yellow]\n")
    except Exception as e:
        tui.console.print(f"\n[bold red]錯誤: {e}[/bold red]\n")
        raise


if __name__ == "__main__":
    main()
