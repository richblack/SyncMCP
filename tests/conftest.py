"""
Pytest 配置和共享 fixtures
"""

import json

import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """創建臨時目錄"""
    return tmp_path


@pytest.fixture
def mock_home_dir(tmp_path, monkeypatch):
    """Mock 用戶主目錄"""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture
def mock_claude_code_config(mock_home_dir):
    """Mock Claude Code 全域配置"""
    config_path = mock_home_dir / ".claude.json"
    config_data = {
        "mcpServers": {
            "filesystem": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            },
            "brave-search": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            },
        }
    }
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path


@pytest.fixture
def mock_claude_desktop_config(mock_home_dir):
    """Mock Claude Desktop 配置"""
    config_dir = mock_home_dir / "Library" / "Application Support" / "Claude"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "claude_desktop_config.json"
    config_data = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            }
        }
    }
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path


@pytest.fixture
def mock_roo_code_config(mock_home_dir):
    """Mock Roo Code 配置"""
    config_dir = mock_home_dir / ".roo-code"
    config_dir.mkdir()
    config_path = config_dir / "settings.json"
    config_data = {
        "mcpServers": {
            "context7": {"type": "streamable-http", "url": "https://mcp.context7.com/mcp"}
        }
    }
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path


@pytest.fixture
def mock_gemini_config(mock_home_dir):
    """Mock Gemini 配置"""
    config_dir = mock_home_dir / ".gemini"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    config_data = {
        "mcpServers": {
            "brave-search": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            }
        }
    }
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path


@pytest.fixture
def mock_all_configs(
    mock_claude_code_config, mock_claude_desktop_config, mock_roo_code_config, mock_gemini_config
):
    """Mock 所有客戶端配置"""
    return {
        "claude-code": mock_claude_code_config,
        "claude-desktop": mock_claude_desktop_config,
        "roo-code": mock_roo_code_config,
        "gemini": mock_gemini_config,
    }


@pytest.fixture
def mock_syncmcp_dir(mock_home_dir):
    """Mock SyncMCP 目錄結構"""
    syncmcp_dir = mock_home_dir / ".syncmcp"
    syncmcp_dir.mkdir()

    # 創建子目錄
    (syncmcp_dir / "logs").mkdir()
    (syncmcp_dir / "backups").mkdir()
    (syncmcp_dir / "history.json").write_text("[]")

    return syncmcp_dir


@pytest.fixture
def sample_mcp_config():
    """樣本 MCP 配置"""
    return {"test-mcp": {"type": "stdio", "command": "python", "args": ["-m", "test.server"]}}


@pytest.fixture
def sample_client_config_data():
    """樣本客戶端配置數據"""
    return {
        "claude-code": {
            "mcpServers": {
                "filesystem": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                },
                "context7": {"type": "http", "url": "https://mcp.context7.com/mcp"},
            }
        },
        "claude-desktop": {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                }
            }
        },
        "roo-code": {
            "mcpServers": {
                "context7": {"type": "streamable-http", "url": "https://mcp.context7.com/mcp"}
            }
        },
    }
