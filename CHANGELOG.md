# Changelog

All notable changes to SyncMCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- **Doctor Mode**: MCP 健康檢查與自動修復功能
- **Background Monitor**: 背景監控 daemon 模式
- **AI Assistant**: AI 協助診斷複雜問題

## [2.0.0] - 2025-10-28

### 🎉 Major Rewrite

Complete rewrite of SyncMCP from a single script to a modular Python package.

### ✨ Added

#### Core Features
- **Intelligent Sync Engine**: 自動檢測最新配置源並同步到所有客戶端
- **Diff Detection**: 智能差異檢測（新增/移除/修改）
- **Automatic Backup**: 同步前自動備份，支援恢復功能
- **Config Manager**: 統一的配置管理介面，支援 4 種客戶端
  - Claude Code (`~/.claude.json`)
  - Roo Code (Roo Code settings)
  - Claude Desktop (Claude Desktop config)
  - Gemini CLI (Gemini MCP config)

#### CLI Commands
- `syncmcp sync`: 執行配置同步
- `syncmcp status`: 查看配置狀態
- `syncmcp list`: 列出所有 MCP 配置
- `syncmcp diff`: 顯示配置差異
- `syncmcp doctor`: 系統診斷工具
- `syncmcp history`: 查看同步歷史
- `syncmcp interactive`: 啟動 TUI 介面

#### TUI (Terminal User Interface)
- 互動式主選單
- 友善的錯誤提示
- 進度條顯示
- 鍵盤導航支援

#### MCP Server Integration
- `syncmcp mcp`: 啟動 MCP Server 的 CLI 指令
- `sync_mcp_configs`: 同步配置工具
- `check_sync_status`: 檢查狀態工具
- `show_config_diff`: 顯示差異工具
- `suggest_conflict_resolution`: 衝突解決建議
- `get_setup_guide`: MCP 設置指南查詢
- `troubleshoot_mcp`: MCP 問題診斷與修復建議

#### Development Tools
- **GitHub Actions CI/CD**: 多環境自動化測試
- **Pre-commit Hooks**: 本地代碼品質檢查
- **Makefile**: 20+ 個開發指令
- **Test Suite**: 92 個測試（79% 通過率）

#### Documentation
- **USER-GUIDE.md**: 完整使用者指南
- **DEVELOPER-GUIDE.md**: 開發者指南
- **MCP_INTEGRATION.md**: MCP 整合文檔
- **API.md**: API 參考文件
- **EXAMPLES.md**: 使用範例
- **PUBLISHING.md**: 發布指南

### 🔧 Changed
- 從單一腳本遷移到模組化套件結構
- 使用 Click 實現 CLI（取代 argparse）
- 使用 Rich 美化輸出
- 使用 InquirerPy 實現 TUI

### 🛠️ Technical Improvements
- Python 3.10+ 支援
- Type hints 完整覆蓋
- 完整的錯誤處理機制
- 日誌系統（支援 DEBUG/INFO/WARNING/ERROR）
- 配置驗證和警告檢測
- 自動類型轉換（http/sse/streamable-http）

### 📦 Package Structure
```
syncmcp/
├── core/           # 核心功能
│   ├── config_manager.py
│   ├── diff_engine.py
│   ├── backup_manager.py
│   └── sync_engine.py
├── tui/            # Terminal UI
│   └── interface.py
├── mcp/            # MCP Server
│   └── server.py
├── utils/          # 工具函數
│   ├── logger.py
│   └── errors.py
└── cli.py          # CLI 入口
```

### 🐛 Bug Fixes
- 修正 README.md 中的 `--yes` 參數錯誤
- 修正 Node 路徑問題（絕對路徑 → 相對路徑）
- 修正 MCP type 不匹配問題
- 修正專案級別 MCP 配置未同步的問題
- 修正 Claude Desktop 僅支援 stdio 的過濾
- **修正 MCP Server 無法連接的問題**：添加缺失的 `syncmcp mcp` CLI 指令（關鍵修復）

### 🔐 Security
- 實作 Bandit 安全掃描
- 配置檔案權限檢查
- 備份完整性驗證

### ⚡ Performance
- 使用 MD5 雜湊優化差異檢測
- 備份自動清理（保留最近 10 個）
- 日誌輪轉（每個文件最大 10MB）

### 📈 Testing
- 單元測試：config_manager, diff_engine, backup_manager
- 整合測試：完整同步流程
- CLI 測試：所有命令
- MCP 測試：工具註冊和調用
- 覆蓋率：79% (51/72 tests passing)

### 🚀 CI/CD
- GitHub Actions workflow
- Multi-matrix testing (Python 3.10-3.12, Ubuntu/macOS)
- Black formatting check
- Ruff linting
- MyPy type checking
- pytest with coverage
- Build verification with twine

## [1.0.0] - 2025-01-20 (Legacy)

### ✨ Initial Release

Original single-script implementation: `sync-mcp-configs-smart.py`

Features:
- Basic configuration sync
- Simple diff detection
- Manual source selection

### Deprecated
This version is deprecated. Users should migrate to 2.0.0.

---

## Version Comparison

| Feature | v1.0 (Legacy) | v2.0 (Current) |
|---------|---------------|----------------|
| Architecture | Single script | Modular package |
| CLI | Basic argparse | Full Click CLI |
| UI | Plain text | Rich + TUI |
| MCP Integration | ❌ | ✅ |
| Auto Backup | ❌ | ✅ |
| History Tracking | ❌ | ✅ |
| Test Coverage | 0% | 79% |
| CI/CD | ❌ | ✅ |
| Documentation | Basic README | Complete docs |

## Migration Guide (v1.0 → v2.0)

### Installation

**v1.0**:
```bash
python sync-mcp-configs-smart.py
```

**v2.0**:
```bash
pip install syncmcp
syncmcp sync
```

### Command Mapping

| v1.0 | v2.0 |
|------|------|
| `python sync-mcp-configs-smart.py` | `syncmcp sync` |
| (manual inspection) | `syncmcp status` |
| (manual diff) | `syncmcp diff` |
| N/A | `syncmcp doctor` |
| N/A | `syncmcp interactive` |

### Configuration

v1.0 和 v2.0 使用相同的配置文件格式，無需遷移。

### Breaking Changes

無重大不相容變更。v2.0 完全向後相容 v1.0 的配置文件。

---

[Unreleased]: https://github.com/yourusername/SyncMCP/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/yourusername/SyncMCP/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/yourusername/SyncMCP/releases/tag/v1.0.0
