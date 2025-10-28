# 快速移動 MCP 到全域 - 給 Claude Code 的指令

## 🎯 目的

將專案級別的 MCP 移動到全域，讓 SyncMCP 能夠同步到其他客戶端。

---

## ⚡ 快速步驟（3 分鐘）

### 如果你知道 MCP 名稱（例如：chrome-devtools）

```bash
# 1. 在專案目錄中刪除 MCP
cd /Users/youlinhsieh/Documents/tech_projects/AIPM-Client
claude mcp remove chrome-devtools

# 2. 切換到非專案目錄
cd ~

# 3. 重新新增到全域
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest

# 4. 驗證
claude mcp list | grep chrome-devtools

# 5. 同步到其他客戶端
syncmcp sync
```

**完成！** ✅

---

## 📋 如果不確定有哪些專案 MCP

```bash
# 1. 列出所有專案及其 MCP
cat ~/.claude.json | jq '.projects | to_entries[] | select(.value.mcpServers != null and .value.mcpServers != {}) | {project: .key, mcps: (.value.mcpServers | keys)}'

# 2. 查看特定專案的 MCP
cat ~/.claude.json | jq '.projects["/Users/youlinhsieh/Documents/tech_projects/AIPM-Client"].mcpServers'

# 3. 記下輸出的 MCP 名稱，然後對每個 MCP 執行上面的快速步驟
```

---

## 🔍 驗證是否成功

```bash
# 檢查 1: MCP 在全域配置中
cat ~/.claude.json | jq '.mcpServers | keys' | grep chrome-devtools

# 檢查 2: MCP 不在專案配置中（應該返回 null 或空）
cat ~/.claude.json | jq '.projects["/Users/youlinhsieh/Documents/tech_projects/AIPM-Client"].mcpServers.["chrome-devtools"]'

# 檢查 3: SyncMCP 可以看到
syncmcp list | grep chrome-devtools

# 檢查 4: 可以同步
syncmcp sync --dry-run
```

---

## 🚨 重要提醒

### 為什麼要移動？
- SyncMCP 目前**只支援全域 MCP**（Bug #13）
- 專案級別的 MCP **不會被同步**到 Roo Code、Claude Desktop、Gemini

### 移動後的影響
- ✅ 該 MCP 在**所有專案**都可用（不再專屬於某個專案）
- ✅ 可以被 SyncMCP 同步到其他客戶端
- ⚠️ 如果需要專案隔離，等待 Bug #13 修復

### 哪些 MCP 應該移動？
- ✅ 通用工具（filesystem, notion, context7）
- ✅ 需要在多個客戶端使用的 MCP
- ❌ 專案特定的測試工具（可以保留在專案級別，但不會同步）

---

## 🛟 出問題了？

### 恢復備份
```bash
# 如果移動前沒有備份，現在備份
cp ~/.claude.json ~/.claude.json.backup

# 恢復到之前的備份
cp ~/.claude.json.backup.XXXXXXXX ~/.claude.json
```

### MCP 消失了？
```bash
# 檢查是否還在專案級別
cat ~/.claude.json | jq '.projects | to_entries[] | select(.value.mcpServers != null) | {project: .key, mcps: (.value.mcpServers | keys)}'

# 檢查是否在全域
cat ~/.claude.json | jq '.mcpServers | keys'
```

### 需要詳細說明？
查看完整文檔：`docs/MOVE-MCP-TO-GLOBAL.md`

---

## 📝 範例：移動 chrome-devtools

```bash
# 當前狀態：chrome-devtools 在 AIPM-Client 專案中
$ cat ~/.claude.json | jq '.projects["/Users/youlinhsieh/Documents/tech_projects/AIPM-Client"].mcpServers.["chrome-devtools"]'
{
  "type": "stdio",
  "command": "npx",
  "args": ["chrome-devtools-mcp@latest"]
}

# 步驟 1: 刪除專案級別
$ cd /Users/youlinhsieh/Documents/tech_projects/AIPM-Client
$ claude mcp remove chrome-devtools
✓ Removed chrome-devtools

# 步驟 2: 切換目錄
$ cd ~

# 步驟 3: 新增到全域
$ claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
✓ Added chrome-devtools

# 步驟 4: 驗證
$ cat ~/.claude.json | jq '.mcpServers.["chrome-devtools"]'
{
  "type": "stdio",
  "command": "npx",
  "args": ["chrome-devtools-mcp@latest"]
}

# 步驟 5: 同步
$ syncmcp sync
✓ 已同步到 4 個客戶端
```

**完成！** 🎉

---

**快速鏈接**：
- 完整文檔: [MOVE-MCP-TO-GLOBAL.md](./MOVE-MCP-TO-GLOBAL.md)
- Bug 報告: [BUG-13-project-level-mcp.md](../rfp/BUG-13-project-level-mcp.md)
