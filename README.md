# MCP 配置同步工具 🚀

一個簡單實用的工具，用於統一管理多個 AI 客戶端的 MCP (Model Context Protocol) 配置。

## 問題

每個 AI Agent（Claude Desktop、Claude Code、Gemini CLI 等）都有各自的 MCP Server 設定檔。雖然使用的設定大同小異，但每次都要分別設定非常麻煩且容易出錯。

## 解決方案

測試了幾個現有工具都無法完美解決，於是開發了這個簡單的同步工具。實測有效，在此分享。

> 100% 由 Claude 開發

## 支援的客戶端

- 🔵 **Claude Code**
- 🟣 **Roo Code**
- ⚫ **Claude Desktop** (不支援 HTTP MCPs)
- 🔴 **Gemini CLI**

## 快速開始

### 安裝

```bash
git clone https://github.com/yourusername/SyncMCP.git
cd SyncMCP
```

### 同步所有客戶端

```bash
python3 sync-tools/sync-mcp-configs-smart.py --yes
```

這會：
- ✅ 自動選擇最新的配置版本
- ✅ 智能處理不同客戶端的格式差異
- ✅ 自動備份所有變更
- ✅ 同步到 4 個客戶端

## 主要功能

### 1. 智能同步

基於時間戳自動選擇最新配置，並同步到所有客戶端：

```bash
python3 sync-tools/sync-mcp-configs-smart.py --yes
```

### 2. 添加/修改 MCP

在任一客戶端添加或修改 MCP 後，執行同步即可。系統會自動選擇最新修改的版本同步到其他客戶端：

```bash
# 在任一客戶端添加/修改 MCP
# 然後同步
python3 sync-tools/sync-mcp-configs-smart.py --yes
```

**工作原理**：智能同步會比較每個客戶端的配置修改時間，自動選擇最新的版本覆蓋其他客戶端。

### 3. 自動備份

所有變更自動備份到 `backup/` 目錄：

```bash
# 查看備份
ls -lt backup/

# 恢復備份
cp backup/claude-code_smart_TIMESTAMP.json ~/.claude.json
```

## 配置文件位置

| 客戶端 | 配置文件路徑 |
|--------|--------------|
| Claude Code | `~/.claude.json` |
| Roo Code | `~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Gemini CLI | `~/.gemini/settings.json` |

## 故障排除

### MCP 無法連接

1. 檢查配置格式是否正確
2. 確認 API 憑證是否有效
3. 重啟客戶端載入新配置

### 配置損壞

```bash
# 從最新備份恢復
cp backup/claude-code_smart_*.json ~/.claude.json
```

## 相關資源

- [MCP 官方文檔](https://modelcontextprotocol.io/)
- [Claude Code](https://docs.claude.com/)
- [Gemini CLI](https://ai.google.dev/)

## License

MIT

---

**狀態**: ✅ 正常運作
**最後更新**: 2025-10-24
