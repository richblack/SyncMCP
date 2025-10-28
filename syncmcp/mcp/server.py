"""
SyncMCP MCP Server - 讓 LLM 可以管理 MCP 配置同步

使用 MCP (Model Context Protocol) 讓 AI 助手能夠:
- 同步 MCP 配置
- 檢查同步狀態
- 查看配置差異
- 獲取衝突解決建議
"""

import asyncio
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from syncmcp.core.backup_manager import BackupManager
from syncmcp.core.config_manager import ConfigManager
from syncmcp.core.diff_engine import DiffEngine
from syncmcp.core.sync_engine import SyncEngine, SyncStrategy
from syncmcp.utils import get_logger

# 創建 MCP Server 實例
server = Server("syncmcp")
logger = get_logger(verbose=False)


# ============================================================================
# Tool Definitions
# ============================================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="sync_mcp_configs",
            description=(
                "同步所有客戶端的 MCP 配置。"
                "支援自動模式（選擇最新配置）或 dry-run 模式（預覽變更）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "enum": ["auto", "manual"],
                        "default": "auto",
                        "description": "同步策略：auto（自動選擇最新）或 manual（需手動選擇）",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "default": False,
                        "description": "是否只預覽變更而不實際執行",
                    },
                    "create_backup": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否在同步前創建備份",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="check_sync_status",
            description=(
                "檢查所有客戶端的配置狀態。"
                "顯示每個客戶端的配置文件位置、MCP 數量、最後修改時間等信息。"
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="show_config_diff",
            description=(
                "顯示所有客戶端之間的配置差異。"
                "使用 Markdown 格式化輸出，標示新增、刪除、修改的 MCP。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source_client": {
                        "type": "string",
                        "description": "指定作為參考的源客戶端（可選，默認自動選擇最新）",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="suggest_conflict_resolution",
            description=(
                "分析配置差異並提供智能的衝突解決建議。"
                "針對每個差異項目，提供具體的解決方案和理由。"
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


# ============================================================================
# Tool Implementations
# ============================================================================


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """處理工具調用"""

    try:
        if name == "sync_mcp_configs":
            return await _sync_mcp_configs(arguments)
        elif name == "check_sync_status":
            return await _check_sync_status(arguments)
        elif name == "show_config_diff":
            return await _show_config_diff(arguments)
        elif name == "suggest_conflict_resolution":
            return await _suggest_conflict_resolution(arguments)
        else:
            return [TextContent(type="text", text=f"❌ 未知的工具: {name}")]

    except Exception as e:
        logger.exception(f"工具 {name} 執行失敗")
        return [
            TextContent(
                type="text", text=f"❌ 執行失敗: {str(e)}\n\n請檢查配置文件是否存在且格式正確。"
            )
        ]


async def _sync_mcp_configs(arguments: dict) -> list[TextContent]:
    """執行配置同步"""

    strategy_str = arguments.get("strategy", "auto")
    dry_run = arguments.get("dry_run", False)
    create_backup = arguments.get("create_backup", True)

    # 轉換策略
    strategy = SyncStrategy.AUTO if strategy_str == "auto" else SyncStrategy.MANUAL

    # 創建管理器
    config_manager = ConfigManager()
    diff_engine = DiffEngine()
    backup_manager = BackupManager()
    sync_engine = SyncEngine(config_manager, diff_engine, backup_manager)

    # 執行同步
    result = sync_engine.sync(strategy=strategy, dry_run=dry_run, create_backup=create_backup)

    # 格式化結果
    output_lines = []

    if dry_run:
        output_lines.append("# 🔍 Dry Run 結果預覽\n")
    else:
        output_lines.append("# ✅ 同步完成\n")

    output_lines.append(f"**策略**: {strategy.value}\n")

    # 變更摘要
    output_lines.append("## 📊 變更摘要\n")
    total_changes = sum(len(changes) for changes in result.changes.values())
    output_lines.append(f"- 總變更數: **{total_changes}**")

    for client, changes in result.changes.items():
        if changes:
            output_lines.append(f"- {client}: {len(changes)} 項變更")

    # 詳細變更
    if result.changes:
        output_lines.append("\n## 📝 詳細變更\n")
        for client, changes in result.changes.items():
            if changes:
                output_lines.append(f"### {client}\n")
                for change in changes:
                    output_lines.append(f"- {change}")
                output_lines.append("")

    # 警告
    if result.warnings:
        output_lines.append("## ⚠️ 警告\n")
        for warning in result.warnings:
            output_lines.append(f"- {warning}")
        output_lines.append("")

    # 備份信息
    if result.backup_path and not dry_run:
        backup_name = Path(result.backup_path).name
        output_lines.append("## 💾 備份已創建\n")
        output_lines.append(f"備份位置: `{backup_name}`")
        output_lines.append("如有問題可使用 CLI 恢復: `syncmcp restore`")

    return [TextContent(type="text", text="\n".join(output_lines))]


async def _check_sync_status(arguments: dict) -> list[TextContent]:
    """檢查配置狀態"""

    config_manager = ConfigManager()
    configs = config_manager.load_all()

    output_lines = []
    output_lines.append("# 📊 MCP 配置狀態\n")

    # 統計信息
    total_clients = len(configs)
    total_mcps = sum(len(config.mcpServers) for config in configs.values())

    output_lines.append(f"- 客戶端數量: **{total_clients}**")
    output_lines.append(f"- MCP 總數: **{total_mcps}**\n")

    # 各客戶端詳情
    output_lines.append("## 客戶端詳情\n")

    for client_name, config in configs.items():
        output_lines.append(f"### {client_name}\n")
        output_lines.append(f"- **配置文件**: `{config.file_path}`")
        output_lines.append(f"- **MCP 數量**: {len(config.mcpServers)}")

        # 檢查文件是否存在
        if Path(config.file_path).exists():
            mtime = Path(config.file_path).stat().st_mtime
            from datetime import datetime

            mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            output_lines.append(f"- **最後修改**: {mtime_str}")
            output_lines.append("- **狀態**: ✅ 正常")
        else:
            output_lines.append("- **狀態**: ❌ 文件不存在")

        # 列出 MCP
        if config.mcpServers:
            output_lines.append("\n**已配置的 MCP**:")
            for mcp_name, mcp_config in config.mcpServers.items():
                mcp_type = mcp_config.get("type", "unknown")
                output_lines.append(f"  - `{mcp_name}` ({mcp_type})")

        output_lines.append("")

    return [TextContent(type="text", text="\n".join(output_lines))]


async def _show_config_diff(arguments: dict) -> list[TextContent]:
    """顯示配置差異"""

    config_manager = ConfigManager()
    diff_engine = DiffEngine()

    configs = config_manager.load_all()

    if not configs:
        return [TextContent(type="text", text="❌ 沒有找到任何配置文件")]

    # 執行差異分析
    diff_report = diff_engine.analyze(configs)

    output_lines = []
    output_lines.append("# 🔍 配置差異分析\n")

    # 統計摘要
    output_lines.append("## 📊 差異統計\n")
    added = sum(
        1
        for client_items in diff_report.diffs.values()
        for item in client_items
        if item.status == "added"
    )
    removed = sum(
        1
        for client_items in diff_report.diffs.values()
        for item in client_items
        if item.status == "removed"
    )
    modified = sum(
        1
        for client_items in diff_report.diffs.values()
        for item in client_items
        if item.status == "modified"
    )

    output_lines.append(f"- 新增: **{added}** 項")
    output_lines.append(f"- 刪除: **{removed}** 項")
    output_lines.append(f"- 修改: **{modified}** 項\n")

    # 詳細差異 - 使用內建的 to_text() 方法
    if diff_report.diffs:
        output_lines.append("## 📝 詳細差異\n")
        output_lines.append("```")
        output_lines.append(diff_report.to_text())
        output_lines.append("```\n")
    else:
        output_lines.append("✅ 所有配置已同步，無差異\n")

    return [TextContent(type="text", text="\n".join(output_lines))]


async def _suggest_conflict_resolution(arguments: dict) -> list[TextContent]:
    """提供衝突解決建議"""

    config_manager = ConfigManager()
    diff_engine = DiffEngine()

    configs = config_manager.load_all()
    diff_report = diff_engine.analyze(configs)

    output_lines = []
    output_lines.append("# 💡 衝突解決建議\n")

    if not diff_report.diffs:
        output_lines.append("✅ 所有配置已同步，無需解決衝突。")
        return [TextContent(type="text", text="\n".join(output_lines))]

    # 統計各類差異
    added_items = []
    removed_items = []
    modified_items = []

    for client, items in diff_report.diffs.items():
        for item in items:
            if item.status == "added":
                added_items.append((client, item))
            elif item.status == "removed":
                removed_items.append((client, item))
            elif item.status == "modified":
                modified_items.append((client, item))

    if added_items:
        output_lines.append("## ➕ 新增的 MCP\n")
        output_lines.append("**建議**: 這些 MCP 在某些客戶端中是新的\n")
        for client, item in added_items[:5]:  # Show first 5
            output_lines.append(f"- **{item.name}** ({client})")
        if len(added_items) > 5:
            output_lines.append(f"  ... 以及其他 {len(added_items) - 5} 項\n")

    if removed_items:
        output_lines.append("\n## ➖ 已刪除的 MCP\n")
        output_lines.append("**建議**: 這些 MCP 在某些客戶端中已被移除\n")
        for client, item in removed_items[:5]:
            output_lines.append(f"- **{item.name}** ({client})")
        if len(removed_items) > 5:
            output_lines.append(f"  ... 以及其他 {len(removed_items) - 5} 項\n")

    if modified_items:
        output_lines.append("\n## ✏️ 配置不一致的 MCP\n")
        output_lines.append("**建議**: 這些 MCP 的配置在不同客戶端間不一致\n")
        for client, item in modified_items[:5]:
            output_lines.append(f"- **{item.name}** ({client})")
        if len(modified_items) > 5:
            output_lines.append(f"  ... 以及其他 {len(modified_items) - 5} 項\n")

    # 整體建議
    output_lines.append("\n## 🎯 推薦操作\n")
    output_lines.append("1. **先執行 dry-run 預覽**:")
    output_lines.append("   執行 `sync_mcp_configs` 並設定 `dry_run: true`\n")
    output_lines.append("2. **確認無誤後執行同步**:")
    output_lines.append("   執行 `sync_mcp_configs` 並設定 `strategy: auto`\n")
    output_lines.append("3. **如有問題可恢復備份**:")
    output_lines.append("   使用 CLI: `syncmcp restore`")

    return [TextContent(type="text", text="\n".join(output_lines))]


# ============================================================================
# Main Entry Point
# ============================================================================


async def main():
    """啟動 MCP Server"""

    # 使用 STDIO transport
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        logger.info("SyncMCP MCP Server 已啟動")
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
