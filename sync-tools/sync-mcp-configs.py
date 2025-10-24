#!/usr/bin/env python3
"""
MCP Configuration Sync Script
同步 Claude Code, Roo Code, 和 Claude Desktop 的 MCP 設定

使用方法:
    python sync-mcp-configs.py [source]

參數:
    source: 來源配置 (claude-code, roo-code, claude-desktop, auto)
            預設為 'auto' - 自動選擇最新的配置
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import shutil

class MCPConfigSync:
    def __init__(self):
        self.home = Path.home()

        # 定義三個配置文件路徑
        self.configs = {
            'claude-code': self.home / '.claude.json',
            'roo-code': self.home / 'Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json',
            'claude-desktop': self.home / 'Library/Application Support/Claude/claude_desktop_config.json'
        }

        # 備份目錄設置為項目內的 backup/
        script_dir = Path(__file__).resolve().parent.parent
        self.backup_dir = script_dir / 'backup'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_config(self, config_type: str, config_path: Path) -> Optional[Path]:
        """備份配置文件"""
        if not config_path.exists():
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{config_type}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(config_path, backup_path)
        print(f"✅ 已備份 {config_type} -> {backup_path}")
        return backup_path

    def load_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """載入配置文件"""
        config_path = self.configs[config_type]

        if not config_path.exists():
            print(f"⚠️  {config_type} 配置文件不存在: {config_path}")
            return None

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 根據不同類型提取 mcpServers
            if config_type == 'claude-code':
                return data.get('mcpServers', {})
            elif config_type == 'roo-code':
                return data.get('mcpServers', {})
            elif config_type == 'claude-desktop':
                return data.get('mcpServers', {})

        except json.JSONDecodeError as e:
            print(f"❌ {config_type} JSON 解析錯誤: {e}")
            return None
        except Exception as e:
            print(f"❌ 讀取 {config_type} 失敗: {e}")
            return None

    def normalize_server_config(self, server_name: str, config: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        """標準化伺服器配置格式"""
        normalized = config.copy()

        # 確保有 type 欄位
        if 'type' not in normalized:
            if 'url' in normalized:
                normalized['type'] = 'streamable-http'  # Roo Code 需要 streamable-http
            elif 'command' in normalized:
                normalized['type'] = 'stdio'
            else:
                normalized['type'] = 'stdio'
        # 修正 http -> streamable-http (Roo Code 不支持純 http)
        elif normalized.get('type') == 'http':
            normalized['type'] = 'streamable-http'

        # Roo Code 特有欄位轉換
        if source_type == 'roo-code':
            # Roo Code 使用 autoApprove, alwaysAllow
            normalized.pop('autoApprove', None)
            normalized.pop('alwaysAllow', None)
            normalized.pop('disabled', None)

        return normalized

    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """合併多個配置,後面的優先級更高"""
        merged = {}

        for config in configs:
            if config:
                merged.update(config)

        return merged

    def get_latest_config(self) -> tuple[str, Dict[str, Any]]:
        """獲取最新修改的配置作為來源"""
        latest_type = None
        latest_mtime = 0

        for config_type, config_path in self.configs.items():
            if config_path.exists():
                mtime = config_path.stat().st_mtime
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_type = config_type

        if latest_type:
            config = self.load_config(latest_type)
            print(f"📍 檢測到最新配置: {latest_type} (修改時間: {datetime.fromtimestamp(latest_mtime)})")
            return latest_type, config or {}

        return None, {}

    def write_claude_code_config(self, mcp_servers: Dict[str, Any]):
        """寫入 Claude Code 配置"""
        config_path = self.configs['claude-code']

        # 讀取現有配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = json.load(f)
        else:
            full_config = {}

        # 更新 mcpServers
        full_config['mcpServers'] = mcp_servers

        # 寫回
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(full_config, f, indent=2, ensure_ascii=False)

        print(f"✅ 已更新 Claude Code: {config_path}")

    def write_roo_code_config(self, mcp_servers: Dict[str, Any]):
        """寫入 Roo Code 配置"""
        config_path = self.configs['roo-code']

        # 確保目錄存在
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Roo Code 格式
        roo_config = {
            'mcpServers': mcp_servers
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(roo_config, f, indent=2, ensure_ascii=False)

        print(f"✅ 已更新 Roo Code: {config_path}")

    def write_claude_desktop_config(self, mcp_servers: Dict[str, Any]):
        """寫入 Claude Desktop 配置"""
        config_path = self.configs['claude-desktop']

        # Claude Desktop 格式 (不需要 type 欄位,且不支持 HTTP MCP)
        desktop_servers = {}
        skipped_http = []

        for name, config in mcp_servers.items():
            # 跳過 HTTP/streamable-http 類型的 MCP (Claude Desktop 不支持)
            if config.get('type') in ['http', 'streamable-http', 'sse']:
                skipped_http.append(name)
                continue

            server_config = config.copy()
            server_config.pop('type', None)  # 移除 type 欄位
            desktop_servers[name] = server_config

        desktop_config = {
            'mcpServers': desktop_servers
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(desktop_config, f, indent=2, ensure_ascii=False)

        print(f"✅ 已更新 Claude Desktop: {config_path}")
        if skipped_http:
            print(f"   ⚠️  跳過 HTTP MCP (Claude Desktop 不支持): {', '.join(skipped_http)}")

    def sync(self, source: str = 'auto'):
        """執行同步"""
        print("\n🔄 開始同步 MCP 配置...")
        print("=" * 60)

        # 1. 備份所有現有配置
        print("\n📦 備份現有配置...")
        for config_type, config_path in self.configs.items():
            self.backup_config(config_type, config_path)

        # 2. 確定來源配置
        if source == 'auto':
            source_type, source_config = self.get_latest_config()
            if not source_type:
                print("❌ 找不到任何配置文件")
                return False
        else:
            source_type = source
            source_config = self.load_config(source_type)
            if not source_config:
                print(f"❌ 無法載入來源配置: {source_type}")
                return False

        # 3. 載入所有配置並合併
        print(f"\n📥 載入所有配置 (以 {source_type} 為主)...")
        all_configs = []

        for config_type in ['claude-code', 'roo-code', 'claude-desktop']:
            if config_type != source_type:
                config = self.load_config(config_type)
                if config:
                    all_configs.append(config)

        # 將來源配置放在最後 (最高優先級)
        all_configs.append(source_config)

        # 合併配置
        merged_servers = self.merge_configs(*all_configs)

        # 標準化所有伺服器配置
        for server_name in merged_servers:
            merged_servers[server_name] = self.normalize_server_config(
                server_name,
                merged_servers[server_name],
                source_type
            )

        print(f"\n📊 合併後共有 {len(merged_servers)} 個 MCP 伺服器:")
        for i, name in enumerate(sorted(merged_servers.keys()), 1):
            print(f"   {i}. {name}")

        # 4. 寫入所有配置文件
        print(f"\n💾 同步到所有客戶端...")
        try:
            self.write_claude_code_config(merged_servers)
            self.write_roo_code_config(merged_servers)
            self.write_claude_desktop_config(merged_servers)
        except Exception as e:
            print(f"\n❌ 同步失敗: {e}")
            print(f"💡 可以從備份恢復: {self.backup_dir}")
            return False

        print("\n" + "=" * 60)
        print("✨ 同步完成!")
        print(f"📁 備份位置: {self.backup_dir}")
        print("\n💡 提示:")
        print("   - 重啟 Claude Code 和 Roo Code 以載入新配置")
        print("   - Claude Desktop 會自動重新載入")

        return True

    def compare_configs(self):
        """比較三個配置的差異"""
        print("\n🔍 比較配置差異...")
        print("=" * 60)

        configs = {}
        for config_type in ['claude-code', 'roo-code', 'claude-desktop']:
            config = self.load_config(config_type)
            if config:
                configs[config_type] = set(config.keys())

        if not configs:
            print("❌ 沒有找到任何配置文件")
            return

        # 所有伺服器
        all_servers = set()
        for servers in configs.values():
            all_servers.update(servers)

        print(f"\n📊 總共發現 {len(all_servers)} 個不同的 MCP 伺服器\n")

        # 列出每個伺服器在哪些配置中
        for server in sorted(all_servers):
            locations = []
            for config_type, servers in configs.items():
                if server in servers:
                    locations.append(config_type)

            status = "✅" if len(locations) == len(configs) else "⚠️ "
            print(f"{status} {server:25} -> {', '.join(locations)}")

        # 顯示不一致的統計
        inconsistent = [s for s in all_servers
                       if not all(s in servers for servers in configs.values())]

        if inconsistent:
            print(f"\n⚠️  發現 {len(inconsistent)} 個不同步的伺服器")
        else:
            print(f"\n✅ 所有配置完全同步!")


def main():
    sync_tool = MCPConfigSync()

    # 解析命令行參數
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command in ['compare', 'diff', 'status']:
            sync_tool.compare_configs()
        elif command in ['claude-code', 'roo-code', 'claude-desktop', 'auto']:
            sync_tool.sync(source=command)
        elif command in ['help', '--help', '-h']:
            print(__doc__)
            print("\n可用命令:")
            print("  python sync-mcp-configs.py [source]  - 執行同步")
            print("  python sync-mcp-configs.py compare   - 比較配置差異")
            print("  python sync-mcp-configs.py help      - 顯示幫助")
            print("\n來源選項 (source):")
            print("  auto (預設)    - 自動選擇最新修改的配置")
            print("  claude-code    - 以 Claude Code 為準")
            print("  roo-code       - 以 Roo Code 為準")
            print("  claude-desktop - 以 Claude Desktop 為準")
        else:
            print(f"❌ 未知命令: {command}")
            print("使用 'python sync-mcp-configs.py help' 查看幫助")
    else:
        # 預設行為:先比較,然後詢問是否同步
        sync_tool.compare_configs()
        print("\n" + "=" * 60)
        response = input("\n是否要執行同步? (y/n): ").strip().lower()
        if response == 'y':
            sync_tool.sync('auto')


if __name__ == '__main__':
    main()
