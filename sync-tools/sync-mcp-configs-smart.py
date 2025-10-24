#!/usr/bin/env python3
"""
智能 MCP 配置同步腳本 (基於時間戳)
對於每個 MCP 伺服器,選擇最新修改的版本進行同步

使用方法:
    python sync-mcp-configs-smart.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import shutil
import hashlib

class SmartMCPConfigSync:
    def __init__(self):
        self.home = Path.home()

        # 定義四個配置文件路徑
        self.configs = {
            'claude-code': self.home / '.claude.json',
            'roo-code': self.home / 'Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json',
            'claude-desktop': self.home / 'Library/Application Support/Claude/claude_desktop_config.json',
            'gemini-cli': self.home / '.gemini/settings.json'
        }

        # 備份目錄設置為項目內的 backup/
        script_dir = Path(__file__).resolve().parent.parent
        self.backup_dir = script_dir / 'backup'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 存儲每個配置文件的修改時間
        self.config_mtimes = {}

    def get_config_mtime(self, config_type: str) -> Optional[float]:
        """獲取配置文件的修改時間"""
        config_path = self.configs[config_type]
        if config_path.exists():
            return config_path.stat().st_mtime
        return None

    def backup_config(self, config_type: str, config_path: Path) -> Optional[Path]:
        """備份配置文件"""
        if not config_path.exists():
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{config_type}_smart_{timestamp}.json"
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
            # 獲取文件修改時間
            mtime = config_path.stat().st_mtime
            self.config_mtimes[config_type] = mtime

            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 根據不同類型提取 mcpServers
            if config_type in ['claude-code', 'roo-code', 'claude-desktop', 'gemini-cli']:
                return data.get('mcpServers', {})

        except json.JSONDecodeError as e:
            print(f"❌ {config_type} JSON 解析錯誤: {e}")
            return None
        except Exception as e:
            print(f"❌ 讀取 {config_type} 失敗: {e}")
            return None

    def get_server_hash(self, server_config: Dict[str, Any]) -> str:
        """計算伺服器配置的哈希值"""
        # 移除可能變化但不影響配置本質的欄位
        config_copy = server_config.copy()
        config_copy.pop('autoApprove', None)
        config_copy.pop('alwaysAllow', None)
        config_copy.pop('disabled', None)

        # 排序並序列化為JSON字符串
        config_str = json.dumps(config_copy, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()

    def smart_merge_servers(self, all_servers: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        智能合併伺服器配置

        Args:
            all_servers: {
                'server_name': {
                    'claude-code': {...config...},
                    'roo-code': {...config...},
                    'claude-desktop': {...config...}
                }
            }

        Returns:
            合併後的配置
        """
        merged = {}

        for server_name, configs in all_servers.items():
            # 為每個來源計算配置哈希和修改時間
            candidates = []

            for source, config in configs.items():
                if config is None:
                    continue

                config_hash = self.get_server_hash(config)
                mtime = self.config_mtimes.get(source, 0)

                candidates.append({
                    'source': source,
                    'config': config,
                    'hash': config_hash,
                    'mtime': mtime
                })

            if not candidates:
                continue

            # 按修改時間排序,選擇最新的
            candidates.sort(key=lambda x: x['mtime'], reverse=True)
            winner = candidates[0]

            merged[server_name] = winner['config'].copy()

            # 如果有多個不同版本,顯示選擇信息
            unique_hashes = set(c['hash'] for c in candidates)
            if len(unique_hashes) > 1:
                mtime_str = datetime.fromtimestamp(winner['mtime']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"   🔄 {server_name}: 選擇 {winner['source']} (最新: {mtime_str})")

        return merged

    def normalize_server_config(self, server_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """標準化伺服器配置格式"""
        normalized = config.copy()

        # 確保有 type 欄位
        if 'type' not in normalized:
            if 'url' in normalized:
                normalized['type'] = 'streamable-http'
            elif 'command' in normalized:
                normalized['type'] = 'stdio'
            else:
                normalized['type'] = 'stdio'
        # 修正 http -> streamable-http
        elif normalized.get('type') == 'http':
            normalized['type'] = 'streamable-http'

        # 移除 Roo Code 特有欄位
        normalized.pop('autoApprove', None)
        normalized.pop('alwaysAllow', None)
        normalized.pop('disabled', None)

        return normalized

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
            # 跳過 HTTP/streamable-http 類型的 MCP
            if config.get('type') in ['http', 'streamable-http', 'sse']:
                skipped_http.append(name)
                continue

            server_config = config.copy()
            server_config.pop('type', None)
            desktop_servers[name] = server_config

        desktop_config = {
            'mcpServers': desktop_servers
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(desktop_config, f, indent=2, ensure_ascii=False)

        print(f"✅ 已更新 Claude Desktop: {config_path}")
        if skipped_http:
            print(f"   ⚠️  跳過 HTTP MCP (Claude Desktop 不支持): {', '.join(skipped_http)}")

    def write_gemini_cli_config(self, mcp_servers: Dict[str, Any]):
        """寫入 Gemini CLI 配置"""
        config_path = self.configs['gemini-cli']

        # 確保目錄存在
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # 讀取現有配置 (保留其他設定)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = json.load(f)
        else:
            full_config = {}

        # 更新 mcpServers
        full_config['mcpServers'] = mcp_servers

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(full_config, f, indent=2, ensure_ascii=False)

        print(f"✅ 已更新 Gemini CLI: {config_path}")

    def sync(self):
        """執行智能同步"""
        print("\n🔄 開始智能同步 MCP 配置...")
        print("="*60)

        # 1. 備份所有現有配置
        print("\n📦 備份現有配置...")
        for config_type, config_path in self.configs.items():
            self.backup_config(config_type, config_path)

        # 2. 載入所有配置
        print(f"\n📥 載入所有配置...")
        configs = {}
        for config_type in ['claude-code', 'roo-code', 'claude-desktop', 'gemini-cli']:
            config = self.load_config(config_type)
            if config:
                configs[config_type] = config
                mtime_str = datetime.fromtimestamp(self.config_mtimes[config_type]).strftime('%Y-%m-%d %H:%M:%S')
                print(f"   ✅ {config_type}: {len(config)} 個伺服器 (修改: {mtime_str})")

        # 3. 收集所有伺服器
        all_server_names = set()
        for config in configs.values():
            all_server_names.update(config.keys())

        print(f"\n📊 發現 {len(all_server_names)} 個不同的 MCP 伺服器")

        # 4. 為每個伺服器收集所有版本
        all_servers = {}
        for server_name in all_server_names:
            all_servers[server_name] = {}
            for config_type, config in configs.items():
                all_servers[server_name][config_type] = config.get(server_name)

        # 5. 智能合併 (選擇最新版本)
        print(f"\n🧠 智能合併 (選擇最新修改的版本)...")
        merged_servers = self.smart_merge_servers(all_servers)

        # 6. 標準化所有伺服器配置
        for server_name in merged_servers:
            merged_servers[server_name] = self.normalize_server_config(
                server_name,
                merged_servers[server_name]
            )

        print(f"\n📊 合併後共有 {len(merged_servers)} 個 MCP 伺服器:")
        for i, name in enumerate(sorted(merged_servers.keys()), 1):
            print(f"   {i}. {name}")

        # 7. 寫入所有配置文件
        print(f"\n💾 同步到所有客戶端...")
        try:
            self.write_claude_code_config(merged_servers)
            self.write_roo_code_config(merged_servers)
            self.write_claude_desktop_config(merged_servers)
            self.write_gemini_cli_config(merged_servers)
        except Exception as e:
            print(f"\n❌ 同步失敗: {e}")
            print(f"💡 可以從備份恢復: {self.backup_dir}")
            return False

        print("\n" + "="*60)
        print("✨ 智能同步完成!")
        print(f"📁 備份位置: {self.backup_dir}")
        print("\n💡 提示:")
        print("   - 重啟 Claude Code 和 Roo Code 以載入新配置")
        print("   - Claude Desktop 和 Gemini CLI 會自動重新載入")
        print("\n🎯 智能同步特性:")
        print("   - 自動選擇最新修改的配置版本")
        print("   - 正確處理 HTTP MCP (Claude Desktop 不支持)")
        print("   - 自動標準化格式 (type 欄位)")
        print("   - 同步到 4 個客戶端: Claude Code, Roo Code, Claude Desktop, Gemini CLI")

        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description='智能 MCP 配置同步工具')
    parser.add_argument('--yes', '-y', action='store_true', help='自動確認,不詢問')
    args = parser.parse_args()

    syncer = SmartMCPConfigSync()

    print("\n📋 智能 MCP 配置同步工具")
    print("   - 對於每個 MCP 伺服器,自動選擇最新修改的版本")
    print("   - 自動備份所有配置")
    print("   - 處理不同客戶端的格式差異")

    if not args.yes:
        response = input("\n是否繼續? (y/n): ").strip().lower()
        if response != 'y':
            print("取消操作")
            return

    success = syncer.sync()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
