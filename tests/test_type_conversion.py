#!/usr/bin/env python3
"""
測試 MCP 類型轉換邏輯
"""

import importlib.util

# 直接執行腳本文件
import sys
from pathlib import Path

# 動態載入模組
spec = importlib.util.spec_from_file_location(
    "sync_module", Path(__file__).parent.parent / "sync-tools" / "sync-mcp-configs-smart.py"
)
sync_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_module)

SmartMCPConfigSync = sync_module.SmartMCPConfigSync


def test_type_conversion():
    """測試所有類型轉換場景"""
    syncer = SmartMCPConfigSync()

    print("🧪 測試 MCP 類型轉換邏輯")
    print("=" * 70)

    # 測試案例 1: Roo Code (streamable-http) → Claude Code
    print("\n📋 測試 1: Roo Code (streamable-http 無 headers) → Claude Code")
    roo_config_no_headers = {
        "type": "streamable-http",
        "url": "https://mcp.canva.com/mcp",
        "alwaysAllow": ["tool1"],
    }
    result = syncer.normalize_server_config(roo_config_no_headers, "claude-code")
    print(f"   輸入: {roo_config_no_headers}")
    print(f"   輸出: {result}")
    assert result["type"] == "sse", f"❌ 預期 'sse'，實際 '{result['type']}'"
    assert "alwaysAllow" not in result, "❌ Roo 特有欄位應該被移除"
    print("   ✅ 通過：streamable-http → sse, Roo 欄位已移除")

    # 測試案例 2: Roo Code (streamable-http 有 headers) → Claude Code
    print("\n📋 測試 2: Roo Code (streamable-http 有 headers) → Claude Code")
    roo_config_with_headers = {
        "type": "streamable-http",
        "url": "https://mcp.context7.com/mcp",
        "headers": {"API_KEY": "xxx"},
        "alwaysAllow": ["tool1"],
    }
    result = syncer.normalize_server_config(roo_config_with_headers, "claude-code")
    print(f"   輸入: {roo_config_with_headers}")
    print(f"   輸出: {result}")
    assert result["type"] == "http", f"❌ 預期 'http'，實際 '{result['type']}'"
    assert "alwaysAllow" not in result, "❌ Roo 特有欄位應該被移除"
    print("   ✅ 通過：streamable-http + headers → http")

    # 測試案例 3: Claude Code (http) → Roo Code
    print("\n📋 測試 3: Claude Code (http) → Roo Code")
    claude_config = {
        "type": "http",
        "url": "https://mcp.example.com/mcp",
        "headers": {"API_KEY": "xxx"},
    }
    result = syncer.normalize_server_config(claude_config, "roo-code")
    print(f"   輸入: {claude_config}")
    print(f"   輸出: {result}")
    assert (
        result["type"] == "streamable-http"
    ), f"❌ 預期 'streamable-http'，實際 '{result['type']}'"
    print("   ✅ 通過：http → streamable-http")

    # 測試案例 4: Claude Code (sse) → Roo Code
    print("\n📋 測試 4: Claude Code (sse) → Roo Code")
    claude_sse = {"type": "sse", "url": "https://mcp.example.com/mcp"}
    result = syncer.normalize_server_config(claude_sse, "roo-code")
    print(f"   輸入: {claude_sse}")
    print(f"   輸出: {result}")
    assert (
        result["type"] == "streamable-http"
    ), f"❌ 預期 'streamable-http'，實際 '{result['type']}'"
    print("   ✅ 通過：sse → streamable-http")

    # 測試案例 5: stdio 保持不變（所有客戶端）
    print("\n📋 測試 5: stdio 類型在所有客戶端保持一致")
    stdio_config = {"type": "stdio", "command": "npx", "args": ["-y", "some-server"]}
    for client in ["claude-code", "roo-code", "gemini"]:
        result = syncer.normalize_server_config(stdio_config, client)
        print(f"   {client}: {result.get('type')}")
        assert result["type"] == "stdio", f"❌ {client} 應該保持 stdio"

    # Claude Desktop 特殊：移除 type
    result = syncer.normalize_server_config(stdio_config, "claude-desktop")
    print(f"   claude-desktop: {'無 type 欄位' if 'type' not in result else result.get('type')}")
    assert "type" not in result, "❌ Desktop 不應該有 type 欄位"
    print("   ✅ 通過：stdio 在所有客戶端正確處理")

    # 測試案例 6: 遠端 MCP 被 Claude Desktop 過濾
    print("\n📋 測試 6: Claude Desktop 過濾所有遠端 MCP")
    for mcp_type in ["http", "sse", "streamable-http"]:
        remote_config = {"type": mcp_type, "url": "https://mcp.example.com/mcp"}
        result = syncer.normalize_server_config(remote_config, "claude-desktop")
        print(f"   {mcp_type} → {result}")
        assert result is None, f"❌ {mcp_type} 應該被 Desktop 過濾"
    print("   ✅ 通過：Desktop 正確過濾所有遠端 MCP")

    # 測試案例 7: 缺少 type 欄位的推斷
    print("\n📋 測試 7: 缺少 type 欄位時的推斷邏輯")
    incomplete_remote = {"url": "https://mcp.example.com/mcp"}
    result = syncer.normalize_server_config(incomplete_remote, "claude-code")
    print(f"   有 url 但缺少 type → Claude Code: {result['type']}")
    assert result["type"] == "sse", f"❌ 預期推斷為 'sse'，實際 '{result['type']}'"

    result = syncer.normalize_server_config(incomplete_remote, "roo-code")
    print(f"   有 url 但缺少 type → Roo Code: {result['type']}")
    assert result["type"] == "streamable-http", "❌ 預期推斷為 'streamable-http'"
    print("   ✅ 通過：正確推斷缺失的 type")

    # 測試案例 8: Gemini 轉換
    print("\n📋 測試 8: Gemini CLI 轉換")
    http_config = {"type": "http", "url": "https://mcp.example.com/mcp"}
    result = syncer.normalize_server_config(http_config, "gemini")
    print(f"   http → {result['type']}")
    assert result["type"] == "streamable-http", "❌ 預期 'streamable-http'"
    print("   ✅ 通過：Gemini 正確使用 streamable-http")

    print("\n" + "=" * 70)
    print("✅ 所有測試通過！類型轉換邏輯正確。")
    return True


if __name__ == "__main__":
    try:
        test_type_conversion()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 測試失敗：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 錯誤：{e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
