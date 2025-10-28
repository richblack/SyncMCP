"""
自定義錯誤類別 - 提供友善的錯誤訊息和解決建議
"""



class SyncMCPError(Exception):
    """SyncMCP 基礎錯誤類別"""

    def __init__(
        self, message: str, suggestions: list[str] | None = None, details: str | None = None
    ):
        """
        初始化錯誤

        Args:
            message: 錯誤訊息
            suggestions: 解決建議列表
            details: 詳細錯誤信息
        """
        self.message = message
        self.suggestions = suggestions or []
        self.details = details
        super().__init__(self.message)

    def get_user_message(self) -> str:
        """獲取用戶友善的錯誤訊息"""
        lines = [f"❌ {self.message}"]

        if self.suggestions:
            lines.append("\n💡 建議解決方案:")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"  {i}. {suggestion}")

        if self.details:
            lines.append(f"\n🔍 詳細信息: {self.details}")

        lines.append("\n💬 使用 --verbose 查看更多調試信息")

        return "\n".join(lines)


class ConfigNotFoundError(SyncMCPError):
    """配置文件不存在錯誤"""

    def __init__(self, client: str, config_path: str):
        message = f"{client} 的配置文件不存在"
        suggestions = [
            f"檢查配置文件路徑是否正確: {config_path}",
            f"確認 {client} 已正確安裝",
            "如果是首次使用，請先在該客戶端中配置至少一個 MCP",
        ]
        details = f"配置路徑: {config_path}"
        super().__init__(message, suggestions, details)


class ConfigValidationError(SyncMCPError):
    """配置驗證錯誤"""

    def __init__(self, client: str, reason: str):
        message = f"{client} 的配置驗證失敗"
        suggestions = [
            "使用 JSON 格式驗證工具檢查配置文件",
            "參考官方文檔確認配置格式",
            "使用 `syncmcp status` 查看配置狀態",
        ]
        details = f"原因: {reason}"
        super().__init__(message, suggestions, details)


class ConfigReadError(SyncMCPError):
    """配置讀取錯誤"""

    def __init__(self, client: str, error: Exception):
        message = f"無法讀取 {client} 的配置文件"
        suggestions = [
            "檢查文件權限是否正確",
            "確認文件未被其他程序佔用",
            "嘗試手動打開文件檢查內容",
        ]
        details = f"錯誤: {str(error)}"
        super().__init__(message, suggestions, details)


class ConfigWriteError(SyncMCPError):
    """配置寫入錯誤"""

    def __init__(self, client: str, error: Exception):
        message = f"無法寫入 {client} 的配置文件"
        suggestions = [
            "檢查文件權限是否正確",
            "確認磁碟空間是否充足",
            "檢查目標目錄是否存在",
            "備份已自動恢復，配置未被修改",
        ]
        details = f"錯誤: {str(error)}"
        super().__init__(message, suggestions, details)


class SyncError(SyncMCPError):
    """同步錯誤"""

    def __init__(self, reason: str, failed_clients: list[str] | None = None):
        message = f"配置同步失敗: {reason}"
        suggestions = [
            "檢查所有客戶端配置文件是否可訪問",
            "使用 `syncmcp status` 查看當前狀態",
            "使用 `syncmcp diff` 查看差異",
            "如果問題持續，使用 `syncmcp restore` 恢復備份",
        ]
        details = None
        if failed_clients:
            details = f"失敗的客戶端: {', '.join(failed_clients)}"
        super().__init__(message, suggestions, details)


class BackupError(SyncMCPError):
    """備份錯誤"""

    def __init__(self, reason: str):
        message = f"備份操作失敗: {reason}"
        suggestions = [
            "檢查 ~/.syncmcp/backups/ 目錄權限",
            "確認磁碟空間是否充足",
            "嘗試手動清理舊備份: `syncmcp history --cleanup`",
        ]
        super().__init__(message, suggestions)


class RestoreError(SyncMCPError):
    """恢復錯誤"""

    def __init__(self, backup_id: str, reason: str):
        message = f"從備份 {backup_id} 恢復失敗: {reason}"
        suggestions = [
            "檢查備份是否完整",
            "使用 `syncmcp history` 查看可用的備份",
            "嘗試恢復其他備份",
        ]
        super().__init__(message, suggestions)


class MCPTypeConversionError(SyncMCPError):
    """MCP 類型轉換錯誤"""

    def __init__(self, mcp_name: str, from_type: str, to_client: str):
        message = f"MCP '{mcp_name}' 的類型 '{from_type}' 無法轉換為 {to_client} 支援的格式"
        suggestions = [
            f"檢查 {mcp_name} 的配置是否正確",
            f"{to_client} 可能不支援此類型的 MCP",
            "參考 CLAUDE.md 中的類型轉換規則",
        ]
        details = f"源類型: {from_type}, 目標客戶端: {to_client}"
        super().__init__(message, suggestions, details)


class DiskSpaceError(SyncMCPError):
    """磁碟空間不足錯誤"""

    def __init__(self, required_mb: int, available_mb: int):
        message = f"磁碟空間不足，需要 {required_mb}MB，可用 {available_mb}MB"
        suggestions = ["清理不需要的文件釋放空間", "清理舊的備份文件", "移動備份目錄到其他磁碟"]
        super().__init__(message, suggestions)


class NetworkError(SyncMCPError):
    """網絡錯誤（用於未來的 MCP Server 功能）"""

    def __init__(self, reason: str):
        message = f"網絡連接失敗: {reason}"
        suggestions = ["檢查網絡連接是否正常", "檢查防火牆設定", "稍後重試"]
        super().__init__(message, suggestions)


class PermissionError(SyncMCPError):
    """權限錯誤"""

    def __init__(self, path: str, operation: str):
        message = f"沒有權限執行 {operation} 操作"
        suggestions = [
            f"檢查 {path} 的文件權限",
            "使用 `chmod` 修改權限（如果需要）",
            "確認當前用戶有足夠的權限",
        ]
        details = f"路徑: {path}"
        super().__init__(message, suggestions, details)


def format_error_for_display(error: Exception, verbose: bool = False) -> str:
    """
    格式化錯誤訊息用於顯示

    Args:
        error: 異常對象
        verbose: 是否顯示詳細信息

    Returns:
        格式化的錯誤訊息
    """
    if isinstance(error, SyncMCPError):
        if verbose:
            # Verbose 模式顯示完整信息和堆疊
            import traceback

            lines = [error.get_user_message()]
            lines.append("\n" + "=" * 60)
            lines.append("完整堆疊追蹤:")
            lines.append(traceback.format_exc())
            return "\n".join(lines)
        else:
            # 一般模式只顯示友善訊息
            return error.get_user_message()
    else:
        # 未知錯誤類型
        if verbose:
            import traceback

            return f"❌ 發生未預期的錯誤:\n{traceback.format_exc()}"
        else:
            return f"❌ 發生錯誤: {str(error)}\n💬 使用 --verbose 查看詳細信息"
