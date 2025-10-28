# SyncMCP API 文檔

> **版本**: 2.0.0
> **更新日期**: 2025-10-29

## 📋 目錄

- [核心模組](#核心模組)
  - [config_manager](#config_manager)
  - [diff_engine](#diff_engine)
  - [sync_engine](#sync_engine)
  - [backup_manager](#backup_manager)
- [MCP Server API](#mcp-server-api)
- [CLI API](#cli-api)
- [工具函數](#工具函數)

---

## 核心模組

### config_manager

配置管理模組，處理所有客戶端的配置載入、保存和轉換。

#### ClientConfig

配置資料類別。

```python
@dataclass
class ClientConfig:
    """客戶端配置"""

    client_name: str            # 客戶端名稱
    mcpServers: Dict[str, Any]  # MCP 伺服器配置
    last_modified: float        # 最後修改時間（timestamp）
```

**屬性**:

| 屬性 | 類型 | 說明 |
|-----|------|------|
| `client_name` | str | 客戶端名稱（如 "claude-code"） |
| `mcpServers` | Dict[str, Any] | MCP 配置字典 |
| `last_modified` | float | 最後修改時間戳 |

**範例**:
```python
config = ClientConfig(
    client_name="claude-code",
    mcpServers={
        "filesystem": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"]
        }
    },
    last_modified=1698765432.0
)
```

---

#### BaseConfigAdapter

配置 Adapter 抽象基類。

```python
class BaseConfigAdapter(ABC):
    """配置 Adapter 基類"""

    @abstractmethod
    def get_config_path(self) -> Path:
        """取得配置檔案路徑"""

    @abstractmethod
    def load(self) -> ClientConfig:
        """載入配置"""

    @abstractmethod
    def save(self, config: ClientConfig) -> None:
        """保存配置"""
```

**方法**:

##### `get_config_path() -> Path`

取得配置檔案路徑。

**Returns**: `Path` - 配置檔案的絕對路徑

**範例**:
```python
adapter = ClaudeCodeAdapter()
path = adapter.get_config_path()
print(path)  # /Users/username/.claude.json
```

##### `load() -> ClientConfig`

載入配置檔案。

**Returns**: `ClientConfig` - 載入的配置物件

**Raises**:
- `FileNotFoundError`: 配置檔案不存在
- `json.JSONDecodeError`: JSON 格式錯誤

**範例**:
```python
adapter = ClaudeCodeAdapter()
config = adapter.load()
print(config.mcpServers.keys())
```

##### `save(config: ClientConfig) -> None`

保存配置到檔案。

**Args**:
- `config` (ClientConfig): 要保存的配置物件

**Raises**:
- `IOError`: 檔案寫入失敗

**範例**:
```python
config.mcpServers["new-mcp"] = {"type": "stdio", "command": "test"}
adapter.save(config)
```

---

#### ClaudeCodeAdapter

Claude Code 配置 Adapter。

```python
class ClaudeCodeAdapter(BaseConfigAdapter):
    """Claude Code 配置 Adapter"""

    def get_config_path(self) -> Path:
        return Path.home() / ".claude.json"

    def load(self) -> ClientConfig:
        """載入配置（目前只支援全域 MCPs）"""

    def save(self, config: ClientConfig) -> None:
        """保存配置"""
```

**特性**:
- 配置路徑: `~/.claude.json`
- 支援層級: 全域 + 專案級別（目前只載入全域）
- 支援類型: `stdio`, `http`, `sse`

**已知限制**:
- Bug #13: 目前不載入專案級別的 MCP
- 不支援 `streamable-http`（Roo Code 專有）

---

#### ClaudeDesktopAdapter

Claude Desktop 配置 Adapter。

```python
class ClaudeDesktopAdapter(BaseConfigAdapter):
    """Claude Desktop 配置 Adapter"""

    def get_config_path(self) -> Path:
        # macOS
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"

    def load(self) -> ClientConfig:
        """載入配置"""

    def save(self, config: ClientConfig) -> None:
        """保存配置（自動過濾非 stdio MCPs）"""
```

**特性**:
- 配置路徑:
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Linux: `~/.config/Claude/config.json`
  - Windows: `%APPDATA%\Claude\config.json`
- 支援層級: 僅全域
- 支援類型: **僅 `stdio`**

**自動過濾**:
保存時自動過濾掉所有非 `stdio` 類型的 MCP。

---

#### RooCodeAdapter

Roo Code 配置 Adapter。

```python
class RooCodeAdapter(BaseConfigAdapter):
    """Roo Code 配置 Adapter"""

    def get_config_path(self) -> Path:
        return Path.home() / ".roo-code/config.json"

    def load(self) -> ClientConfig:
        """載入配置（轉換 streamable-http）"""

    def save(self, config: ClientConfig) -> None:
        """保存配置（轉換為 streamable-http）"""
```

**特性**:
- 配置路徑: `~/.roo-code/config.json`
- 支援層級: 全域 + 專案級別
- 支援類型: `stdio`, `streamable-http`

**自動轉換**:
- 載入時: `streamable-http` → `http` 或 `sse`
- 保存時: `http`/`sse` → `streamable-http`

---

#### GeminiAdapter

Gemini CLI 配置 Adapter。

```python
class GeminiAdapter(BaseConfigAdapter):
    """Gemini CLI 配置 Adapter"""

    def get_config_path(self) -> Path:
        return Path.home() / ".gemini/config.json"

    def load(self) -> ClientConfig:
        """載入配置"""

    def save(self, config: ClientConfig) -> None:
        """保存配置"""
```

**特性**:
- 配置路徑: `~/.gemini/config.json`
- 支援層級: **僅全域**
- 支援類型: 主要 `stdio`

---

#### ConfigManager

統一配置管理器。

```python
class ConfigManager:
    """統一配置管理器"""

    def __init__(self):
        self.adapters = {
            "claude-code": ClaudeCodeAdapter(),
            "claude-desktop": ClaudeDesktopAdapter(),
            "roo-code": RooCodeAdapter(),
            "gemini": GeminiAdapter()
        }

    def load(self, client_name: str) -> ClientConfig:
        """載入指定客戶端的配置"""

    def save(self, client_name: str, config: ClientConfig) -> None:
        """保存指定客戶端的配置"""

    def load_all(self) -> Dict[str, ClientConfig]:
        """載入所有客戶端的配置"""

    def get_adapter(self, client_name: str) -> BaseConfigAdapter:
        """取得指定客戶端的 Adapter"""
```

**方法**:

##### `load(client_name: str) -> ClientConfig`

載入指定客戶端的配置。

**Args**:
- `client_name` (str): 客戶端名稱

**Returns**: `ClientConfig` - 載入的配置

**Raises**:
- `ValueError`: 客戶端名稱無效

**範例**:
```python
manager = ConfigManager()
config = manager.load("claude-code")
```

##### `save(client_name: str, config: ClientConfig) -> None`

保存指定客戶端的配置。

**Args**:
- `client_name` (str): 客戶端名稱
- `config` (ClientConfig): 配置物件

**範例**:
```python
manager.save("claude-code", config)
```

##### `load_all() -> Dict[str, ClientConfig]`

載入所有客戶端的配置。

**Returns**: `Dict[str, ClientConfig]` - 客戶端名稱 → 配置

**範例**:
```python
configs = manager.load_all()
for name, config in configs.items():
    print(f"{name}: {len(config.mcpServers)} MCPs")
```

---

### diff_engine

差異偵測引擎。

#### DiffType

差異類型枚舉。

```python
class DiffType(Enum):
    """差異類型"""
    ADDED = "added"       # 新增
    REMOVED = "removed"   # 刪除
    MODIFIED = "modified" # 修改
```

---

#### DiffItem

單一差異項目。

```python
@dataclass
class DiffItem:
    """差異項目"""

    mcp_name: str                    # MCP 名稱
    diff_type: DiffType              # 差異類型
    clients: Dict[str, Optional[Dict]]  # 客戶端配置
```

**屬性**:

| 屬性 | 類型 | 說明 |
|-----|------|------|
| `mcp_name` | str | MCP 伺服器名稱 |
| `diff_type` | DiffType | 差異類型 |
| `clients` | Dict[str, Optional[Dict]] | 各客戶端的配置（None 表示不存在） |

**範例**:
```python
diff = DiffItem(
    mcp_name="filesystem",
    diff_type=DiffType.ADDED,
    clients={
        "claude-code": {"type": "stdio", ...},
        "claude-desktop": None  # 不存在
    }
)
```

---

#### DiffReport

完整差異報告。

```python
class DiffReport:
    """差異報告"""

    def __init__(self):
        self.diffs: List[DiffItem] = []

    def add_diff(self, diff: DiffItem) -> None:
        """新增差異項目"""

    def has_removals(self) -> bool:
        """是否有刪除項目"""

    def get_statistics(self) -> Dict[str, int]:
        """取得統計資訊"""

    def to_text(self) -> str:
        """轉換為文字報告"""
```

**方法**:

##### `add_diff(diff: DiffItem) -> None`

新增差異項目。

**Args**:
- `diff` (DiffItem): 差異項目

##### `has_removals() -> bool`

檢查是否有刪除項目。

**Returns**: `bool` - 是否有刪除

##### `get_statistics() -> Dict[str, int]`

取得統計資訊。

**Returns**: `Dict[str, int]` - 統計數據

**範例**:
```python
stats = report.get_statistics()
# {
#     "total": 15,
#     "added": 3,
#     "removed": 1,
#     "modified": 2,
#     "unchanged": 9
# }
```

##### `to_text() -> str`

轉換為格式化的文字報告。

**Returns**: `str` - 文字報告

---

#### DiffEngine

差異偵測引擎。

```python
class DiffEngine:
    """差異偵測引擎"""

    def analyze(
        self,
        configs: Dict[str, ClientConfig]
    ) -> DiffReport:
        """分析配置差異"""

    def select_source(
        self,
        configs: Dict[str, ClientConfig],
        strategy: str = "auto"
    ) -> str:
        """選擇同步來源"""

    def get_all_mcp_names(
        self,
        configs: Dict[str, ClientConfig]
    ) -> Set[str]:
        """取得所有 MCP 名稱"""
```

**方法**:

##### `analyze(configs: Dict[str, ClientConfig]) -> DiffReport`

分析配置差異。

**Args**:
- `configs` (Dict[str, ClientConfig]): 客戶端配置字典

**Returns**: `DiffReport` - 差異報告

**範例**:
```python
engine = DiffEngine()
configs = config_manager.load_all()
report = engine.analyze(configs)

print(report.to_text())
```

##### `select_source(configs, strategy="auto") -> str`

選擇同步來源客戶端。

**Args**:
- `configs` (Dict[str, ClientConfig]): 配置字典
- `strategy` (str): 選擇策略（"auto" 或 "manual"）

**Returns**: `str` - 來源客戶端名稱

**策略**:
- `auto`: 選擇最近修改的配置
- `manual`: 需要用戶手動選擇

---

### sync_engine

同步引擎。

#### SyncStrategy

同步策略枚舉。

```python
class SyncStrategy(Enum):
    """同步策略"""
    AUTO = "auto"       # 自動同步
    MANUAL = "manual"   # 手動確認
```

---

#### SyncResult

同步結果。

```python
@dataclass
class SyncResult:
    """同步結果"""

    success: bool                    # 是否成功
    changes: Dict[str, List[str]]    # 變更摘要
    warnings: List[str]              # 警告訊息
    errors: List[str]                # 錯誤訊息
    backup_path: Optional[str]       # 備份路徑
```

**屬性**:

| 屬性 | 類型 | 說明 |
|-----|------|------|
| `success` | bool | 是否成功完成同步 |
| `changes` | Dict[str, List[str]] | 各客戶端的變更列表 |
| `warnings` | List[str] | 警告訊息 |
| `errors` | List[str] | 錯誤訊息 |
| `backup_path` | Optional[str] | 備份路徑（如有建立） |

---

#### SyncEngine

同步引擎。

```python
class SyncEngine:
    """同步引擎"""

    def __init__(
        self,
        config_manager: ConfigManager,
        diff_engine: DiffEngine,
        backup_manager: BackupManager,
        verbose: bool = False
    ):
        """初始化同步引擎"""

    def sync(
        self,
        strategy: SyncStrategy = SyncStrategy.AUTO,
        dry_run: bool = False,
        create_backup: bool = True
    ) -> SyncResult:
        """執行同步"""
```

**方法**:

##### `sync(strategy, dry_run, create_backup) -> SyncResult`

執行配置同步。

**Args**:
- `strategy` (SyncStrategy): 同步策略（預設: AUTO）
- `dry_run` (bool): 預覽模式，不實際修改（預設: False）
- `create_backup` (bool): 是否建立備份（預設: True）

**Returns**: `SyncResult` - 同步結果

**流程**:
1. 載入所有配置
2. 分析差異
3. （可選）建立備份
4. 執行同步
5. （錯誤時）自動回滾

**範例**:
```python
engine = SyncEngine(config_manager, diff_engine, backup_manager)

# 預覽同步
result = engine.sync(dry_run=True)
print(f"Will modify {len(result.changes)} clients")

# 執行同步
result = engine.sync(strategy=SyncStrategy.AUTO)
if result.success:
    print("✅ 同步成功")
else:
    print(f"❌ 同步失敗: {result.errors}")
```

---

### backup_manager

備份管理器。

#### BackupManager

```python
class BackupManager:
    """備份管理器"""

    def __init__(self, backup_dir: Optional[Path] = None):
        """初始化備份管理器"""

    def create(
        self,
        adapters: List[BaseConfigAdapter]
    ) -> str:
        """建立備份"""

    def restore(
        self,
        backup_path: str,
        adapters: List[BaseConfigAdapter]
    ) -> None:
        """恢復備份"""

    def list(self) -> List[Dict]:
        """列出所有備份"""

    def cleanup(self, keep: int = 10) -> None:
        """清理舊備份"""

    def get_info(self, backup_path: str) -> Dict:
        """取得備份資訊"""
```

**方法**:

##### `create(adapters: List[BaseConfigAdapter]) -> str`

建立新備份。

**Args**:
- `adapters` (List[BaseConfigAdapter]): 要備份的 Adapters

**Returns**: `str` - 備份路徑

**範例**:
```python
manager = BackupManager()
backup_path = manager.create(config_manager.adapters.values())
print(f"Backup created: {backup_path}")
```

##### `restore(backup_path: str, adapters) -> None`

從備份恢復配置。

**Args**:
- `backup_path` (str): 備份路徑
- `adapters` (List[BaseConfigAdapter]): 要恢復的 Adapters

**Raises**:
- `FileNotFoundError`: 備份不存在

**範例**:
```python
manager.restore(backup_path, config_manager.adapters.values())
```

##### `list() -> List[Dict]`

列出所有可用備份。

**Returns**: `List[Dict]` - 備份資訊列表

**備份資訊格式**:
```python
{
    "path": "/path/to/backup",
    "timestamp": 1698765432.0,
    "date": "2025-10-29 10:30:45",
    "clients": ["claude-code", "claude-desktop", ...]
}
```

**範例**:
```python
backups = manager.list()
for backup in backups:
    print(f"{backup['date']}: {backup['path']}")
```

##### `cleanup(keep: int = 10) -> None`

清理舊備份，保留最新 N 個。

**Args**:
- `keep` (int): 保留數量（預設: 10）

**範例**:
```python
manager.cleanup(keep=10)  # 保留最新 10 個
```

##### `get_info(backup_path: str) -> Dict`

取得備份詳細資訊。

**Args**:
- `backup_path` (str): 備份路徑

**Returns**: `Dict` - 備份資訊

---

## MCP Server API

SyncMCP 提供 MCP Server 實作，可作為 MCP 工具被 AI 客戶端使用。

### 工具列表

#### `sync_mcp_configs`

同步 MCP 配置。

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "strategy": {
      "type": "string",
      "enum": ["auto", "manual"],
      "default": "auto"
    },
    "dry_run": {
      "type": "boolean",
      "default": false
    },
    "create_backup": {
      "type": "boolean",
      "default": true
    }
  }
}
```

**範例**:
```python
result = await call_tool("sync_mcp_configs", {
    "strategy": "auto",
    "dry_run": True,
    "create_backup": True
})
```

---

#### `check_sync_status`

檢查同步狀態。

**Input Schema**:
```json
{
  "type": "object",
  "properties": {}
}
```

**範例**:
```python
result = await call_tool("check_sync_status", {})
```

---

#### `show_config_diff`

顯示配置差異。

**Input Schema**:
```json
{
  "type": "object",
  "properties": {}
}
```

**範例**:
```python
result = await call_tool("show_config_diff", {})
```

---

#### `suggest_conflict_resolution`

建議衝突解決方案。

**Input Schema**:
```json
{
  "type": "object",
  "properties": {}
}
```

**範例**:
```python
result = await call_tool("suggest_conflict_resolution", {})
```

---

## CLI API

### 主命令

```python
@click.group()
@click.version_option()
@click.option("--verbose", "-v", is_flag=True)
def cli(verbose):
    """SyncMCP - MCP 配置同步工具"""
```

### 子命令

#### sync

```python
@cli.command()
@click.option("--strategy", type=click.Choice(["auto", "manual"]))
@click.option("--dry-run", is_flag=True)
@click.option("--no-backup", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
def sync(strategy, dry_run, no_backup, verbose):
    """同步所有客戶端的 MCP 配置"""
```

#### status

```python
@cli.command()
def status():
    """顯示所有客戶端的配置狀態"""
```

#### list

```python
@cli.command()
def list_mcps():
    """列出所有 MCP 及其狀態"""
```

#### diff

```python
@cli.command()
def diff():
    """顯示配置差異"""
```

#### doctor

```python
@cli.command()
def doctor():
    """診斷系統環境"""
```

#### history

```python
@cli.command()
@click.option("--limit", type=int, default=10)
@click.option("--stats", is_flag=True)
def history(limit, stats):
    """查看同步歷史"""
```

#### restore

```python
@cli.command()
def restore():
    """從備份恢復配置"""
```

#### interactive

```python
@cli.command()
def interactive():
    """啟動互動模式（TUI）"""
```

#### open

```python
@cli.command()
@click.argument("client", required=False)
def open_config(client):
    """在編輯器中打開配置檔案"""
```

---

## 工具函數

### 路徑工具

```python
def get_syncmcp_dir() -> Path:
    """取得 SyncMCP 目錄（~/.syncmcp）"""
    return Path.home() / ".syncmcp"

def get_backup_dir() -> Path:
    """取得備份目錄"""
    return get_syncmcp_dir() / "backups"

def get_history_file() -> Path:
    """取得歷史記錄檔案"""
    return get_syncmcp_dir() / "history.json"
```

### 日期時間工具

```python
def timestamp_to_str(timestamp: float) -> str:
    """轉換時間戳為字串"""
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def get_current_timestamp() -> float:
    """取得當前時間戳"""
    import time
    return time.time()
```

### JSON 工具

```python
def load_json(file_path: Path) -> Dict:
    """載入 JSON 檔案"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path: Path, data: Dict) -> None:
    """保存 JSON 檔案"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

---

## 範例程式碼

### 完整同步流程

```python
from syncmcp.core.config_manager import ConfigManager
from syncmcp.core.diff_engine import DiffEngine
from syncmcp.core.sync_engine import SyncEngine, SyncStrategy
from syncmcp.core.backup_manager import BackupManager

# 初始化元件
config_manager = ConfigManager()
diff_engine = DiffEngine()
backup_manager = BackupManager()
sync_engine = SyncEngine(config_manager, diff_engine, backup_manager)

# 執行同步
result = sync_engine.sync(
    strategy=SyncStrategy.AUTO,
    dry_run=False,
    create_backup=True
)

# 檢查結果
if result.success:
    print("✅ 同步成功")
    print(f"備份位置: {result.backup_path}")
    for client, changes in result.changes.items():
        print(f"{client}: {len(changes)} 項變更")
else:
    print("❌ 同步失敗")
    for error in result.errors:
        print(f"  - {error}")
```

### 手動配置管理

```python
# 載入配置
config = config_manager.load("claude-code")

# 修改配置
config.mcpServers["new-mcp"] = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "new-mcp-server"]
}

# 保存配置
config_manager.save("claude-code", config)
```

### 差異分析

```python
# 載入所有配置
configs = config_manager.load_all()

# 分析差異
report = diff_engine.analyze(configs)

# 顯示統計
stats = report.get_statistics()
print(f"總計: {stats['total']}")
print(f"新增: {stats['added']}")
print(f"刪除: {stats['removed']}")
print(f"修改: {stats['modified']}")

# 顯示詳細報告
print(report.to_text())
```

### 備份與恢復

```python
# 建立備份
backup_path = backup_manager.create(config_manager.adapters.values())
print(f"備份已建立: {backup_path}")

# 列出備份
backups = backup_manager.list()
for backup in backups[:5]:  # 顯示最新 5 個
    print(f"{backup['date']}: {backup['path']}")

# 恢復備份
backup_manager.restore(backup_path, config_manager.adapters.values())
print("配置已恢復")
```

---

## 錯誤處理

### 常見異常

| 異常 | 說明 | 處理方式 |
|-----|------|---------|
| `FileNotFoundError` | 配置檔案不存在 | 檢查路徑，或初始化新配置 |
| `json.JSONDecodeError` | JSON 格式錯誤 | 檢查檔案內容，或恢復備份 |
| `ValueError` | 參數無效 | 檢查輸入參數 |
| `IOError` | 檔案讀寫失敗 | 檢查權限，確保磁碟空間 |

### 錯誤處理範例

```python
try:
    result = sync_engine.sync()
    if not result.success:
        # 同步失敗但有受控處理
        for error in result.errors:
            logger.error(error)
except FileNotFoundError as e:
    print(f"配置檔案不存在: {e}")
except Exception as e:
    print(f"未預期的錯誤: {e}")
    # 嘗試恢復最新備份
    backups = backup_manager.list()
    if backups:
        backup_manager.restore(backups[0]['path'], adapters)
```

---

## 型別提示

SyncMCP 使用完整的型別提示，建議啟用 mypy 檢查：

```bash
mypy syncmcp/
```

**常用型別**:
```python
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
```

---

## 版本相容性

| SyncMCP 版本 | Python 版本 | 依賴套件 |
|------------|-----------|---------|
| 2.0.0 | >= 3.10 | click>=8.1, rich>=13.0, InquirerPy>=0.3 |
| 1.x | >= 3.9 | （舊版） |

---

**上次更新**: 2025-10-29
**版本**: 2.0.0
