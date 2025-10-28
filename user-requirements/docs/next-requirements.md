# SyncMCP - 未來功能需求

## 功能 1: MCP 健康檢查與自動修復 (Doctor Mode)

### 優先級
高 (5/5 星)

### 問題描述
MCP 經常因為小問題導致連接失敗（Node 版本、Python 依賴、路徑錯誤、type 不匹配等），每次開始工作前都要花時間診斷和修復這些問題，嚴重影響工作效率。

例如：2025-10-28 花了整個早上處理 chrome-devtools、google-workspace、context7 等 MCP 的連接問題。

### 目標
- 自動檢測所有 MCP 的健康狀態
- 自動診斷常見問題（Node 版本、依賴缺失、路徑錯誤、type 不匹配等）
- 自動修復簡單和中等問題
- 對複雜問題提供修復建議，或呼叫 AI 協助診斷

### 核心功能

#### Phase 1: 基礎健康檢查
```bash
syncmcp doctor                 # 檢查所有 MCP 狀態
syncmcp doctor --verbose       # 顯示詳細診斷資訊
syncmcp doctor --client=claude-code  # 僅檢查特定客戶端
```

檢查項目：
- 掃描所有 MCP 配置（Claude Code, Roo Code, Desktop, Gemini）
- 逐一嘗試啟動每個 MCP 進程
- 檢測 MCP 是否回應 initialize 請求
- 記錄錯誤訊息和堆疊追蹤
- 分類問題嚴重程度（正常/警告/錯誤）

#### Phase 2: 自動修復
```bash
syncmcp doctor --fix           # 自動修復所有可修復的問題
syncmcp doctor --fix --dry-run # 預覽修復操作，不實際執行
syncmcp doctor --interactive   # 交互式修復，每個問題詢問用戶
```

修復策略：
1. **簡單問題（自動修復）**：Type 轉換錯誤、相對路徑錯誤
2. **中等問題（自動修復）**：Node 版本問題、Python 依賴問題
3. **複雜問題（提供建議）**：API Key 無效、連接超時、未知錯誤

#### Phase 3: AI 協助診斷
```bash
syncmcp doctor --ai-assist     # 使用 AI 協助診斷複雜問題
syncmcp doctor --ai=claude     # 指定使用的 AI CLI
```

前提條件：
- 用戶已安裝 AI CLI（claude, aider, cursor 等）
- 或者使用 API（需要配置 API Key）

#### Phase 4: 背景監控（選用）
```bash
syncmcp monitor start          # 啟動背景監控
syncmcp monitor stop           # 停止監控
syncmcp monitor status         # 查看監控狀態
```

### 錯誤診斷引擎

支援的錯誤類型：

| 錯誤類型 | 檢測方式 | 嚴重程度 | 可自動修復 |
|---------|---------|---------|-----------|
| Node 版本不符 | 解析 "does not support Node vX.X.X" | 中等 | 是 |
| Python 依賴缺失 | 解析 "ModuleNotFoundError" | 中等 | 是 |
| 路徑錯誤 | 解析 "ENOENT: no such file" | 簡單 | 是 |
| Type 不匹配 | 解析 "Invalid input" / schema error | 簡單 | 是 |
| API Key 無效 | 解析 "401 Unauthorized" | 警告 | 否 |
| 連接超時 | 解析 "Connection closed" / timeout | 中等 | 可能 |

### 使用場景

#### 場景 1: 每日工作開始前
```bash
$ syncmcp doctor

正在檢查 MCP 健康狀態...
✅ 10/10 MCP 正常運作
可以開始工作了！
```

#### 場景 2: MCP 無法連接
```bash
$ syncmcp doctor --verbose

❌ chrome-devtools (stdio) - 錯誤
   錯誤: chrome-devtools-mcp does not support Node v22.7.0
   建議: 需要 Node >= 22.12.0

$ syncmcp doctor --fix

正在修復 chrome-devtools...
  1. 找到 Node v22.21.0
  2. 建立 wrapper script
  3. 更新配置
  4. 測試連接... ✅ 成功！
```

#### 場景 3: 複雜問題需要 AI 協助
```bash
$ syncmcp doctor --ai-assist

正在請教 AI...

AI 診斷結果：
  問題: custom-mcp 缺少 Node.js 依賴 @anthropic/sdk
  建議修復步驟：
  1. cd /path/to/custom-mcp
  2. npm install @anthropic/sdk

是否執行這些命令？[y/N] y

正在執行修復...
✅ custom-mcp 現在可以正常運作！
```

### 實作階段

#### Phase 1: 基礎健康檢查（預計 1-2 天）
- 實作 `syncmcp doctor` CLI 命令
- 實作 MCP 測試框架（stdio + http/sse）
- 實作基本錯誤偵測
- 實作報告生成器

#### Phase 2: 自動修復（預計 2-3 天）
- 實作錯誤診斷引擎（pattern matching）
- 實作簡單問題修復（type, path）
- 實作中等問題修復（Node, Python）
- 實作修復驗證（重新測試）

#### Phase 3: AI 協助（預計 1-2 天）
- 實作 AI CLI 檢測
- 設計提示詞模板
- 實作 AI 請求和回應解析
- 實作交互式確認

#### Phase 4: 背景監控（預計 2-3 天，選用）
- 實作 daemon 模式
- 實作定時檢查機制
- 整合桌面通知
- 實作健康日誌

### 相關文件
- `docs/doctor-mode.md` - Doctor 模式完整文件
- `docs/troubleshooting.md` - 常見問題和手動修復方案
- `docs/ai-assistant.md` - AI 協助使用指南

---

**需求提出日期**: 2025-10-28
**提出人**: User
**狀態**: 待實作
**優先級**: 高 (5/5 星)
