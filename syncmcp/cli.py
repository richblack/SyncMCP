"""
SyncMCP CLI 命令列介面

使用 Click 實現的命令列工具
"""

from datetime import datetime

import click
from rich.console import Console
from rich.table import Table

from syncmcp.core.backup_manager import BackupManager
from syncmcp.core.config_manager import ConfigManager
from syncmcp.core.diff_engine import DiffEngine
from syncmcp.core.sync_engine import SyncEngine, SyncStrategy
from syncmcp.utils import get_history_manager, set_verbose

console = Console()


@click.group()
@click.version_option(version="2.0.0-dev", prog_name="syncmcp")
@click.option("--verbose", "-v", is_flag=True, help="顯示詳細日誌")
@click.pass_context
def cli(ctx, verbose):
    """SyncMCP - 智能 MCP 配置同步工具"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    # 設定全局 logger verbose 級別
    set_verbose(verbose)


@cli.command()
@click.option("--auto", is_flag=True, default=True, help="自動選擇最新配置")
@click.option("--dry-run", is_flag=True, help="預覽變更但不執行")
@click.option("--backup/--no-backup", default=True, help="是否備份")
@click.pass_context
def sync(ctx, auto, dry_run, backup):
    """執行 MCP 配置同步"""
    verbose = ctx.obj.get("verbose", False)

    # 初始化元件
    config_manager = ConfigManager()
    diff_engine = DiffEngine()
    backup_manager = BackupManager()
    sync_engine = SyncEngine(config_manager, diff_engine, backup_manager, verbose=verbose)

    try:
        # 執行同步
        with console.status("[bold green]分析配置..."):
            result = sync_engine.sync(
                strategy=SyncStrategy.AUTO, dry_run=dry_run, create_backup=backup
            )

        # 顯示結果
        if result.warnings:
            console.print("\n[bold yellow]⚠️  警告:")
            for warning in result.warnings:
                console.print(f"  {warning}")

        if result.changes:
            console.print("\n[bold cyan]📋 變更摘要:")
            for client, changes in result.changes.items():
                console.print(f"\n  [cyan]{client}:[/cyan]")
                for change in changes:
                    if change.startswith("+"):
                        console.print(f"    [green]{change}[/green]")
                    elif change.startswith("-"):
                        console.print(f"    [red]{change}[/red]")
                    elif change.startswith("~"):
                        console.print(f"    [yellow]{change}[/yellow]")

        if dry_run:
            console.print("\n[bold blue]ℹ️  這是預覽模式，未執行實際同步")
            console.print("   移除 --dry-run 參數以執行同步")
        elif result.success:
            console.print("\n[bold green]✅ 同步完成!")
            if result.backup_path:
                console.print(f"[dim]備份保存於: {result.backup_path}[/dim]")
        else:
            console.print("\n[bold red]❌ 同步失敗!")
            for error in result.errors:
                console.print(f"  [red]{error}[/red]")

    except Exception as e:
        console.print(f"[bold red]❌ 錯誤: {e}[/bold red]")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")


@cli.command()
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
def status(format):
    """顯示所有客戶端的配置狀態"""
    config_manager = ConfigManager()
    configs = config_manager.load_all()

    if format == "table":
        table = Table(title="MCP 配置狀態")
        table.add_column("客戶端", style="cyan")
        table.add_column("配置路徑", style="white")
        table.add_column("MCP 數量", style="green")
        table.add_column("最後修改", style="yellow")
        table.add_column("狀態", style="magenta")

        for name, config in configs.items():
            mcp_count = len(config.mcpServers)
            last_modified = (
                datetime.fromtimestamp(config.last_modified).strftime("%Y-%m-%d %H:%M:%S")
                if config.last_modified
                else "N/A"
            )
            status_icon = "✅" if config.file_path.exists() else "❌"

            table.add_row(name, str(config.file_path), str(mcp_count), last_modified, status_icon)

        console.print(table)
    else:
        import json

        status_data = {}
        for name, config in configs.items():
            status_data[name] = {
                "path": str(config.file_path),
                "mcp_count": len(config.mcpServers),
                "last_modified": config.last_modified,
                "exists": config.file_path.exists(),
            }
        console.print(json.dumps(status_data, indent=2))


@cli.command()
@click.argument("client", required=False)
def list(client):
    """列出配置文件路徑和 MCP 列表"""
    config_manager = ConfigManager()
    configs = config_manager.load_all()

    if client:
        # 顯示特定客戶端
        if client not in configs:
            console.print(f"[red]❌ 未知的客戶端: {client}[/red]")
            return

        config = configs[client]
        console.print(f"\n[bold cyan]{client}[/bold cyan]")
        console.print(f"路徑: {config.file_path}")
        console.print(f"MCP 數量: {len(config.mcpServers)}\n")

        if config.mcpServers:
            for name, server in config.mcpServers.items():
                console.print(f"  • [green]{name}[/green]")
                console.print(f"    command: {server.get('command', 'N/A')}")
                if "args" in server:
                    console.print(f"    args: {server['args']}")
        else:
            console.print("  [dim]無 MCP 配置[/dim]")
    else:
        # 顯示所有客戶端
        for name, config in configs.items():
            console.print(f"\n[bold cyan]{name}[/bold cyan]")
            console.print(f"路徑: {config.file_path}")
            console.print(f"MCP 數量: {len(config.mcpServers)}")
            if config.mcpServers:
                console.print("MCP 列表:")
                for mcp_name in config.mcpServers.keys():
                    console.print(f"  • {mcp_name}")


@cli.command()
@click.argument(
    "client", type=click.Choice(["claude-code", "roo-code", "claude-desktop", "gemini"])
)
def open(client):
    """在編輯器中打開配置文件"""
    console.print("[yellow]⚠️  open 命令尚未實作[/yellow]")


@cli.command()
def diff():
    """顯示同步前後的差異"""
    config_manager = ConfigManager()
    diff_engine = DiffEngine()

    configs = config_manager.load_all()
    diff_report = diff_engine.analyze(configs)

    console.print("\n[bold cyan]📊 配置差異分析[/bold cyan]\n")

    text_report = diff_report.to_text()
    if text_report == "無差異":
        console.print("[green]✅ 所有客戶端配置一致，無需同步[/green]")
    else:
        console.print(text_report)

        # 顯示警告
        if diff_report.has_removals():
            console.print("\n[bold yellow]⚠️  警告: 檢測到配置將被移除[/bold yellow]")
            console.print("   執行同步前請確認這是預期的行為")


@cli.command()
@click.argument("backup_id", required=False)
def restore(backup_id):
    """從備份恢復配置"""
    console.print("[yellow]⚠️  restore 命令尚未實作[/yellow]")


@cli.command()
@click.option("--limit", default=10, help="顯示記錄數量")
@click.option("--stats", is_flag=True, help="顯示統計信息")
def history(limit, stats):
    """查看同步歷史記錄"""
    history_manager = get_history_manager()

    if stats:
        # 顯示統計信息
        statistics = history_manager.get_statistics()
        console.print("\n[bold cyan]📊 同步統計信息[/bold cyan]\n")

        table = Table(show_header=False, box=None)
        table.add_column("項目", style="cyan")
        table.add_column("數值", style="white")

        table.add_row("總同步次數", str(statistics["total_syncs"]))
        table.add_row("成功次數", f"[green]{statistics['successful_syncs']}[/green]")
        table.add_row("失敗次數", f"[red]{statistics['failed_syncs']}[/red]")
        table.add_row("成功率", f"{statistics['success_rate']:.1f}%")
        table.add_row("總變更數", str(statistics["total_changes"]))
        table.add_row("總警告數", str(statistics["total_warnings"]))
        table.add_row("總錯誤數", str(statistics["total_errors"]))

        console.print(table)
        console.print()
    else:
        # 顯示歷史記錄
        entries = history_manager.get_history(limit=limit)

        if not entries:
            console.print("[yellow]沒有同步歷史記錄[/yellow]")
            return

        console.print(f"\n[bold cyan]📜 最近 {len(entries)} 次同步記錄[/bold cyan]\n")

        for entry in entries:
            timestamp = datetime.fromisoformat(entry.timestamp)
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            # 狀態圖示和顏色
            if entry.success:
                status = "[green]✓ 成功[/green]"
            else:
                status = "[red]✗ 失敗[/red]"

            console.print(f"{status} - {time_str}")
            console.print(f"  策略: {entry.strategy}")

            # 變更數
            changes_count = sum(len(c) for c in entry.changes.values())
            if changes_count > 0:
                console.print(f"  變更: {changes_count} 項")

            # 警告
            if entry.warnings:
                console.print(f"  [yellow]警告: {len(entry.warnings)} 項[/yellow]")

            # 錯誤
            if entry.errors:
                console.print(f"  [red]錯誤: {len(entry.errors)} 項[/red]")
                for error in entry.errors[:2]:  # 只顯示前兩個錯誤
                    console.print(f"    - {error}")

            # 耗時
            if entry.duration_seconds:
                console.print(f"  耗時: {entry.duration_seconds:.2f} 秒")

            # 備份
            if entry.backup_path:
                from pathlib import Path

                backup_name = Path(entry.backup_path).name
                console.print(f"  備份: {backup_name}")

            console.print()  # 空行分隔


@cli.command()
def interactive():
    """啟動互動式介面（TUI）"""
    from syncmcp.tui import main as tui_main

    tui_main()


@cli.command()
def doctor():
    """診斷系統環境和安裝狀態"""
    import importlib.metadata
    import shutil
    import sys
    from pathlib import Path

    console.print("\n[bold cyan]🔍 SyncMCP 系統診斷[/bold cyan]\n")

    all_ok = True

    # 1. Python 版本檢查
    console.print("[bold]1. Python 版本[/bold]")
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        console.print(f"  ✅ Python {py_version} (需要 >= 3.10)")
    else:
        console.print(f"  ❌ Python {py_version} (需要 >= 3.10)")
        all_ok = False
    console.print(f"  📍 位置: {sys.executable}\n")

    # 2. syncmcp 命令檢查
    console.print("[bold]2. syncmcp 命令[/bold]")
    syncmcp_path = shutil.which("syncmcp")
    if syncmcp_path:
        console.print("  ✅ 在 PATH 中")
        console.print(f"  📍 位置: {syncmcp_path}")
    else:
        console.print("  ⚠️  不在 PATH 中")
        console.print("  💡 建議:")
        console.print("     1. 執行: pip install -e . (開發模式)")
        console.print("     2. 或將以下路徑加入 PATH:")

        # 找到可能的安裝路徑
        site_packages = (
            Path(sys.executable).parent.parent
            / "lib"
            / f"python{sys.version_info.major}.{sys.version_info.minor}"
            / "site-packages"
        )
        console.print(f"        {Path(sys.executable).parent}")
        all_ok = False
    console.print()

    # 3. 依賴包檢查
    console.print("[bold]3. 依賴包[/bold]")
    required_packages = {
        "click": ">=8.1.0",
        "rich": ">=13.0.0",
        "InquirerPy": ">=0.3.4",
    }

    for package, version_req in required_packages.items():
        try:
            version = importlib.metadata.version(package)
            console.print(f"  ✅ {package} {version} {version_req}")
        except importlib.metadata.PackageNotFoundError:
            console.print(f"  ❌ {package} 未安裝 {version_req}")
            all_ok = False
    console.print()

    # 4. MCP 包檢查（可選）
    console.print("[bold]4. MCP Server 支援（可選）[/bold]")
    try:
        mcp_version = importlib.metadata.version("mcp")
        console.print(f"  ✅ mcp {mcp_version}")
    except importlib.metadata.PackageNotFoundError:
        console.print("  ⚠️  mcp 未安裝（MCP Server 功能將不可用）")
        console.print("  💡 安裝: pip install mcp")
    console.print()

    # 5. 配置文件檢查
    console.print("[bold]5. 配置文件[/bold]")
    config_paths = {
        "Claude Code (全域)": Path.home() / ".claude.json",
        "Claude Desktop": Path.home()
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json",
        "Roo Code": Path.home() / ".roo-code" / "settings.json",
        "Gemini": Path.home() / ".gemini" / "config.json",
    }

    found_configs = 0
    for name, path in config_paths.items():
        if path.exists():
            console.print(f"  ✅ {name}")
            console.print(f"     {path}")
            found_configs += 1
        else:
            console.print(f"  ⚪ {name} (未找到)")

    if found_configs == 0:
        console.print("\n  ⚠️  未找到任何配置文件")
        console.print("  💡 至少需要配置一個客戶端才能使用同步功能")
    console.print()

    # 6. SyncMCP 目錄檢查
    console.print("[bold]6. SyncMCP 目錄[/bold]")
    syncmcp_dir = Path.home() / ".syncmcp"
    if syncmcp_dir.exists():
        console.print(f"  ✅ {syncmcp_dir}")

        # 檢查子目錄
        subdirs = {
            "logs": syncmcp_dir / "logs",
            "backups": syncmcp_dir / "backups",
        }
        for name, path in subdirs.items():
            if path.exists():
                console.print(f"     ✅ {name}/")
            else:
                console.print(f"     ⚪ {name}/ (將在首次使用時創建)")
    else:
        console.print(f"  ⚪ {syncmcp_dir} (將在首次使用時創建)")
    console.print()

    # 7. 總結
    console.print("[bold]7. 診斷總結[/bold]")
    if all_ok and found_configs > 0:
        console.print("  ✅ [bold green]系統狀態良好，可以正常使用！[/bold green]")
    elif all_ok and found_configs == 0:
        console.print("  ⚠️  [bold yellow]系統已就緒，但需要配置至少一個客戶端[/bold yellow]")
    else:
        console.print("  ❌ [bold red]發現問題，請按照上述建議修復[/bold red]")
    console.print()


if __name__ == "__main__":
    cli()
