# SyncMCP 使用者指南

> **版本**: 2.0.0
> **更新日期**: 2025-10-29

## 📋 目錄

- [快速開始](#快速開始)
- [安裝](#安裝)
- [基本使用](#基本使用)
- [命令參考](#命令參考)
- [互動模式](#互動模式)
- [常見使用場景](#常見使用場景)
- [故障排除](#故障排除)
- [最佳實踐](#最佳實踐)

---

## 🚀 快速開始

### 5 分鐘入門

```bash
# 1. 安裝
pip install syncmcp

# 2. 檢查系統
syncmcp doctor

# 3. 查看當前配置
syncmcp status

# 4. 預覽同步（不實際修改）
syncmcp sync --dry-run

# 5. 執行同步
syncmcp sync
```

### 什麼是 SyncMCP？

SyncMCP 是一個工具，用於在多個 AI 客戶端之間同步 MCP（Model Context Protocol）配置：

- ✅ **Claude Code** - VSCode 擴充功能
- ✅ **Claude Desktop** - 桌面應用
- ✅ **Roo Code** - VSCode 擴充功能
- ✅ **Gemini CLI** - 命令列工具

### 為什麼需要 SyncMCP？

當你在不同 AI 客戶端之間切換時，手動複製 MCP 配置容易出錯且繁瑣。SyncMCP 自動化這個過程，確保：

- 🔄 配置在所有客戶端間保持一致
- 🛡️ 自動備份，防止資料丟失
- 🔍 智慧偵測差異
- ⚡ 一鍵同步

---

## 📦 安裝

### 系統需求

- **Python**: >= 3.10
- **作業系統**: macOS, Linux, Windows
- **必要套件**: click, rich, InquirerPy

### 安裝方法

#### 方法 1: PyPI 安裝（推薦）

```bash
pip install syncmcp
```

#### 方法 2: 從原始碼安裝

```bash
git clone https://github.com/yourusername/syncmcp.git
cd syncmcp
pip install -e .
```

#### 方法 3: 開發模式安裝

```bash
git clone https://github.com/yourusername/syncmcp.git
cd syncmcp
pip install -e ".[dev]"
```

### 驗證安裝

```bash
# 檢查版本
syncmcp --version

# 執行系統診斷
syncmcp doctor
```

**預期輸出**:
```
🔍 SyncMCP 系統診斷

1. Python 版本
  ✅ Python 3.12.11 (需要 >= 3.10)

2. syncmcp 命令
  ✅ 在 PATH 中
  📍 位置: /usr/local/bin/syncmcp

...

✅ 系統狀態良好，SyncMCP 已就緒！
```

---

## 🎯 基本使用

### 1. 查看當前狀態

```bash
syncmcp status
```

**輸出示例**:
```
📊 配置狀態

Claude Code (~/.claude.json)
  ✅ 存在 | 10 MCPs | 最後修改: 2025-10-29 10:30

Claude Desktop (~/Library/Application Support/Claude/claude_desktop_config.json)
  ✅ 存在 | 8 MCPs | 最後修改: 2025-10-28 15:20

Roo Code (~/.roo-code/config.json)
  ✅ 存在 | 10 MCPs | 最後修改: 2025-10-29 09:00

Gemini CLI (~/.gemini/config.json)
  ⚠️  不存在
```

### 2. 列出所有 MCP

```bash
syncmcp list
```

**輸出示例**:
```
📦 已安裝的 MCP Servers

filesystem
  ├─ Claude Code: ✅
  ├─ Claude Desktop: ✅
  ├─ Roo Code: ✅
  └─ Gemini: ❌

brave-search
  ├─ Claude Code: ✅
  ├─ Claude Desktop: ❌ (不支援 HTTP)
  ├─ Roo Code: ✅
  └─ Gemini: ❌
```

### 3. 查看配置差異

```bash
syncmcp diff
```

**輸出示例**:
```
🔍 配置差異分析

新增 (2)
  • filesystem (Claude Desktop 缺少)
  • brave-search (Claude Desktop 缺少)

修改 (1)
  • context7
    - Claude Code: type=sse
    - Roo Code: type=streamable-http

統計
  總計 MCP: 12
  需要同步: 3
  無差異: 9
```

### 4. 預覽同步（Dry Run）

```bash
syncmcp sync --dry-run
```

這會顯示同步將執行的操作，但**不會實際修改**任何配置。

### 5. 執行同步

```bash
# 自動同步（推薦）
syncmcp sync

# 手動模式（逐個確認）
syncmcp sync --strategy manual

# 不建立備份
syncmcp sync --no-backup

# 詳細輸出
syncmcp sync --verbose
```

---

## 📖 命令參考

### `syncmcp sync`

同步所有客戶端的 MCP 配置。

**選項**:
- `--dry-run`: 預覽模式，不實際修改
- `--strategy <auto|manual>`: 同步策略
  - `auto`: 自動選擇最新配置（預設）
  - `manual`: 逐個確認
- `--no-backup`: 不建立備份
- `--verbose, -v`: 詳細輸出

**範例**:
```bash
# 自動同步
syncmcp sync

# 預覽同步
syncmcp sync --dry-run

# 手動確認每個變更
syncmcp sync --strategy manual

# 同步但不備份
syncmcp sync --no-backup
```

---

### `syncmcp status`

顯示所有客戶端的配置狀態。

**輸出資訊**:
- 配置檔案路徑
- 是否存在
- MCP 數量
- 最後修改時間

**範例**:
```bash
syncmcp status
```

---

### `syncmcp list`

列出所有 MCP 及其在各客戶端的狀態。

**範例**:
```bash
syncmcp list
```

---

### `syncmcp diff`

顯示客戶端之間的配置差異。

**輸出資訊**:
- 新增的 MCP
- 刪除的 MCP
- 修改的 MCP
- 統計摘要

**範例**:
```bash
syncmcp diff
```

---

### `syncmcp doctor`

診斷系統環境和安裝狀態。

**檢查項目**:
1. Python 版本
2. syncmcp 命令是否在 PATH
3. 必要依賴套件
4. MCP 支援檢測
5. 配置檔案位置
6. 目錄結構

**範例**:
```bash
syncmcp doctor
```

---

### `syncmcp history`

查看同步歷史記錄。

**選項**:
- `--limit <n>`: 顯示最近 n 筆記錄（預設: 10）
- `--stats`: 顯示統計資訊

**範例**:
```bash
# 顯示最近 10 筆
syncmcp history

# 顯示最近 20 筆
syncmcp history --limit 20

# 顯示統計
syncmcp history --stats
```

---

### `syncmcp restore`

從備份恢復配置。

**使用方式**:
```bash
syncmcp restore
```

會顯示可用備份列表，選擇要恢復的備份。

---

### `syncmcp interactive`

啟動互動模式（TUI）。

**範例**:
```bash
syncmcp interactive
```

---

### `syncmcp open`

在編輯器中打開配置檔案。

**選項**:
- `<client>`: 指定客戶端名稱

**範例**:
```bash
# 打開 Claude Code 配置
syncmcp open claude-code

# 打開 Claude Desktop 配置
syncmcp open claude-desktop
```

---

## 🖥️ 互動模式

SyncMCP 提供友善的終端互動介面（TUI）。

### 啟動互動模式

```bash
syncmcp interactive
```

### 功能

1. **同步配置** - 一鍵同步所有客戶端
2. **查看狀態** - 即時顯示配置狀態
3. **查看差異** - 視覺化差異比較
4. **查看歷史** - 瀏覽同步歷史
5. **恢復備份** - 從備份恢復
6. **退出** - 結束互動模式

### 鍵盤操作

- `↑/↓` - 移動選項
- `Enter` - 確認選擇
- `Ctrl+C` - 退出

---

## 💡 常見使用場景

### 場景 1: 初次設定 Claude Desktop

你在 Claude Code 中安裝了多個 MCP，現在想在 Claude Desktop 中使用。

```bash
# 1. 檢查當前配置
syncmcp status

# 2. 查看會同步哪些 MCP
syncmcp diff

# 3. 執行同步
syncmcp sync
```

**注意**: Claude Desktop 只支援 `stdio` 類型的 MCP，HTTP/SSE 類型會自動過濾。

---

### 場景 2: 在 Claude Code 和 Roo Code 間切換

兩個客戶端都支援多種 MCP 類型，但使用不同的 transport 類型。

```bash
# 自動轉換並同步
syncmcp sync
```

**自動轉換**:
- Claude Code 的 `http`/`sse` → Roo Code 的 `streamable-http`
- Roo Code 的 `streamable-http` → Claude Code 的 `sse` 或 `http`

---

### 場景 3: 測試新 MCP 後回滾

```bash
# 1. 安裝並同步新 MCP
claude mcp add new-mcp npx new-mcp@latest
syncmcp sync

# 2. 發現問題，需要回滾
syncmcp restore

# 3. 選擇同步前的備份
```

---

### 場景 4: 在多台機器間同步

```bash
# 機器 A - 匯出配置
syncmcp sync
cp ~/.syncmcp/backups/latest backups/

# 機器 B - 匯入配置
syncmcp restore
# 選擇複製過來的備份
```

---

### 場景 5: 定期維護

```bash
# 檢查系統健康
syncmcp doctor

# 查看同步歷史
syncmcp history --stats

# 清理舊備份（自動保留最新 10 個）
# 自動執行，無需手動操作
```

---

## 🔧 故障排除

### 問題 1: syncmcp 命令找不到

**症狀**:
```bash
zsh: command not found: syncmcp
```

**解決方法**:
```bash
# 確認安裝
pip list | grep syncmcp

# 重新安裝
pip install --force-reinstall syncmcp

# 檢查 PATH
syncmcp doctor
```

---

### 問題 2: Python 版本過舊

**症狀**:
```
❌ Python 3.9.0 (需要 >= 3.10)
```

**解決方法**:
```bash
# macOS
brew install python@3.12

# Ubuntu/Debian
sudo apt install python3.12

# 使用 pyenv
pyenv install 3.12.0
pyenv global 3.12.0
```

---

### 問題 3: 同步失敗

**症狀**:
```
❌ 同步失敗: Permission denied
```

**解決方法**:
```bash
# 檢查檔案權限
ls -la ~/.claude.json
ls -la ~/Library/Application\ Support/Claude/

# 修復權限
chmod 644 ~/.claude.json

# 如果是系統保護，暫時停用應用
```

---

### 問題 4: Claude Desktop HTTP MCP 無法同步

**原因**: Claude Desktop **只支援** `stdio` 類型的 MCP。

**解決方法**:
這是正常行為。SyncMCP 會自動過濾不支援的類型。如果你需要在 Claude Desktop 使用該 MCP，請檢查是否有 stdio 版本。

---

### 問題 5: 專案級別的 MCP 未被同步

**症狀**:
```bash
# MCP 在 Claude Code 中存在
claude mcp list
# ✓ chrome-devtools

# 但 syncmcp 看不到
syncmcp list
# ✗ chrome-devtools
```

**原因**: Bug #13 - 目前不支援專案級別的 MCP 配置。

**解決方法**: 將專案級別的 MCP 移動到全域級別。

```bash
# 1. 在專案目錄中刪除
cd /path/to/project
claude mcp remove chrome-devtools

# 2. 切換到非專案目錄
cd ~

# 3. 重新新增到全域
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest

# 4. 同步
syncmcp sync
```

詳細說明: [docs/MOVE-MCP-TO-GLOBAL.md](MOVE-MCP-TO-GLOBAL.md)

---

## ✅ 最佳實踐

### 1. 定期備份

雖然 SyncMCP 會自動備份，但建議定期手動備份重要配置：

```bash
# 手動備份
cp -r ~/.syncmcp/backups ~/Dropbox/syncmcp-backups
```

### 2. 使用 Dry Run

在執行實際同步前，先使用 `--dry-run` 預覽：

```bash
syncmcp sync --dry-run
```

### 3. 檢查 doctor

遇到問題時，先執行診斷：

```bash
syncmcp doctor
```

### 4. 查看歷史

了解之前的同步操作：

```bash
syncmcp history --limit 20
```

### 5. 使用全域 MCP

避免專案級別的 MCP（目前不支援），統一使用全域配置。

### 6. 保持客戶端更新

確保所有 AI 客戶端都是最新版本，以獲得最佳相容性。

### 7. 了解客戶端限制

- **Claude Desktop**: 只支援 stdio
- **Gemini CLI**: 只支援全域配置
- **Roo Code**: 使用 streamable-http（會自動轉換）

---

## 📚 進階主題

### 配置檔案位置

| 客戶端 | 配置檔案路徑 |
|-------|-------------|
| Claude Code | `~/.claude.json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) |
| Roo Code | `~/.roo-code/config.json` |
| Gemini CLI | `~/.gemini/config.json` |

### SyncMCP 目錄結構

```
~/.syncmcp/
├── backups/          # 自動備份（保留最新 10 個）
│   ├── 2025-10-29_10-30-45/
│   ├── 2025-10-29_09-15-20/
│   └── ...
├── history.json      # 同步歷史
└── config.json       # SyncMCP 配置（未來功能）
```

### 環境變數

目前 SyncMCP 不使用環境變數，但未來版本可能支援：

- `SYNCMCP_HOME`: 自訂 SyncMCP 目錄
- `SYNCMCP_BACKUP_KEEP`: 保留備份數量

---

## 🆘 獲取幫助

### 內建幫助

```bash
# 主命令幫助
syncmcp --help

# 子命令幫助
syncmcp sync --help
syncmcp restore --help
```

### 社群支援

- **GitHub Issues**: [提交問題](https://github.com/yourusername/syncmcp/issues)
- **文檔**: [完整文檔](https://github.com/yourusername/syncmcp/tree/main/docs)

### 報告 Bug

請提供以下資訊：

1. `syncmcp --version` 輸出
2. `syncmcp doctor` 輸出
3. 完整錯誤訊息
4. 重現步驟

---

## 📝 更新日誌

查看 [CHANGELOG.md](../CHANGELOG.md) 了解版本更新內容。

---

## 🔗 相關文檔

- [開發者指南](DEVELOPER-GUIDE.md)
- [API 文檔](API.md)
- [範例和教學](EXAMPLES.md)
- [移動 MCP 到全域](MOVE-MCP-TO-GLOBAL.md)

---

**上次更新**: 2025-10-29
**版本**: 2.0.0
