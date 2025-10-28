# Claude Flow 開發指南

## 🎯 開發流程

### 1. 開始前必讀
- **永遠先閱讀 `rfp/` 目錄**：理解需求後再開始開發
- **使用記憶系統**：重要決策和進度都要記錄

### 2. 標準開發流程

```bash
# 啟動時 - 恢復記憶
claude-flow memory recall "*"

# 閱讀需求
# 請仔細閱讀 rfp/ 目錄中的所有需求文件

# 規劃架構
claude-flow sparc run architect "根據 rfp/ 需求設計架構"

# 開始開發
claude-flow sparc run coder "實作功能"

# 測試
claude-flow sparc run tdd "建立測試"

# 結束時 - 保存記憶
claude-flow memory store "progress" "今日完成：XXX"
```

## 🔔 通知規則

### 何時必須主動詢問用戶

1. **需要決策時**
   - 多種實作方案可選擇
   - 架構設計的重要決定
   - 技術棧選擇

2. **遇到阻礙時**
   - 錯誤無法自行解決
   - 需求不清楚
   - 測試失敗且原因不明

3. **完成階段性任務時**
   - 完成一個主要功能
   - 完成測試
   - 準備部署

### 通知方式

當需要用戶注意時：
- 系統會自動彈出通知（透過 hooks）
- 在訊息中明確說明需要什麼
- 等待用戶回應後再繼續

## 📋 最佳實踐

### Do ✅
- 先讀 rfp/ 再動手
- 重要決策記錄到 memory
- 需要確認時主動詢問
- 階段完成後通知用戶

### Don't ❌
- 不要假設需求，有疑問就問
- 不要跳過測試
- 不要在不確定時繼續開發
- 不要忘記保存記憶

## 💾 記憶系統使用

```bash
# 保存架構決策
claude-flow memory store "architecture" "使用 微服務架構，API Gateway + 3個服務"

# 保存技術棧
claude-flow memory store "tech-stack" "Node.js + PostgreSQL + Redis"

# 保存進度
claude-flow memory store "progress" "完成用戶認證模組"

# 保存問題
claude-flow memory store "issues" "資料庫連線池需要優化"

# 查詢特定記憶
claude-flow memory query "architecture"

# 恢復所有記憶
claude-flow memory recall "*"
```

## 🚨 特別注意

1. **上下文壓縮後的恢復**
   - 如果忘記之前的工作，立即執行：`claude-flow memory recall "*"`
   - 重新閱讀 `rfp/requirements.md`

2. **長時間執行的任務**
   - 定期報告進度
   - 階段完成時通知用戶

3. **需要用戶介入**
   - 系統會自動觸發通知
   - 明確說明需要什麼決策或行動

## 🔧 SyncMCP 專案：關鍵技術知識

### ⚠️ MCP 客戶端特性差異（絕對不可忘記）

這些是不同 AI 客戶端對 MCP 的支援差異，**必須在同步時正確處理**：

#### 1. Claude Code
- ✅ **配置層級**：支援全域 (`~/.claude.json`) 和專案級別 (`.claude/settings.json`)
- ✅ **Transport 類型**：完整支援 `stdio`、`sse`、`http`
- ❌ **不支援** `streamable-http`（這是 Roo Code 專有）
- 🔍 **檢查規則**：如果在 Claude Code 配置中看到 `streamable-http`，表示**同步出錯**

#### 2. Claude Desktop
- ✅ **配置層級**：僅支援全域配置
- ✅ **Transport 類型**：**僅支援 `stdio`**
- ❌ **不支援**：`http`、`sse`、`streamable-http` 等所有遠端類型
- 🔍 **同步規則**：必須**過濾掉**所有非 stdio 的 MCP

#### 3. Gemini CLI
- ✅ **配置層級**：**僅支援全域配置**（無專案級別）
- ⚠️ **Transport 類型**：主要支援 `stdio`，`http`/`sse` 未測試
- 🔍 **同步規則**：不要同步專案級別的配置

#### 4. Roo Code
- ✅ **配置層級**：支援全域和專案級別
- ✅ **Transport 類型**：主要支援 `stdio`
- ✅ **特殊類型**：使用 **`streamable-http`**（Roo Code 專有）
- ⚠️ **HTTP 支援**：未完全測試，但如果支援，**必須是 `streamable-http`** 而非 `http`
- 🔍 **轉換規則**：
  - 從 Claude Code 同步到 Roo Code：`http`/`sse` → `streamable-http`
  - 從 Roo Code 同步到 Claude Code：`streamable-http` → `http` 或 `sse`

### 📊 類型轉換對照表

| 來源客戶端 | 目標客戶端 | 轉換規則 |
|-----------|-----------|---------|
| Roo Code | Claude Code | `streamable-http` → `http` (有 headers) 或 `sse` (無 headers) |
| Claude Code | Roo Code | `http`/`sse` → `streamable-http` |
| 任何 | Claude Desktop | **過濾掉所有非 stdio** 的 MCP |
| 任何 | Gemini | 僅同步全域配置，不同步專案級 |

### 🚨 常見錯誤模式（必須避免）

#### 錯誤 1: Claude Code 中出現 `streamable-http`
```json
// ❌ 錯誤 - 這會導致 schema validation 失敗
{
  "mcpServers": {
    "canva": {
      "type": "streamable-http",  // Claude Code 不認識
      "url": "https://mcp.canva.com/mcp"
    }
  }
}

// ✅ 正確 - 應該轉換為 sse 或 http
{
  "mcpServers": {
    "canva": {
      "type": "sse",  // 或 "http"（如果有 headers）
      "url": "https://mcp.canva.com/mcp"
    }
  }
}
```

#### 錯誤 2: Roo Code 中使用 `http`
```json
// ❌ 錯誤 - Roo Code 需要 streamable-http
{
  "mcpServers": {
    "context7": {
      "type": "http",  // 應該是 streamable-http
      "url": "https://mcp.context7.com/mcp"
    }
  }
}

// ✅ 正確
{
  "mcpServers": {
    "context7": {
      "type": "streamable-http",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

#### 錯誤 3: 將 HTTP MCP 同步到 Claude Desktop
```python
# ❌ 錯誤 - Desktop 不支援 HTTP
def sync_to_desktop(mcpServers):
    return mcpServers  # 會包含 http/sse 類型

# ✅ 正確 - 必須過濾
def sync_to_desktop(mcpServers):
    return {
        name: config
        for name, config in mcpServers.items()
        if config.get('type') == 'stdio'
    }
```

### 💡 實作檢查清單

開發 SyncMCP 功能時，**每次都要確認**：

- [ ] Roo Code → Claude Code 時，是否正確轉換 `streamable-http`？
- [ ] Claude Code → Roo Code 時，是否將 `http`/`sse` 轉為 `streamable-http`？
- [ ] 同步到 Claude Desktop 時，是否過濾掉所有非 stdio MCP？
- [ ] 同步到 Gemini 時，是否僅同步全域配置？
- [ ] 是否在轉換後驗證配置的 schema？
- [ ] 是否記錄轉換日誌，方便 debug？

### 📚 相關文檔

- **詳細說明**：[rfp/bug-fix-mcp-type-conversion.md](rfp/bug-fix-mcp-type-conversion.md)
- **實作位置**：`syncmcp/core/config_manager.py` 的各個 Adapter
- **測試案例**：`tests/test_type_conversion.py`（待建立）

---

**記住**：通知功能已透過 `.claude/settings.json` 的 hooks 配置，
不受上下文壓縮影響，會穩定運作！

**更重要**：這些 MCP 類型轉換規則是**核心業務邏輯**，違反會導致客戶端無法載入 MCP！
