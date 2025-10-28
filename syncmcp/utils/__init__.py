"""
工具模組 - 日誌、錯誤處理、歷史記錄
"""

from .errors import (
    BackupError,
    ConfigNotFoundError,
    ConfigReadError,
    ConfigValidationError,
    ConfigWriteError,
    DiskSpaceError,
    MCPTypeConversionError,
    NetworkError,
    PermissionError,
    RestoreError,
    SyncError,
    SyncMCPError,
    format_error_for_display,
)
from .history import SyncHistoryEntry, SyncHistoryManager, get_history_manager
from .logger import SyncMCPLogger, get_logger, set_verbose

__all__ = [
    # Logger
    "SyncMCPLogger",
    "get_logger",
    "set_verbose",
    # Errors
    "SyncMCPError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    "ConfigReadError",
    "ConfigWriteError",
    "SyncError",
    "BackupError",
    "RestoreError",
    "MCPTypeConversionError",
    "DiskSpaceError",
    "NetworkError",
    "PermissionError",
    "format_error_for_display",
    # History
    "SyncHistoryEntry",
    "SyncHistoryManager",
    "get_history_manager",
]
