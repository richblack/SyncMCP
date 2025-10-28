"""
配置管理器 - 管理所有客戶端的 MCP 配置
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path


class ClientConfig:
    """客戶端配置的統一表示"""

    def __init__(self, client_name: str, file_path: Path):
        self.client_name = client_name
        self.file_path = file_path
        self.mcpServers: dict = {}
        self.last_modified: float | None = None
        self._raw_data: dict = {}

    def load(self):
        """載入配置文件"""
        if not self.file_path.exists():
            return

        with open(self.file_path, encoding="utf-8") as f:
            self._raw_data = json.load(f)
            self.mcpServers = self._raw_data.get("mcpServers", {})
            self.last_modified = self.file_path.stat().st_mtime

    def save(self):
        """保存配置文件"""
        # 確保目錄存在
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # 保持原有結構，只更新 mcpServers
        if self.file_path.exists():
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        data["mcpServers"] = self.mcpServers

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class ClientAdapter(ABC):
    """客戶端適配器基類"""

    @abstractmethod
    def get_config_path(self) -> Path:
        """獲取配置文件路徑"""
        pass

    @abstractmethod
    def normalize_config(self, config: dict) -> dict:
        """標準化配置格式"""
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> list[str]:
        """驗證配置有效性，返回錯誤列表"""
        pass


class ClaudeCodeAdapter(ClientAdapter):
    """Claude Code 適配器"""

    def get_config_path(self) -> Path:
        return Path.home() / ".claude.json"

    def normalize_config(self, config: dict) -> dict:
        """
        標準化配置為 Claude Code 格式
        - streamable-http → http (有 headers) 或 sse (無 headers)
        """
        normalized = {}
        for name, server in config.items():
            server_copy = server.copy()

            # Roo Code → Claude Code 類型轉換
            if server_copy.get("type") == "streamable-http":
                # 如果有 headers，轉為 http；否則轉為 sse
                if "headers" in server_copy and server_copy["headers"]:
                    server_copy["type"] = "http"
                else:
                    server_copy["type"] = "sse"

            normalized[name] = server_copy
        return normalized

    def validate_config(self, config: dict) -> list[str]:
        errors = []
        # 驗證必要欄位（僅針對 stdio 類型）
        for name, server in config.get("mcpServers", {}).items():
            if server.get("type") == "stdio" and "command" not in server:
                errors.append(f"{name}: 缺少 'command' 欄位")
        return errors


class RooCodeAdapter(ClientAdapter):
    """Roo Code 適配器"""

    def get_config_path(self) -> Path:
        return (
            Path.home()
            / "Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json"
        )

    def normalize_config(self, config: dict) -> dict:
        """
        標準化配置為 Roo Code 格式
        - http/sse → streamable-http
        """
        normalized = {}
        for name, server in config.items():
            server_copy = server.copy()

            # Claude Code → Roo Code 類型轉換
            if server_copy.get("type") in ["http", "sse"]:
                server_copy["type"] = "streamable-http"

            normalized[name] = server_copy
        return normalized

    def validate_config(self, config: dict) -> list[str]:
        return []


class ClaudeDesktopAdapter(ClientAdapter):
    """Claude Desktop 適配器"""

    def get_config_path(self) -> Path:
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"

    def normalize_config(self, config: dict) -> dict:
        """
        標準化配置為 Claude Desktop 格式
        - 只保留 stdio 類型的 MCP
        - 過濾掉所有遠端 MCP (http, sse, streamable-http)
        """
        filtered = {}
        for name, server in config.items():
            server_type = server.get("type", server.get("transport"))
            # 只保留 stdio 類型
            if server_type == "stdio":
                filtered[name] = server
        return filtered

    def validate_config(self, config: dict) -> list[str]:
        errors = []
        # Claude Desktop 只支援 stdio
        for name, server in config.get("mcpServers", {}).items():
            server_type = server.get("type", server.get("transport"))
            if server_type != "stdio":
                errors.append(f"{name}: Claude Desktop 只支援 stdio transport（已自動過濾）")
        return errors


class GeminiAdapter(ClientAdapter):
    """Gemini CLI 適配器"""

    def get_config_path(self) -> Path:
        return Path.home() / ".gemini/settings.json"

    def normalize_config(self, config: dict) -> dict:
        # Gemini 格式轉換
        return config

    def validate_config(self, config: dict) -> list[str]:
        return []


class ConfigManager:
    """配置管理器 - 管理所有客戶端的配置"""

    def __init__(self):
        self.adapters = {
            "claude-code": ClaudeCodeAdapter(),
            "roo-code": RooCodeAdapter(),
            "claude-desktop": ClaudeDesktopAdapter(),
            "gemini": GeminiAdapter(),
        }

    def load_all(self) -> dict[str, ClientConfig]:
        """載入所有客戶端配置"""
        configs = {}
        for name, adapter in self.adapters.items():
            config = ClientConfig(name, adapter.get_config_path())
            config.load()
            configs[name] = config
        return configs

    def sync_all(self, source_config: ClientConfig):
        """將源配置同步到所有客戶端"""
        for name, adapter in self.adapters.items():
            target_config = ClientConfig(name, adapter.get_config_path())

            # 標準化和驗證
            normalized = adapter.normalize_config(source_config.mcpServers)
            errors = adapter.validate_config({"mcpServers": normalized})

            if errors:
                # 記錄警告但繼續
                print(f"警告: {name} 配置驗證失敗: {errors}")

            # 寫入配置
            target_config.mcpServers = normalized
            target_config.save()
