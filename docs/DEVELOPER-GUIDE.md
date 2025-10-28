# SyncMCP 開發者指南

> **版本**: 2.0.0
> **更新日期**: 2025-10-29

## 📋 目錄

- [開發環境設定](#開發環境設定)
- [專案架構](#專案架構)
- [核心概念](#核心概念)
- [開發工作流程](#開發工作流程)
- [測試指南](#測試指南)
- [貢獻指南](#貢獻指南)
- [發布流程](#發布流程)

---

## 🛠️ 開發環境設定

### 系統需求

- **Python**: >= 3.10
- **pip**: 最新版本
- **git**: 用於版本控制
- **推薦編輯器**: VSCode, PyCharm

### 1. Clone 專案

```bash
git clone https://github.com/yourusername/syncmcp.git
cd syncmcp
```

### 2. 建立虛擬環境

```bash
# 使用 venv
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 或使用 conda
conda create -n syncmcp python=3.12
conda activate syncmcp
```

### 3. 安裝開發依賴

```bash
# 安裝所有依賴（包括開發工具）
pip install -e ".[dev]"

# 或分別安裝
pip install -e .
pip install pytest pytest-asyncio pytest-cov
pip install black ruff mypy
```

### 4. 驗證安裝

```bash
# 檢查 CLI
syncmcp --version
syncmcp doctor

# 執行測試
pytest

# 檢查程式碼品質
black --check syncmcp/
ruff check syncmcp/
```

---

## 🏗️ 專案架構

### 目錄結構

```
syncmcp/
├── syncmcp/                 # 主要原始碼
│   ├── __init__.py
│   ├── cli.py              # CLI 命令入口
│   ├── core/               # 核心功能
│   │   ├── config_manager.py   # 配置管理
│   │   ├── diff_engine.py      # 差異偵測
│   │   ├── sync_engine.py      # 同步引擎
│   │   └── backup_manager.py   # 備份管理
│   ├── mcp/                # MCP Server
│   │   └── server.py
│   ├── tui/                # 互動介面
│   │   ├── __init__.py
│   │   └── interactive.py
│   └── utils/              # 工具函數
│       └── helpers.py
├── tests/                  # 測試檔案
│   ├── conftest.py         # pytest fixtures
│   ├── test_config_manager.py
│   ├── test_diff_engine.py
│   ├── test_sync_engine.py
│   ├── test_backup_manager.py
│   ├── test_cli.py
│   └── test_mcp_server.py
├── docs/                   # 文檔
│   ├── USER-GUIDE.md
│   ├── DEVELOPER-GUIDE.md
│   ├── API.md
│   └── EXAMPLES.md
├── rfp/                    # 需求規格
│   ├── requirements.md
│   ├── tasks.md
│   └── bug-reports/
├── pyproject.toml          # 專案配置
├── README.md
└── CHANGELOG.md
```

### 模組說明

#### `syncmcp/core/config_manager.py`

**職責**: 管理所有客戶端的配置載入、保存、轉換

**核心類別**:
- `ClientConfig`: 配置資料結構
- `BaseConfigAdapter`: 抽象基類
- `ClaudeCodeAdapter`: Claude Code 配置
- `ClaudeDesktopAdapter`: Claude Desktop 配置
- `RooCodeAdapter`: Roo Code 配置
- `GeminiAdapter`: Gemini CLI 配置
- `ConfigManager`: 統一配置管理

**關鍵方法**:
```python
class ConfigManager:
    def load(self, client_name: str) -> ClientConfig
    def save(self, client_name: str, config: ClientConfig)
    def load_all(self) -> Dict[str, ClientConfig]
```

---

#### `syncmcp/core/diff_engine.py`

**職責**: 偵測配置差異，生成差異報告

**核心類別**:
- `DiffType`: 差異類型枚舉（ADDED, REMOVED, MODIFIED）
- `DiffItem`: 單一差異項目
- `DiffReport`: 完整差異報告
- `DiffEngine`: 差異偵測引擎

**關鍵方法**:
```python
class DiffEngine:
    def analyze(self, configs: Dict[str, ClientConfig]) -> DiffReport
    def select_source(self, configs: Dict[str, ClientConfig], strategy: str) -> str
```

---

#### `syncmcp/core/sync_engine.py`

**職責**: 執行同步邏輯，協調各模組

**核心類別**:
- `SyncStrategy`: 同步策略枚舉
- `SyncResult`: 同步結果
- `SyncEngine`: 同步引擎

**關鍵方法**:
```python
class SyncEngine:
    def sync(
        self,
        strategy: SyncStrategy = SyncStrategy.AUTO,
        dry_run: bool = False,
        create_backup: bool = True
    ) -> SyncResult
```

---

#### `syncmcp/core/backup_manager.py`

**職責**: 管理配置備份和恢復

**核心類別**:
- `BackupManager`: 備份管理器

**關鍵方法**:
```python
class BackupManager:
    def create(self, adapters: List[BaseConfigAdapter]) -> str
    def restore(self, backup_path: str, adapters: List[BaseConfigAdapter])
    def list(self) -> List[Dict]
    def cleanup(self, keep: int = 10)
```

---

#### `syncmcp/cli.py`

**職責**: CLI 命令入口

**技術**: Click 框架 + Rich 輸出

**命令清單**:
- `sync`: 同步配置
- `status`: 顯示狀態
- `list`: 列出 MCP
- `diff`: 顯示差異
- `doctor`: 系統診斷
- `history`: 同步歷史
- `restore`: 恢復備份
- `interactive`: 互動模式
- `open`: 打開配置檔案

---

#### `syncmcp/mcp/server.py`

**職責**: MCP Server 實作

**技術**: MCP SDK (Model Context Protocol)

**工具清單**:
- `sync_mcp_configs`: 同步配置
- `check_sync_status`: 檢查狀態
- `show_config_diff`: 顯示差異
- `suggest_conflict_resolution`: 建議解決方案

---

#### `syncmcp/tui/interactive.py`

**職責**: 終端互動介面

**技術**: InquirerPy + Rich

**功能**:
- 互動式選單
- 即時狀態顯示
- 視覺化差異比較
- 歷史記錄瀏覽

---

## 🧠 核心概念

### 1. 配置 Adapter 模式

SyncMCP 使用 Adapter 模式處理不同客戶端的配置差異。

```python
class BaseConfigAdapter(ABC):
    """配置 Adapter 基類"""

    @abstractmethod
    def get_config_path(self) -> Path:
        """取得配置檔案路徑"""
        pass

    @abstractmethod
    def load(self) -> ClientConfig:
        """載入配置"""
        pass

    @abstractmethod
    def save(self, config: ClientConfig):
        """保存配置"""
        pass
```

每個客戶端實作自己的 Adapter：

```python
class ClaudeCodeAdapter(BaseConfigAdapter):
    def get_config_path(self) -> Path:
        return Path.home() / ".claude.json"

    def load(self) -> ClientConfig:
        # 載入並解析 ~/.claude.json
        pass

    def save(self, config: ClientConfig):
        # 保存到 ~/.claude.json
        pass
```

---

### 2. MCP Transport 類型轉換

不同客戶端支援不同的 MCP transport 類型。SyncMCP 自動轉換：

| 來源客戶端 | 目標客戶端 | 轉換規則 |
|-----------|-----------|---------|
| Roo Code | Claude Code | `streamable-http` → `http` 或 `sse` |
| Claude Code | Roo Code | `http`/`sse` → `streamable-http` |
| 任何 | Claude Desktop | 過濾掉所有非 `stdio` |
| 任何 | Gemini | 僅同步全域配置 |

**實作位置**: `syncmcp/core/config_manager.py` 各 Adapter

**範例**:
```python
class RooCodeAdapter(BaseConfigAdapter):
    def _convert_from_streamable_http(self, server_config: Dict) -> Dict:
        """Roo Code → Claude Code: streamable-http → http/sse"""
        if server_config.get("type") == "streamable-http":
            # 有 headers → http
            if "headers" in server_config:
                server_config["type"] = "http"
            # 無 headers → sse
            else:
                server_config["type"] = "sse"
        return server_config
```

---

### 3. 差異偵測策略

`DiffEngine` 分析配置差異：

1. **收集所有 MCP 名稱**
2. **逐個比較配置**
3. **分類差異類型**:
   - `ADDED`: 某些客戶端有，某些沒有
   - `REMOVED`: 某些客戶端沒有，某些有
   - `MODIFIED`: 配置內容不同
4. **生成差異報告**

---

### 4. 同步策略

#### AUTO 策略（預設）

自動選擇最新的配置作為來源：

```python
def select_source(self, configs, strategy="auto"):
    if strategy == "auto":
        # 選擇最新修改時間的配置
        return max(configs, key=lambda c: c.last_modified)
```

#### MANUAL 策略

逐個確認每個變更：

```python
def sync_manual(self, diff_report):
    for diff in diff_report.diffs:
        # 詢問用戶是否執行此變更
        if confirm(f"Apply {diff}?"):
            apply_change(diff)
```

---

### 5. 備份機制

每次同步前自動建立備份：

```python
def sync(self, dry_run=False, create_backup=True):
    if create_backup and not dry_run:
        backup_path = self.backup_manager.create(adapters)

    try:
        # 執行同步
        ...
    except Exception as e:
        # 發生錯誤，自動回滾
        if backup_path:
            self.backup_manager.restore(backup_path, adapters)
```

**備份保留策略**: 自動保留最新 10 個備份

---

## 🔄 開發工作流程

### 1. 建立新功能

```bash
# 建立新分支
git checkout -b feature/new-feature

# 開發功能
# ... 編輯程式碼 ...

# 執行測試
pytest tests/

# 檢查程式碼品質
black syncmcp/
ruff check syncmcp/

# 提交
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### 2. 修復 Bug

```bash
# 建立 bugfix 分支
git checkout -b bugfix/fix-issue-123

# 修復 bug
# ... 編輯程式碼 ...

# 新增測試案例
# ... 編輯 tests/ ...

# 驗證修復
pytest tests/test_specific.py

# 提交
git commit -m "fix: resolve issue #123"
```

### 3. 重構程式碼

```bash
# 建立 refactor 分支
git checkout -b refactor/improve-performance

# 重構
# ... 編輯程式碼 ...

# 確保測試全部通過
pytest tests/

# 提交
git commit -m "refactor: improve performance"
```

---

## 🧪 測試指南

### 測試結構

```
tests/
├── conftest.py                  # 共用 fixtures
├── test_config_manager.py       # 配置管理測試
├── test_diff_engine.py          # 差異偵測測試
├── test_sync_engine.py          # 同步引擎測試
├── test_backup_manager.py       # 備份管理測試
├── test_cli.py                  # CLI 測試
└── test_mcp_server.py           # MCP Server 測試
```

### 執行測試

```bash
# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/test_config_manager.py

# 執行特定測試類別
pytest tests/test_config_manager.py::TestClaudeCodeAdapter

# 執行特定測試方法
pytest tests/test_config_manager.py::TestClaudeCodeAdapter::test_load_config

# 詳細輸出
pytest -v

# 顯示 print 輸出
pytest -s

# 測試覆蓋率
pytest --cov=syncmcp --cov-report=html
```

### 撰寫測試

#### 使用 Fixtures

```python
@pytest.fixture
def mock_claude_config(tmp_path):
    """建立模擬的 Claude Code 配置"""
    config_path = tmp_path / ".claude.json"
    config_data = {
        "mcpServers": {
            "filesystem": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"]
            }
        }
    }
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path
```

#### 單元測試範例

```python
def test_load_config(mock_claude_config, monkeypatch):
    """測試載入配置"""
    # 設定 HOME 環境變數指向臨時目錄
    monkeypatch.setenv("HOME", str(mock_claude_config.parent))

    # 載入配置
    adapter = ClaudeCodeAdapter()
    config = adapter.load()

    # 驗證
    assert "filesystem" in config.mcpServers
    assert config.mcpServers["filesystem"]["type"] == "stdio"
```

#### 整合測試範例

```python
def test_full_sync_workflow(mock_all_configs):
    """測試完整同步流程"""
    # 建立各元件
    config_manager = ConfigManager()
    diff_engine = DiffEngine()
    backup_manager = BackupManager()
    sync_engine = SyncEngine(config_manager, diff_engine, backup_manager)

    # 執行同步
    result = sync_engine.sync(dry_run=False)

    # 驗證結果
    assert result.success is True
    assert result.backup_path is not None
```

#### 非同步測試範例

```python
@pytest.mark.asyncio
async def test_mcp_server_tool():
    """測試 MCP Server 工具"""
    result = await call_tool("sync_mcp_configs", {"dry_run": True})

    assert isinstance(result, list)
    assert len(result) > 0
```

### 測試覆蓋率目標

- **單元測試**: >= 80%
- **整合測試**: >= 70%
- **核心模組**: >= 90%

---

## 🤝 貢獻指南

### 程式碼風格

#### Python 風格

遵循 **PEP 8** 和 **Black** 格式：

```bash
# 自動格式化
black syncmcp/

# 檢查風格
ruff check syncmcp/

# 型別檢查
mypy syncmcp/
```

#### 命名規範

- **模組**: `lowercase_with_underscores.py`
- **類別**: `PascalCase`
- **函數**: `snake_case`
- **常數**: `UPPER_CASE_WITH_UNDERSCORES`
- **私有**: `_leading_underscore`

#### Docstring 格式

使用 Google 風格：

```python
def sync_configs(strategy: str, dry_run: bool = False) -> SyncResult:
    """同步所有客戶端的 MCP 配置。

    Args:
        strategy: 同步策略（"auto" 或 "manual"）
        dry_run: 是否為預覽模式（不實際修改）

    Returns:
        SyncResult: 同步結果物件

    Raises:
        ValueError: 當 strategy 參數無效時
        IOError: 當配置檔案無法讀取時

    Examples:
        >>> result = sync_configs("auto", dry_run=True)
        >>> print(result.success)
        True
    """
    pass
```

### Commit 訊息格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新功能
- `fix`: Bug 修復
- `docs`: 文檔更新
- `style`: 程式碼格式（不影響功能）
- `refactor`: 重構
- `perf`: 效能優化
- `test`: 測試相關
- `chore`: 建置工具、依賴更新

**範例**:
```
feat(sync): add manual confirmation strategy

實作手動確認同步策略，允許用戶逐個確認每個變更。

Closes #42
```

### Pull Request 流程

1. **Fork 專案**
2. **建立功能分支**: `git checkout -b feature/amazing-feature`
3. **開發並測試**: 確保測試通過
4. **Commit**: 遵循 Commit 訊息格式
5. **Push**: `git push origin feature/amazing-feature`
6. **建立 PR**: 詳細描述變更內容
7. **Code Review**: 回應審查意見
8. **Merge**: 通過審查後合併

### 審查清單

- [ ] 所有測試通過
- [ ] 新增適當的測試案例
- [ ] 程式碼遵循風格指南
- [ ] 更新相關文檔
- [ ] Commit 訊息符合規範
- [ ] 無多餘的 debug 程式碼
- [ ] 型別標註完整

---

## 🚀 發布流程

### 1. 更新版本號

編輯 `pyproject.toml`:

```toml
[project]
name = "syncmcp"
version = "2.1.0"  # 更新版本
```

### 2. 更新 CHANGELOG

編輯 `CHANGELOG.md`:

```markdown
## [2.1.0] - 2025-11-01

### Added
- 新增手動確認同步策略
- 新增配置驗證功能

### Fixed
- 修復 HTTP 類型轉換問題
- 修復備份恢復錯誤

### Changed
- 改善差異報告格式
- 優化同步效能
```

### 3. 建立 Git Tag

```bash
git tag -a v2.1.0 -m "Release version 2.1.0"
git push origin v2.1.0
```

### 4. 建置發布套件

```bash
# 清理舊建置
rm -rf dist/

# 建置
python -m build

# 檢查
twine check dist/*
```

### 5. 上傳到 PyPI

```bash
# 測試環境
twine upload --repository testpypi dist/*

# 生產環境
twine upload dist/*
```

### 6. GitHub Release

1. 前往 GitHub Releases
2. 建立新 Release
3. 選擇 Tag: v2.1.0
4. 填寫 Release Notes（從 CHANGELOG 複製）
5. 上傳建置產物（可選）
6. 發布

---

## 🐛 除錯技巧

### 啟用詳細日誌

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("syncmcp")
```

### 使用 pdb 除錯

```python
def sync(self):
    import pdb; pdb.set_trace()  # 設定斷點
    # ... 程式碼 ...
```

### 測試特定場景

```python
# 建立測試腳本
def test_specific_bug():
    # 重現 bug 的步驟
    config = load_config()
    # ... 除錯 ...

if __name__ == "__main__":
    test_specific_bug()
```

---

## 📚 參考資源

### 文檔

- [Python 官方文檔](https://docs.python.org/3/)
- [Click 文檔](https://click.palletsprojects.com/)
- [Rich 文檔](https://rich.readthedocs.io/)
- [pytest 文檔](https://docs.pytest.org/)
- [MCP SDK 文檔](https://modelcontextprotocol.io/)

### 相關專案

- [Claude CLI](https://github.com/anthropics/claude-cli)
- [MCP Servers](https://github.com/modelcontextprotocol/servers)

---

## 🔮 未來計劃

### v2.1.0
- [ ] 支援專案級別 MCP（Bug #13）
- [ ] 新增配置驗證
- [ ] 改善錯誤訊息

### v2.2.0
- [ ] 支援遠端同步（雲端備份）
- [ ] 新增插件系統
- [ ] 支援自訂同步規則

### v3.0.0
- [ ] Web UI
- [ ] 多用戶支援
- [ ] 自動化同步（監聽配置變更）

---

## 📞 聯絡方式

- **Email**: developer@syncmcp.dev
- **GitHub**: [syncmcp/syncmcp](https://github.com/syncmcp/syncmcp)
- **Discord**: [加入我們的 Discord](https://discord.gg/syncmcp)

---

**上次更新**: 2025-10-29
**版本**: 2.0.0
