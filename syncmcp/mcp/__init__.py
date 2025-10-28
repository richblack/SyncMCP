"""
MCP Server 模組 - Model Context Protocol 整合

提供 MCP Server 讓 AI 助手可以管理配置同步
"""

from .server import main, server

__all__ = ["server", "main"]
