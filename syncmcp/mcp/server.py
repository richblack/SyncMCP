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
        Tool(
            name="get_setup_guide",
            description=(
                "獲取 MCP 設置完整指南。當需要設置新 MCP 或修復 MCP 問題時使用。"
                "包含全域 MCP、專案 MCP、各種安裝方式（npx/uvx/python）的詳細說明。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "enum": [
                            "全部",
                            "全域MCP",
                            "專案MCP",
                            "npx安裝",
                            "uvx安裝",
                            "python安裝",
                            "常見錯誤",
                            "測試驗證",
                        ],
                        "default": "全部",
                        "description": "要查看的指南章節",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="troubleshoot_mcp",
            description=(
                "診斷並提供 MCP 問題的解決方案。"
                "可以分析錯誤訊息、檢查配置、提供修復步驟。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "error_message": {
                        "type": "string",
                        "description": "錯誤訊息或問題描述",
                    },
                    "mcp_name": {
                        "type": "string",
                        "description": "有問題的 MCP 名稱（可選）",
                    },
                },
                "required": ["error_message"],
            },
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
        elif name == "get_setup_guide":
            return await _get_setup_guide(arguments)
        elif name == "troubleshoot_mcp":
            return await _troubleshoot_mcp(arguments)
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


async def _get_setup_guide(arguments: dict) -> list[TextContent]:
    """獲取 MCP 設置指南"""

    section = arguments.get("section", "全部")

    # 讀取指南檔案
    guide_path = Path(__file__).parent.parent.parent / "docs" / "MCP-SETUP-GUIDE.md"

    if not guide_path.exists():
        return [
            TextContent(
                type="text",
                text=(
                    "❌ 找不到設置指南文檔\n\n"
                    "請確認 SyncMCP 已正確安裝，或訪問 GitHub 查看：\n"
                    "https://github.com/richblack/SyncMCP/blob/main/docs/MCP-SETUP-GUIDE.md"
                ),
            )
        ]

    # 讀取完整指南
    with open(guide_path, "r", encoding="utf-8") as f:
        full_guide = f.read()

    # 根據要求的章節返回內容
    if section == "全部":
        return [TextContent(type="text", text=full_guide)]

    # 章節映射
    section_markers = {
        "全域MCP": "## 全域 MCP 設置",
        "專案MCP": "## 專案級 MCP 設置",
        "npx安裝": "#### 方式 A: npx (Node.js 套件)",
        "uvx安裝": "#### 方式 B: uvx (Python 套件)",
        "python安裝": "#### 方式 C: Python 虛擬環境",
        "常見錯誤": "## 常見錯誤與修復",
        "測試驗證": "## 測試與驗證",
    }

    marker = section_markers.get(section)
    if not marker:
        return [TextContent(type="text", text=full_guide)]

    # 提取章節內容
    lines = full_guide.split("\n")
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if marker in line:
            start_idx = i
        elif start_idx is not None and line.startswith("##") and i > start_idx:
            end_idx = i
            break

    if start_idx is None:
        return [TextContent(type="text", text=f"❌ 找不到章節: {section}\n\n使用 `section: \"全部\"` 查看完整指南")]

    if end_idx is None:
        end_idx = len(lines)

    section_content = "\n".join(lines[start_idx:end_idx])

    return [
        TextContent(
            type="text",
            text=f"# MCP 設置指南 - {section}\n\n{section_content}\n\n---\n\n💡 使用 `section: \"全部\"` 查看完整指南",
        )
    ]


async def _troubleshoot_mcp(arguments: dict) -> list[TextContent]:
    """診斷 MCP 問題並提供解決方案"""

    error_message = arguments.get("error_message", "")
    mcp_name = arguments.get("mcp_name", "")

    output_lines = []
    output_lines.append("# 🔧 MCP 故障排除\n")

    if mcp_name:
        output_lines.append(f"**問題 MCP**: {mcp_name}\n")

    output_lines.append(f"**錯誤訊息**: {error_message}\n")

    # 常見錯誤模式匹配
    error_lower = error_message.lower()

    # 1. 模組找不到
    if "modulenotfounderror" in error_lower or "no module named" in error_lower:
        output_lines.append("## 🔍 診斷結果\n")
        output_lines.append("**問題類型**: Python 模組依賴缺失\n")
        output_lines.append("## ✅ 解決方案\n")
        output_lines.append("### 方案 1: 改用虛擬環境安裝\n")
        output_lines.append("```bash")
        output_lines.append("# 建立虛擬環境")
        output_lines.append(f"mkdir -p ~/Documents/mcps/{mcp_name or 'your-mcp'}")
        output_lines.append(f"cd ~/Documents/mcps/{mcp_name or 'your-mcp'}")
        output_lines.append("python3.12 -m venv .venv")
        output_lines.append("")
        output_lines.append("# 安裝套件及缺失的依賴")
        output_lines.append(f".venv/bin/pip install {mcp_name or 'your-mcp-package'}")

        # 提取缺失的模組名稱
        if "'" in error_message:
            missing_module = error_message.split("'")[1]
            output_lines.append(f".venv/bin/pip install {missing_module}")

        output_lines.append("```\n")
        output_lines.append("### 方案 2: 更新配置使用虛擬環境\n")
        output_lines.append("在 `~/.claude.json` 中：")
        output_lines.append("```json")
        mcp_key = mcp_name or 'your-mcp'
        mcp_bin = mcp_name or 'your-mcp-executable'
        output_lines.append(f'"{mcp_key}": {{')
        output_lines.append('  "type": "stdio",')
        output_lines.append(f'  "command": "/Users/YOUR_USERNAME/Documents/mcps/{mcp_key}/.venv/bin/{mcp_bin}",')
        output_lines.append('  "args": [],')
        output_lines.append('  "env": {}')
        output_lines.append("}")
        output_lines.append("```")

    # 2. 命令找不到
    elif "command not found" in error_lower or "enoent" in error_lower:
        output_lines.append("## 🔍 診斷結果\n")
        output_lines.append("**問題類型**: 命令或執行檔不存在\n")
        output_lines.append("## ✅ 解決方案\n")
        output_lines.append("### 檢查命令是否存在\n")
        output_lines.append("```bash")
        output_lines.append("# 檢查 npx/uvx")
        output_lines.append("which npx uvx")
        output_lines.append("")
        output_lines.append("# 如果是 uvx，可能需要完整路徑")
        output_lines.append("which uvx  # 複製完整路徑到配置中")
        output_lines.append("```\n")
        output_lines.append("### 使用完整路徑\n")
        output_lines.append("將配置中的 `command` 改為完整路徑，例如：")
        output_lines.append('```json')
        output_lines.append('"command": "/Users/username/.cargo/bin/uvx"')
        output_lines.append("```")

    # 3. JSON 格式錯誤
    elif "json" in error_lower and ("parse" in error_lower or "syntax" in error_lower):
        output_lines.append("## 🔍 診斷結果\n")
        output_lines.append("**問題類型**: JSON 配置格式錯誤\n")
        output_lines.append("## ✅ 解決方案\n")
        output_lines.append("### 驗證 JSON 格式\n")
        output_lines.append("```bash")
        output_lines.append("# 檢查全域配置")
        output_lines.append("python3 -m json.tool ~/.claude.json")
        output_lines.append("")
        output_lines.append("# 檢查專案配置")
        output_lines.append("python3 -m json.tool .claude/mcp.json")
        output_lines.append("```\n")
        output_lines.append("### 常見錯誤\n")
        output_lines.append("- ❌ 最後一個項目後多餘的逗號")
        output_lines.append("- ❌ 缺少引號")
        output_lines.append("- ❌ 不匹配的括號")

    # 4. 認證問題
    elif "auth" in error_lower or "token" in error_lower or "credential" in error_lower:
        output_lines.append("## 🔍 診斷結果\n")
        output_lines.append("**問題類型**: 認證或憑證問題\n")
        output_lines.append("## ✅ 解決方案\n")
        output_lines.append("### 檢查環境變數\n")
        output_lines.append("確認 `env` 區塊中的認證資訊正確：")
        output_lines.append("```json")
        output_lines.append('"env": {')
        output_lines.append('  "API_KEY": "your_actual_key",')
        output_lines.append('  "TOKEN": "your_actual_token"')
        output_lines.append("}")
        output_lines.append("```\n")
        output_lines.append("### 檢查憑證檔案\n")
        output_lines.append("```bash")
        output_lines.append("# 確認檔案存在")
        output_lines.append("test -f /path/to/credentials.json && echo '✅ 存在' || echo '❌ 不存在'")
        output_lines.append("```")

    # 5. 專案 MCP 無效
    elif "專案" in error_message or "project" in error_lower or "mcp.json" in error_lower:
        output_lines.append("## 🔍 診斷結果\n")
        output_lines.append("**問題類型**: 專案級 MCP 配置無效\n")
        output_lines.append("## ✅ 解決方案\n")
        output_lines.append("### 檢查檔案位置\n")
        output_lines.append("**❌ 錯誤位置**:")
        output_lines.append("- `專案根目錄/mcp.json`")
        output_lines.append("- `專案根目錄/.mcp.json`\n")
        output_lines.append("**✅ 正確位置**:")
        output_lines.append("- `專案根目錄/.claude/mcp.json`\n")
        output_lines.append("```bash")
        output_lines.append("# 修復")
        output_lines.append("mkdir -p .claude")
        output_lines.append("mv mcp.json .claude/")
        output_lines.append("```")

    # 通用建議
    else:
        output_lines.append("## 🔍 診斷結果\n")
        output_lines.append("**問題類型**: 未知錯誤\n")
        output_lines.append("## ✅ 通用解決步驟\n")
        output_lines.append("1. **檢查配置格式**")
        output_lines.append("   ```bash")
        output_lines.append("   python3 -m json.tool ~/.claude.json")
        output_lines.append("   ```\n")
        output_lines.append("2. **檢查命令存在性**")
        output_lines.append("   ```bash")
        output_lines.append("   which npx uvx python3")
        output_lines.append("   ```\n")
        output_lines.append("3. **執行系統診斷**")
        output_lines.append("   ```bash")
        output_lines.append("   syncmcp doctor")
        output_lines.append("   ```\n")
        output_lines.append("4. **查看完整設置指南**")
        output_lines.append("   使用 `get_setup_guide` 工具查看詳細說明")

    # 添加相關資源
    output_lines.append("\n## 📚 相關資源\n")
    output_lines.append("- **完整設置指南**: 使用 `get_setup_guide` 工具")
    output_lines.append("- **系統診斷**: 執行 `syncmcp doctor`")
    output_lines.append("- **查看配置**: 執行 `syncmcp list claude-code`")
    output_lines.append("- **GitHub Issues**: https://github.com/richblack/SyncMCP/issues")

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
