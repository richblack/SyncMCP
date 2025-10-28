# SyncMCP - 改進需求說明

> 基於測試發現的問題，提出 SyncMCP 工具的改進需求

## 🎯 專案目標

改進 SyncMCP 工具的易用性、可靠性和可訪問性，讓更多用戶（包括非技術背景）能夠輕鬆使用 MCP 配置同步功能。

## 💡 功能想法

### 我希望系統能夠...

1. **全局命令支援**
   - 目前必須在 SyncMCP 目錄內才能執行 `python3 sync-tools/sync-mcp-configs-smart.py`
   - 希望能在任何位置執行同步工具（例如註冊為系統指令或加入 PATH）
   - 理想指令格式：`syncmcp` 或 `sync-mcp`

2. **修正文檔錯誤**
   - README 中提到的 `--yes` 參數實際上不存在
   - 執行時會報錯「--yes 是不認識的」
   - 需要修正文檔中的指令範例，確保用戶能順利使用

3. **配置可見性工具**
   - 同步後發現 Claude Code 的 MCP 列表中大部分配置消失，只剩 ruv-swarm 和 claude-flow
   - 需要一個指令來列出所有 MCP 配置文件的位置（Claude Code、Roo Code、Claude Desktop、Gemini CLI）
   - 最好能直接打開配置文件，方便檢視同步結果是否正確

4. **Terminal 互動式介面**
   - 目前是純命令列工具，對非技術背景用戶不夠友善
   - 希望在 Terminal 中加入互動功能：
     - 使用上下鍵選擇選項
     - Enter 確認、ESC 取消
     - 視覺化的選單和進度顯示
   - 類似 npm init 或其他互動式 CLI 工具的體驗

5. **整合為 MCP Server**
   - 目前需要手動執行 CLI 指令進行同步
   - 希望將 SyncMCP 本身做成 MCP Server
   - 讓 LLM（Claude、Gemini 等）可以直接調用同步功能
   - 實現「對話式配置管理」

### 使用情境

**情境 1：新手用戶安裝後**
- 用戶安裝完 SyncMCP 後，可以直接在終端輸入 `syncmcp` 啟動互動式介面
- 系統引導用戶完成首次同步，無需記憶複雜的 Python 指令

**情境 2：檢查同步結果**
- 執行同步後，用戶輸入 `syncmcp status` 或 `syncmcp list`
- 系統顯示所有客戶端的配置文件路徑和同步狀態
- 用戶可選擇打開某個配置文件檢視

**情境 3：在 Claude 中管理 MCP**
- 用戶對 Claude 說：「幫我同步所有 MCP 配置」
- Claude 通過 MCP Server 調用 SyncMCP 工具
- 自動完成同步並報告結果

## 🛠 技術偏好

- **語言/框架**: Python（保持與現有工具一致）
- **CLI 框架**: 考慮使用 `click` 或 `typer`（互動式介面）、`rich`（美化輸出）
- **MCP Server**: 使用 FastMCP（與 image-gen-mcp 一致）

## 📎 參考資料

- 測試問題記錄：`user-requirements/docs/test.md`
- 現有工具：`sync-tools/sync-mcp-configs-smart.py`
- MCP Server 範例：`mcp-sources/image-gen-mcp/`
