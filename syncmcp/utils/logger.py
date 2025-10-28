"""
日誌系統 - 統一的日誌記錄和管理
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class SyncMCPLogger:
    """SyncMCP 日誌管理器"""

    def __init__(
        self, name: str = "syncmcp", log_dir: Path | None = None, verbose: bool = False
    ):
        """
        初始化日誌系統

        Args:
            name: Logger 名稱
            log_dir: 日誌目錄（預設 ~/.syncmcp/logs/）
            verbose: 是否顯示 DEBUG 級別日誌
        """
        self.name = name
        self.verbose = verbose

        # 設定日誌目錄
        if log_dir is None:
            log_dir = Path.home() / ".syncmcp" / "logs"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 創建 logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        # 清除現有 handlers（避免重複）
        self.logger.handlers.clear()

        # 設定 handlers
        self._setup_file_handler()
        self._setup_console_handler()

    def _setup_file_handler(self):
        """設定文件 handler（帶日誌輪轉）"""
        # 日誌文件名包含日期
        log_file = self.log_dir / f"syncmcp_{datetime.now().strftime('%Y%m%d')}.log"

        # 使用 RotatingFileHandler 實現日誌輪轉
        # 每個文件最大 10MB，保留 5 個備份
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
        )
        file_handler.setLevel(logging.DEBUG)

        # 詳細格式（用於文件）
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        self.logger.addHandler(file_handler)

    def _setup_console_handler(self):
        """設定控制台 handler"""
        console_handler = logging.StreamHandler(sys.stderr)

        # 根據 verbose 設定級別
        console_handler.setLevel(logging.DEBUG if self.verbose else logging.WARNING)

        # 簡潔格式（用於控制台）
        console_formatter = logging.Formatter(fmt="%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(console_handler)

    def debug(self, message: str, **kwargs):
        """記錄 DEBUG 級別日誌"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """記錄 INFO 級別日誌"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """記錄 WARNING 級別日誌"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """記錄 ERROR 級別日誌"""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """記錄 CRITICAL 級別日誌"""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """記錄異常（包含堆疊追蹤）"""
        self.logger.exception(message, **kwargs)

    @classmethod
    def get_logger(cls, name: str = "syncmcp", verbose: bool = False) -> "SyncMCPLogger":
        """
        獲取或創建 logger 實例

        Args:
            name: Logger 名稱
            verbose: 是否顯示詳細日誌

        Returns:
            SyncMCPLogger 實例
        """
        return cls(name=name, verbose=verbose)

    def cleanup_old_logs(self, keep_days: int = 30):
        """
        清理舊日誌文件

        Args:
            keep_days: 保留天數（預設 30 天）
        """
        try:
            cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)

            for log_file in self.log_dir.glob("syncmcp_*.log*"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    self.info(f"Deleted old log file: {log_file.name}")

        except Exception as e:
            self.error(f"Failed to cleanup old logs: {e}")


# 全局 logger 實例
_global_logger: SyncMCPLogger | None = None


def get_logger(verbose: bool = False) -> SyncMCPLogger:
    """
    獲取全局 logger 實例

    Args:
        verbose: 是否顯示詳細日誌

    Returns:
        SyncMCPLogger 實例
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = SyncMCPLogger.get_logger(verbose=verbose)
    return _global_logger


def set_verbose(verbose: bool):
    """
    設定全局 logger 的 verbose 級別

    Args:
        verbose: 是否顯示詳細日誌
    """
    global _global_logger
    _global_logger = SyncMCPLogger.get_logger(verbose=verbose)
