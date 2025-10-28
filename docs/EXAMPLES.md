# SyncMCP 範例和教學

> **版本**: 2.0.0
> **更新日期**: 2025-10-29

## 📋 目錄

- [快速開始範例](#快速開始範例)
- [基礎使用場景](#基礎使用場景)
- [進階使用場景](#進階使用場景)
- [程式化使用](#程式化使用)
- [故障排除範例](#故障排除範例)
- [最佳實踐範例](#最佳實踐範例)

---

## 🚀 快速開始範例

### 範例 1: 第一次使用 SyncMCP

你剛安裝 SyncMCP，想要了解當前配置狀態並執行第一次同步。

```bash
# 步驟 1: 檢查系統是否正常
$ syncmcp doctor

🔍 SyncMCP 系統診斷

1. Python 版本
  ✅ Python 3.12.11 (需要 >= 3.10)

2. syncmcp 命令
  ✅ 在 PATH 中

...

✅ 系統狀態良好，SyncMCP 已就緒！

# 步驟 2: 查看當前配置狀態
$ syncmcp status

📊 配置狀態

Claude Code (~/.claude.json)
  ✅ 存在 | 10 MCPs | 最後修改: 2025-10-29 10:30

Claude Desktop (~/Library/Application Support/Claude/claude_desktop_config.json)
  ✅ 存在 | 8 MCPs | 最後修改: 2025-10-28 15:20

# 步驟 3: 查看配置差異
$ syncmcp diff

🔍 配置差異分析

新增 (2)
  • filesystem (Claude Desktop 缺少)
  • brave-search (Claude Desktop 缺少)

# 步驟 4: 預覽同步
$ syncmcp sync --dry-run

🔍 Dry Run Mode - 預覽同步結果

將執行以下操作:

Claude Desktop:
  ✅ 新增: filesystem
  ⚠️  跳過: brave-search (不支援 HTTP)

# 步驟 5: 執行同步
$ syncmcp sync

✅ 同步完成！

✅ 變更摘要:
  Claude Desktop: 新增 1 項 MCP

💾 備份已建立: ~/.syncmcp/backups/2025-10-29_10-35-20
```

---

## 📖 基礎使用場景

### 範例 2: 新增 MCP 後同步

你在 Claude Code 中安裝了新的 MCP，現在想要同步到其他客戶端。

```bash
# 在 Claude Code 中安裝 MCP
$ cd ~  # 確保在非專案目錄（安裝到全域）
$ claude mcp add github npx @modelcontextprotocol/server-github

# 驗證安裝
$ claude mcp list | grep github
✓ github

# 使用 SyncMCP 同步到其他客戶端
$ syncmcp sync

📦 分析配置差異...
🔄 來源: claude-code (最新)

✅ 同步完成！

變更摘要:
  Claude Desktop: 新增 github
  Roo Code: 新增 github
  Gemini: 新增 github

# 驗證同步結果
$ syncmcp list | grep github
github
  ├─ Claude Code: ✅
  ├─ Claude Desktop: ✅
  ├─ Roo Code: ✅
  └─ Gemini: ✅
```

---

### 範例 3: 刪除 MCP 後同步

你決定移除某個不再使用的 MCP。

```bash
# 從 Claude Code 移除
$ claude mcp remove old-mcp

# 同步刪除到其他客戶端
$ syncmcp sync

⚠️  警告: 將從以下客戶端刪除 MCP

  • old-mcp 將從 Claude Desktop 刪除
  • old-mcp 將從 Roo Code 刪除

是否繼續? [y/N]: y

✅ 同步完成！

變更摘要:
  Claude Desktop: 刪除 old-mcp
  Roo Code: 刪除 old-mcp

# 驗證
$ syncmcp list | grep old-mcp
# (無結果 - 已刪除)
```

---

### 範例 4: 使用互動模式

使用友善的 TUI 介面進行操作。

```bash
$ syncmcp interactive

╔════════════════════════════════════════════════════╗
║               SyncMCP 互動模式                      ║
╚════════════════════════════════════════════════════╝

請選擇操作:
❯ 🔄 同步配置
  📊 查看狀態
  🔍 查看差異
  📜 查看歷史
  ⏮️  恢復備份
  🚪 退出

# 選擇「同步配置」
# 選擇「查看狀態」後顯示:

╔════════════════════════════════════════════════════╗
║                  配置狀態                           ║
╚════════════════════════════════════════════════════╝

Claude Code
  ✅ 已載入 | 10 MCPs

Claude Desktop
  ✅ 已載入 | 8 MCPs

Roo Code
  ✅ 已載入 | 10 MCPs

[按任意鍵返回]
```

---

## 🎓 進階使用場景

### 範例 5: 處理不同客戶端的類型限制

你有一個 HTTP 類型的 MCP，需要了解如何在不同客戶端間同步。

```bash
# 在 Claude Code 中安裝 HTTP MCP
$ cd ~
$ claude mcp add context7 sse https://mcp.context7.com/mcp

# 查看差異
$ syncmcp diff

🔍 配置差異分析

新增 (1)
  • context7 (其他客戶端缺少)

修改 (0)

注意事項:
  ⚠️  Claude Desktop 不支援 HTTP/SSE 類型
  ⚠️  Roo Code 會自動轉換為 streamable-http

# 執行同步
$ syncmcp sync

處理中...

✅ 同步完成！

變更摘要:
  Claude Desktop: ⚠️  跳過 context7 (不支援 SSE)
  Roo Code: ✅ 新增 context7 (已轉為 streamable-http)
  Gemini: ✅ 新增 context7

# 驗證各客戶端的配置
$ cat ~/.claude.json | jq '.mcpServers.context7'
{
  "type": "sse",
  "url": "https://mcp.context7.com/mcp"
}

$ cat ~/.roo-code/config.json | jq '.mcpServers.context7'
{
  "type": "streamable-http",
  "url": "https://mcp.context7.com/mcp"
}

$ cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq '.mcpServers.context7'
# (無結果 - 已過濾)
```

---

### 範例 6: 從備份恢復

測試新 MCP 時出現問題，需要回滾。

```bash
# 安裝並同步新的測試 MCP
$ claude mcp add test-mcp npx test-mcp-server
$ syncmcp sync

✅ 同步完成！
💾 備份: ~/.syncmcp/backups/2025-10-29_11-00-00

# ... 使用一段時間後發現有問題 ...

# 查看可用備份
$ syncmcp history --limit 5

📜 同步歷史

1. 2025-10-29 11:00:00
   操作: sync (auto)
   狀態: ✅ 成功
   變更: 4 clients
   備份: ~/.syncmcp/backups/2025-10-29_11-00-00

2. 2025-10-29 10:35:20
   操作: sync (auto)
   狀態: ✅ 成功
   變更: 1 client
   備份: ~/.syncmcp/backups/2025-10-29_10-35-20

# 使用互動模式恢復
$ syncmcp restore

📦 可用備份:

❯ 2025-10-29 11:00:00 (最新)
  2025-10-29 10:35:20
  2025-10-29 09:15:45
  ...

# 選擇 10:35:20 (test-mcp 安裝前)

確認要恢復此備份嗎? [y/N]: y

🔄 恢復中...

✅ 恢復完成！

變更摘要:
  所有客戶端已恢復到 2025-10-29 10:35:20

# 驗證
$ claude mcp list | grep test-mcp
# (無結果 - 已恢復到之前狀態)
```

---

### 範例 7: 手動確認同步策略

你想要更精確地控制同步過程。

```bash
$ syncmcp sync --strategy manual

🔍 分析配置差異...

發現 3 項差異

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1/3: 新增 filesystem 到 Claude Desktop?

詳細資訊:
  類型: stdio
  命令: npx -y @modelcontextprotocol/server-filesystem /tmp

是否執行? [Y/n]: y
✅ 已執行

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2/3: 新增 brave-search 到 Claude Desktop?

詳細資訊:
  類型: stdio
  命令: npx -y @modelcontextprotocol/server-brave-search

⚠️  警告: 需要 BRAVE_API_KEY 環境變數

是否執行? [Y/n]: n
⏭️  已跳過

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3/3: 更新 context7 在 Roo Code?

變更:
  - 類型: sse → streamable-http

是否執行? [Y/n]: y
✅ 已執行

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 手動同步完成！

執行: 2
跳過: 1
```

---

### 範例 8: 處理專案級別 MCP（Bug #13 解決方案）

你在專案中安裝了 MCP，現在需要移到全域以便同步。

```bash
# 問題: 專案 MCP 不會被 SyncMCP 偵測
$ cd /Users/username/Projects/my-project
$ claude mcp list | grep chrome-devtools
✓ chrome-devtools  # 在專案中

$ syncmcp list | grep chrome-devtools
# (無結果 - SyncMCP 看不到專案級 MCP)

# 解決方案: 移動到全域

# 步驟 1: 檢查 MCP 位置
$ cat ~/.claude.json | jq '.projects["/Users/username/Projects/my-project"].mcpServers.keys'
[
  "chrome-devtools"
]

# 步驟 2: 在專案目錄中刪除
$ cd /Users/username/Projects/my-project
$ claude mcp remove chrome-devtools

# 步驟 3: 切換到非專案目錄
$ cd ~

# 步驟 4: 重新新增到全域
$ claude mcp add chrome-devtools npx chrome-devtools-mcp@latest

# 步驟 5: 驗證
$ claude mcp list | grep chrome-devtools
✓ chrome-devtools  # 現在在全域

$ syncmcp list | grep chrome-devtools
chrome-devtools
  ├─ Claude Code: ✅  # SyncMCP 可以看到了
  ├─ Claude Desktop: ❌
  ├─ Roo Code: ❌
  └─ Gemini: ❌

# 步驟 6: 同步到其他客戶端
$ syncmcp sync

✅ 同步完成！

變更摘要:
  Claude Desktop: 新增 chrome-devtools
  Roo Code: 新增 chrome-devtools
  Gemini: 新增 chrome-devtools
```

---

## 💻 程式化使用

### 範例 9: 使用 Python API

在 Python 腳本中使用 SyncMCP。

```python
#!/usr/bin/env python3
"""
自動化 MCP 同步腳本
"""

from syncmcp.core.config_manager import ConfigManager
from syncmcp.core.diff_engine import DiffEngine
from syncmcp.core.sync_engine import SyncEngine, SyncStrategy
from syncmcp.core.backup_manager import BackupManager

def main():
    # 初始化元件
    config_manager = ConfigManager()
    diff_engine = DiffEngine()
    backup_manager = BackupManager()
    sync_engine = SyncEngine(
        config_manager,
        diff_engine,
        backup_manager,
        verbose=True
    )

    # 1. 檢查配置狀態
    print("📊 檢查配置狀態...")
    configs = config_manager.load_all()
    for name, config in configs.items():
        print(f"  {name}: {len(config.mcpServers)} MCPs")

    # 2. 分析差異
    print("\n🔍 分析差異...")
    report = diff_engine.analyze(configs)
    stats = report.get_statistics()
    print(f"  新增: {stats['added']}")
    print(f"  刪除: {stats['removed']}")
    print(f"  修改: {stats['modified']}")

    # 3. 詢問是否執行同步
    if stats['added'] > 0 or stats['removed'] > 0 or stats['modified'] > 0:
        response = input("\n是否執行同步? [y/N]: ")
        if response.lower() == 'y':
            # 4. 執行同步
            print("\n🔄 執行同步...")
            result = sync_engine.sync(
                strategy=SyncStrategy.AUTO,
                dry_run=False,
                create_backup=True
            )

            # 5. 顯示結果
            if result.success:
                print("\n✅ 同步成功！")
                if result.backup_path:
                    print(f"💾 備份: {result.backup_path}")
                print("\n變更摘要:")
                for client, changes in result.changes.items():
                    print(f"  {client}: {len(changes)} 項變更")
            else:
                print("\n❌ 同步失敗！")
                for error in result.errors:
                    print(f"  - {error}")
        else:
            print("取消同步")
    else:
        print("\n✅ 配置已同步，無需操作")

if __name__ == "__main__":
    main()
```

**執行**:
```bash
$ python3 auto_sync.py

📊 檢查配置狀態...
  claude-code: 10 MCPs
  claude-desktop: 8 MCPs
  roo-code: 10 MCPs
  gemini: 9 MCPs

🔍 分析差異...
  新增: 2
  刪除: 0
  修改: 1

是否執行同步? [y/N]: y

🔄 執行同步...

✅ 同步成功！
💾 備份: /Users/username/.syncmcp/backups/2025-10-29_11-30-00

變更摘要:
  claude-desktop: 2 項變更
  gemini: 1 項變更
```

---

### 範例 10: 自訂配置載入

載入特定客戶端的配置並進行分析。

```python
from syncmcp.core.config_manager import ConfigManager

# 初始化管理器
manager = ConfigManager()

# 載入 Claude Code 配置
config = manager.load("claude-code")

print(f"客戶端: {config.client_name}")
print(f"MCP 數量: {len(config.mcpServers)}")
print(f"最後修改: {config.last_modified}")

# 列出所有 MCP
print("\nMCP 清單:")
for name, server in config.mcpServers.items():
    print(f"  • {name}")
    print(f"    類型: {server.get('type', 'unknown')}")
    if server.get('type') == 'stdio':
        print(f"    命令: {server.get('command', 'N/A')}")
    elif server.get('type') in ['http', 'sse', 'streamable-http']:
        print(f"    URL: {server.get('url', 'N/A')}")
    print()
```

**輸出**:
```
客戶端: claude-code
MCP 數量: 10
最後修改: 1698765432.0

MCP 清單:
  • filesystem
    類型: stdio
    命令: npx

  • context7
    類型: sse
    URL: https://mcp.context7.com/mcp

  ...
```

---

### 範例 11: 自訂差異報告

生成自訂格式的差異報告。

```python
from syncmcp.core.config_manager import ConfigManager
from syncmcp.core.diff_engine import DiffEngine, DiffType

# 載入配置並分析
manager = ConfigManager()
engine = DiffEngine()
configs = manager.load_all()
report = engine.analyze(configs)

# 生成 JSON 格式報告
import json

def diff_to_dict(diff_item):
    return {
        "mcp_name": diff_item.mcp_name,
        "type": diff_item.diff_type.value,
        "clients": {
            client: (config if config else None)
            for client, config in diff_item.clients.items()
        }
    }

report_dict = {
    "timestamp": "2025-10-29 11:45:00",
    "statistics": report.get_statistics(),
    "diffs": [diff_to_dict(d) for d in report.diffs]
}

# 輸出 JSON
print(json.dumps(report_dict, indent=2, ensure_ascii=False))

# 或保存到檔案
with open("diff_report.json", "w", encoding="utf-8") as f:
    json.dump(report_dict, f, indent=2, ensure_ascii=False)
```

---

### 範例 12: MCP Server 整合

在 AI 客戶端中透過 MCP 使用 SyncMCP。

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_syncmcp_via_mcp():
    """透過 MCP 協定使用 SyncMCP"""

    # 連接到 SyncMCP MCP Server
    server_params = StdioServerParameters(
        command="syncmcp-server",  # 假設已安裝
        args=[]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化
            await session.initialize()

            # 列出可用工具
            tools = await session.list_tools()
            print("可用工具:")
            for tool in tools:
                print(f"  • {tool.name}")

            # 檢查同步狀態
            result = await session.call_tool("check_sync_status", {})
            print(f"\n狀態:\n{result[0].text}")

            # 顯示差異
            result = await session.call_tool("show_config_diff", {})
            print(f"\n差異:\n{result[0].text}")

            # 執行同步（dry-run）
            result = await session.call_tool("sync_mcp_configs", {
                "strategy": "auto",
                "dry_run": True,
                "create_backup": False
            })
            print(f"\n同步預覽:\n{result[0].text}")

# 執行
import asyncio
asyncio.run(use_syncmcp_via_mcp())
```

---

## 🔧 故障排除範例

### 範例 13: 診斷並修復 PATH 問題

```bash
# 問題: syncmcp 命令找不到
$ syncmcp --version
zsh: command not found: syncmcp

# 解決步驟 1: 執行 doctor（如果可以找到 Python 模組）
$ python3 -m syncmcp doctor

⚠️  syncmcp 不在 PATH 中

💡 建議:
   1. 執行: pip install -e . (開發模式)
   或
   2. 將以下路徑加到 PATH:
      export PATH="$HOME/.local/bin:$PATH"

# 解決步驟 2: 重新安裝
$ pip install --force-reinstall syncmcp

# 解決步驟 3: 驗證
$ which syncmcp
/Users/username/.local/bin/syncmcp

$ syncmcp --version
syncmcp, version 2.0.0

# 解決步驟 4: 如果仍然不行，手動添加到 PATH
$ echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
$ source ~/.zshrc
```

---

### 範例 14: 修復損壞的配置

```bash
# 問題: 配置檔案格式錯誤
$ syncmcp status
❌ 錯誤: 無法載入 ~/.claude.json
JSONDecodeError: Expecting ',' delimiter: line 15 column 5

# 解決步驟 1: 查看最新備份
$ syncmcp history --limit 1

📜 最新備份:
  2025-10-29 10:35:20
  備份路徑: ~/.syncmcp/backups/2025-10-29_10-35-20

# 解決步驟 2: 檢查配置檔案
$ cat ~/.claude.json | head -20
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx"
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]  # ❌ 缺少逗號
    }
  }
}

# 解決步驟 3: 選項 A - 手動修復
$ vi ~/.claude.json
# 添加缺少的逗號

# 或 選項 B - 從備份恢復
$ syncmcp restore
# 選擇最近的備份

# 解決步驟 4: 驗證修復
$ syncmcp status
✅ 所有配置已載入

$ syncmcp doctor
✅ 系統狀態良好
```

---

### 範例 15: 處理權限問題

```bash
# 問題: 權限被拒絕
$ syncmcp sync
❌ 錯誤: Permission denied: /Users/username/.claude.json

# 解決步驟 1: 檢查權限
$ ls -la ~/.claude.json
-r--r--r--  1 username  staff  1234 Oct 29 10:00 .claude.json  # 只有讀取權限

# 解決步驟 2: 修復權限
$ chmod 644 ~/.claude.json

# 解決步驟 3: 驗證
$ ls -la ~/.claude.json
-rw-r--r--  1 username  staff  1234 Oct 29 10:00 .claude.json  # 現在有寫入權限

$ syncmcp sync
✅ 同步完成！
```

---

## ✨ 最佳實踐範例

### 範例 16: 定期同步腳本

建立 cron job 定期自動同步。

```bash
# 建立同步腳本
$ cat > ~/bin/auto-sync-mcp.sh << 'EOF'
#!/bin/bash

# SyncMCP 自動同步腳本

LOG_FILE="$HOME/.syncmcp/auto-sync.log"

echo "=== $(date) ===" >> "$LOG_FILE"

# 執行同步
syncmcp sync --strategy auto >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ 自動同步成功" >> "$LOG_FILE"
else
    echo "❌ 自動同步失敗" >> "$LOG_FILE"
    # 可選: 發送通知
    # osascript -e 'display notification "SyncMCP 同步失敗" with title "SyncMCP"'
fi

echo "" >> "$LOG_FILE"
EOF

$ chmod +x ~/bin/auto-sync-mcp.sh

# 設定 cron job（每天中午 12:00 執行）
$ crontab -e
# 添加:
0 12 * * * $HOME/bin/auto-sync-mcp.sh

# 測試執行
$ ~/bin/auto-sync-mcp.sh

# 查看日誌
$ tail -20 ~/.syncmcp/auto-sync.log
```

---

### 範例 17: 同步前檢查清單

建立同步前的檢查腳本。

```python
#!/usr/bin/env python3
"""
同步前檢查腳本
"""

import sys
from pathlib import Path
from syncmcp.core.config_manager import ConfigManager
from syncmcp.core.diff_engine import DiffEngine

def check_configs():
    """檢查配置狀態"""
    print("🔍 檢查配置...")

    manager = ConfigManager()
    issues = []

    # 檢查各客戶端配置
    for client_name, adapter in manager.adapters.items():
        config_path = adapter.get_config_path()

        # 檢查 1: 檔案是否存在
        if not config_path.exists():
            print(f"  ⚠️  {client_name}: 配置不存在")
            continue

        # 檢查 2: 檔案權限
        if not config_path.is_file():
            issues.append(f"{client_name}: 不是檔案")
            continue

        if not (config_path.stat().st_mode & 0o600):
            issues.append(f"{client_name}: 權限不正確")

        # 檢查 3: JSON 格式
        try:
            config = adapter.load()
            print(f"  ✅ {client_name}: {len(config.mcpServers)} MCPs")
        except Exception as e:
            issues.append(f"{client_name}: {str(e)}")

    return issues

def check_backups():
    """檢查備份"""
    print("\n💾 檢查備份...")

    backup_dir = Path.home() / ".syncmcp" / "backups"
    if not backup_dir.exists():
        print("  ⚠️  備份目錄不存在")
        return []

    backups = sorted(backup_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    print(f"  ✅ 找到 {len(backups)} 個備份")

    if backups:
        latest = backups[0]
        print(f"  📅 最新: {latest.name}")

    return []

def check_diff():
    """檢查差異"""
    print("\n🔍 檢查差異...")

    manager = ConfigManager()
    engine = DiffEngine()

    configs = manager.load_all()
    report = engine.analyze(configs)
    stats = report.get_statistics()

    print(f"  新增: {stats['added']}")
    print(f"  刪除: {stats['removed']}")
    print(f"  修改: {stats['modified']}")

    has_significant_changes = stats['removed'] > 0 or stats['modified'] > 5

    return ["存在大量變更，建議手動確認"] if has_significant_changes else []

def main():
    print("╔════════════════════════════════════════════╗")
    print("║        SyncMCP 同步前檢查               ║")
    print("╚════════════════════════════════════════════╝\n")

    all_issues = []

    # 執行檢查
    all_issues.extend(check_configs())
    all_issues.extend(check_backups())
    all_issues.extend(check_diff())

    # 顯示結果
    print("\n" + "=" * 50)
    if all_issues:
        print("❌ 發現問題:")
        for issue in all_issues:
            print(f"  • {issue}")
        print("\n建議: 修復問題後再執行同步")
        sys.exit(1)
    else:
        print("✅ 所有檢查通過，可以安全執行同步")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**使用**:
```bash
$ python3 pre_sync_check.py

╔════════════════════════════════════════════╗
║        SyncMCP 同步前檢查               ║
╚════════════════════════════════════════════╝

🔍 檢查配置...
  ✅ claude-code: 10 MCPs
  ✅ claude-desktop: 8 MCPs
  ✅ roo-code: 10 MCPs
  ✅ gemini: 9 MCPs

💾 檢查備份...
  ✅ 找到 15 個備份
  📅 最新: 2025-10-29_10-35-20

🔍 檢查差異...
  新增: 2
  刪除: 0
  修改: 1

==================================================
✅ 所有檢查通過，可以安全執行同步

# 然後執行同步
$ syncmcp sync
```

---

### 範例 18: 多機器同步方案

使用 Git 同步多台機器的配置。

```bash
# 機器 A - 設定 Git 倉庫
$ mkdir -p ~/mcp-configs
$ cd ~/mcp-configs
$ git init

# 建立同步腳本
$ cat > sync-to-repo.sh << 'EOF'
#!/bin/bash
# 將配置複製到 Git 倉庫

REPO_DIR="$HOME/mcp-configs"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# 複製配置
cp ~/.claude.json "$REPO_DIR/claude-code.json"
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json "$REPO_DIR/claude-desktop.json"
cp ~/.roo-code/config.json "$REPO_DIR/roo-code.json"

# 提交
cd "$REPO_DIR"
git add *.json
git commit -m "Update configs: $TIMESTAMP"
git push origin main
EOF

$ chmod +x sync-to-repo.sh

# 執行並推送
$ ./sync-to-repo.sh

# 機器 B - 克隆並恢復
$ cd ~
$ git clone https://github.com/username/mcp-configs.git

# 建立恢復腳本
$ cat > ~/mcp-configs/restore-from-repo.sh << 'EOF'
#!/bin/bash
# 從 Git 倉庫恢復配置

REPO_DIR="$HOME/mcp-configs"

# 拉取最新
cd "$REPO_DIR"
git pull origin main

# 備份當前配置
syncmcp sync --dry-run  # 確保有備份

# 恢復配置
cp "$REPO_DIR/claude-code.json" ~/.claude.json
cp "$REPO_DIR/claude-desktop.json" ~/Library/Application\ Support/Claude/claude_desktop_config.json
cp "$REPO_DIR/roo-code.json" ~/.roo-code/config.json

echo "✅ 配置已恢復"

# 同步到本地其他客戶端
syncmcp sync
EOF

$ chmod +x ~/mcp-configs/restore-from-repo.sh
$ ~/mcp-configs/restore-from-repo.sh
```

---

## 📚 進一步學習

- [使用者指南](USER-GUIDE.md) - 完整功能說明
- [開發者指南](DEVELOPER-GUIDE.md) - 開發與貢獻
- [API 文檔](API.md) - 程式化使用
- [故障排除](USER-GUIDE.md#故障排除) - 常見問題解決

---

**上次更新**: 2025-10-29
**版本**: 2.0.0
