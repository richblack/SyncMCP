# SyncMCP MCP Server 整合指南

讓 AI 助手（Claude、Gemini 等）直接管理你的 MCP 配置同步！

## 📋 目錄

- [簡介](#簡介)
- [功能特性](#功能特性)
- [安裝配置](#安裝配置)
  - [Claude Code](#claude-code)
  - [Claude Desktop](#claude-desktop)
  - [Gemini CLI](#gemini-cli)
- [可用工具](#可用工具)
- [使用範例](#使用範例)
- [故障排除](#故障排除)

---

## 簡介

SyncMCP MCP Server 是一個基於 Model Context Protocol (MCP) 的服務，讓 AI 助手可以：

- 🔄 自動同步 MCP 配置
- 📊 檢查配置狀態
- 🔍 分析配置差異
- 💡 提供智能衝突解決建議

**無需手動操作，讓 AI 幫你管理配置！**

---

## 功能特性

### ✅ 4 個核心工具

| 工具 | 功能 | 參數 |
|------|------|------|
| `sync_mcp_configs` | 同步所有客戶端配置 | strategy, dry_run, create_backup |
| `check_sync_status` | 查看所有配置狀態 | 無 |
| `show_config_diff` | 顯示配置差異 | source_client (可選) |
| `suggest_conflict_resolution` | 提供解決建議 | 無 |

### 🎯 智能特性

- **自動備份**: 同步前自動創建備份
- **Dry Run**: 預覽變更而不實際執行
- **類型轉換**: 自動處理不同客戶端的 MCP 類型差異
- **衝突檢測**: 智能識別並建議解決方案

---

## 安裝配置

### 前置要求

1. **安裝 SyncMCP**:
   ```bash
   cd /path/to/SyncMCP
   pip install -e ".[mcp]"
   ```

2. **驗證安裝**:
   ```bash
   python3.12 -c "import mcp; from syncmcp.mcp import server; print('✓ 安裝成功')"
   ```

---

### Claude Code

#### 方法 1: 全域配置（推薦）

編輯 `~/.claude.json`:

```json
{
  "mcpServers": {
    "syncmcp": {
      "type": "stdio",
      "command": "python3.12",
      "args": [
        "-m",
        "syncmcp.mcp.server"
      ]
    }
  }
}
```

#### 方法 2: 專案級配置

在專案目錄創建 `.claude/settings.json`:

```json
{
  "mcpServers": {
    "syncmcp": {
      "type": "stdio",
      "command": "python3.12",
      "args": [
        "-m",
        "syncmcp.mcp.server"
      ]
    }
  }
}
```

#### 驗證配置

1. 重啟 Claude Code
2. 在對話中輸入：「幫我檢查 MCP 配置狀態」
3. 如果 Claude 調用了 `check_sync_status` 工具，表示配置成功 ✅

---

### Claude Desktop

編輯 `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "syncmcp": {
      "command": "python3.12",
      "args": [
        "-m",
        "syncmcp.mcp.server"
      ]
    }
  }
}
```

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**驗證**:
1. 重啟 Claude Desktop
2. 在對話中提到 MCP 配置管理
3. 查看是否有工具調用提示

---

### Gemini CLI

編輯 `~/.gemini/config.json`:

```json
{
  "tools": [
    {
      "name": "syncmcp",
      "type": "mcp",
      "transport": "stdio",
      "command": "python3.12",
      "args": ["-m", "syncmcp.mcp.server"]
    }
  ]
}
```

---

## 可用工具

### 1. sync_mcp_configs

同步所有客戶端的 MCP 配置。

**參數**:
```json
{
  "strategy": "auto",      // "auto" 或 "manual"
  "dry_run": false,        // true 只預覽，false 實際執行
  "create_backup": true    // 是否創建備份
}
```

**使用場景**:
- ✅ 新裝了一個 MCP，想同步到所有客戶端
- ✅ 修改了某個 MCP 的配置，想統一更新
- ✅ 多個客戶端配置不一致，想統一

**範例**:

1. **預覽變更**:
   ```
   用戶: "幫我預覽一下同步 MCP 配置會有什麼變化"
   Claude: 調用 sync_mcp_configs({"dry_run": true})
   ```

2. **執行同步**:
   ```
   用戶: "幫我同步所有 MCP 配置"
   Claude: 調用 sync_mcp_configs({"strategy": "auto"})
   ```

---

### 2. check_sync_status

查看所有客戶端的配置狀態。

**無參數**

**返回信息**:
- 客戶端數量
- MCP 總數
- 各客戶端詳情（路徑、數量、最後修改時間、MCP 列表）

**使用場景**:
- ✅ 想知道有哪些客戶端已配置
- ✅ 查看每個客戶端有多少個 MCP
- ✅ 檢查配置文件是否存在

**範例**:
```
用戶: "幫我檢查一下 MCP 配置狀態"
Claude: 調用 check_sync_status()
```

---

### 3. show_config_diff

顯示所有客戶端之間的配置差異。

**參數**:
```json
{
  "source_client": "Claude Code"  // 可選，指定參考源
}
```

**返回信息**:
- 差異統計（新增、刪除、修改）
- 詳細差異列表
- 警告信息

**使用場景**:
- ✅ 想知道哪些客戶端配置不一致
- ✅ 檢查是否有 MCP 沒同步
- ✅ 分析配置差異原因

**範例**:
```
用戶: "幫我看看各個客戶端的配置有什麼不同"
Claude: 調用 show_config_diff()
```

---

### 4. suggest_conflict_resolution

分析配置差異並提供智能的衝突解決建議。

**無參數**

**提供建議**:
- 新增的 MCP 如何處理
- 刪除的 MCP 是否保留
- 修改的 MCP 如何統一
- 推薦的操作步驟

**使用場景**:
- ✅ 配置差異很多，不知道怎麼處理
- ✅ 想要智能建議而非手動決定
- ✅ 確保操作的安全性

**範例**:
```
用戶: "MCP 配置有點亂，給我一些建議吧"
Claude: 調用 suggest_conflict_resolution()
```

---

## 使用範例

### 場景 1: 新增 MCP 後同步

```
用戶: "我在 Claude Code 中新增了一個 context7 的 MCP，
      幫我同步到其他客戶端"

Claude:
1. 先調用 show_config_diff() 查看差異
2. 發現 context7 只在 Claude Code 中存在
3. 調用 sync_mcp_configs({"strategy": "auto"})
4. 報告同步結果
```

### 場景 2: 檢查並修復不一致

```
用戶: "幫我檢查一下配置狀態，看看有沒有問題"

Claude:
1. 調用 check_sync_status() 查看整體狀態
2. 調用 show_config_diff() 分析差異
3. 調用 suggest_conflict_resolution() 提供建議
4. 詢問用戶是否執行同步
```

### 場景 3: 預覽變更再執行

```
用戶: "我想同步配置，但先讓我看看會改什麼"

Claude:
1. 調用 sync_mcp_configs({"dry_run": true})
2. 顯示預覽結果
3. 詢問是否確認執行
4. 用戶確認後調用 sync_mcp_configs({"strategy": "auto"})
```

---

## 故障排除

### 問題 1: MCP Server 沒有出現在工具列表中

**檢查步驟**:

1. **驗證 Python 版本**:
   ```bash
   python3.12 --version  # 應該 >= 3.10
   ```

2. **驗證 MCP 包安裝**:
   ```bash
   python3.12 -c "import mcp; print(mcp.__version__)"
   ```

3. **手動測試 Server**:
   ```bash
   python3.12 -m syncmcp.mcp.server
   ```
   應該不會報錯，且會等待輸入（Ctrl+C 退出）

4. **檢查配置文件格式**:
   - JSON 格式是否正確
   - 路徑中的斜線是否正確
   - command 路徑是否正確

### 問題 2: 調用工具時報錯

**常見錯誤**:

1. **配置文件不存在**:
   ```
   錯誤: 沒有找到任何配置文件
   解決: 確保至少在一個客戶端中配置了 MCP
   ```

2. **權限問題**:
   ```
   錯誤: Permission denied
   解決: 檢查配置文件和備份目錄的權限
   ```

3. **類型轉換失敗**:
   ```
   錯誤: MCP 類型轉換失敗
   解決: 查看警告信息，某些類型可能不被目標客戶端支援
   ```

### 問題 3: Dry Run 顯示正常但實際同步失敗

**可能原因**:
- 文件權限問題
- 磁碟空間不足
- 配置文件被其他程序佔用

**解決方法**:
```bash
# 查看詳細日誌
cat ~/.syncmcp/logs/syncmcp_*.log

# 手動測試
syncmcp sync --verbose --dry-run
```

---

## 進階配置

### 自定義日誌級別

在配置中添加環境變量：

```json
{
  "mcpServers": {
    "syncmcp": {
      "type": "stdio",
      "command": "python3.12",
      "args": ["-m", "syncmcp.mcp.server"],
      "env": {
        "SYNCMCP_VERBOSE": "true"
      }
    }
  }
}
```

### 指定 Python 路徑

如果 `python3.12` 不在 PATH 中：

```json
{
  "command": "/opt/homebrew/bin/python3.12",
  "args": ["-m", "syncmcp.mcp.server"]
}
```

### 多環境配置

為不同專案使用不同配置：

**專案 A** (`.claude/settings.json`):
```json
{
  "mcpServers": {
    "syncmcp": {
      "type": "stdio",
      "command": "python3.12",
      "args": ["-m", "syncmcp.mcp.server"]
    }
  }
}
```

---

## 安全性考量

### 備份機制

- 每次同步前自動創建備份
- 備份保存在 `~/.syncmcp/backups/`
- 包含完整的配置快照和 metadata

### 權限控制

- MCP Server 僅能訪問配置文件
- 不會修改系統設置
- 所有操作都有日誌記錄

### 恢復機制

如果同步出現問題：

```bash
# 查看可用備份
syncmcp history

# 恢復到指定備份
syncmcp restore <backup-id>
```

---

## 最佳實踐

### ✅ 推薦做法

1. **首次使用前預覽**:
   ```
   "幫我預覽同步 MCP 配置"
   ```

2. **定期檢查狀態**:
   ```
   "檢查 MCP 配置狀態"
   ```

3. **新增 MCP 後立即同步**:
   ```
   "我剛加了一個新 MCP，幫我同步到其他客戶端"
   ```

### ❌ 避免做法

1. 不要在多個客戶端同時修改配置
2. 不要跳過 dry-run 直接同步（第一次使用時）
3. 不要刪除 `~/.syncmcp/backups/` 目錄

---

## 反饋與支持

- **GitHub Issues**: [SyncMCP Issues](https://github.com/yourusername/SyncMCP/issues)
- **文檔**: [README.md](README.md)
- **更新日誌**: [CHANGELOG.md](CHANGELOG.md)

---

**享受 AI 驅動的配置管理體驗！** 🚀
