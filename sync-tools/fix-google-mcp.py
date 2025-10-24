#!/usr/bin/env python3
"""
Google MCP 配置修復腳本
修正 Google Workspace OAuth 憑證並移除重複的 Google MCP 伺服器
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil

class GoogleMCPFixer:
    def __init__(self):
        self.home = Path.home()

        # 配置文件路徑
        self.configs = {
            'claude-code': self.home / '.claude.json',
            'roo-code': self.home / 'Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json',
            'claude-desktop': self.home / 'Library/Application Support/Claude/claude_desktop_config.json'
        }

        # OAuth 憑證路徑
        self.oauth_creds_path = self.home / 'Documents/google-credentials/Google Auth Richblack Client Secret.json'

        # 備份目錄設置為項目內的 backup/
        script_dir = Path(__file__).resolve().parent.parent
        self.backup_dir = script_dir / 'backup'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 要移除的重複 MCP
        self.redundant_mcps = ['google-sheets', 'google-slides', 'gdrive']

        # 正確的 OAuth 憑證
        self.correct_oauth = None

    def load_oauth_credentials(self):
        """載入正確的 OAuth 憑證"""
        if not self.oauth_creds_path.exists():
            print(f"❌ OAuth 憑證檔案不存在: {self.oauth_creds_path}")
            return False

        try:
            with open(self.oauth_creds_path, 'r', encoding='utf-8') as f:
                oauth_data = json.load(f)

            # 提取 web 客戶端憑證
            if 'web' in oauth_data:
                self.correct_oauth = {
                    'client_id': oauth_data['web']['client_id'],
                    'client_secret': oauth_data['web']['client_secret']
                }
                print(f"✅ 已載入 OAuth 憑證")
                print(f"   Client ID: {self.correct_oauth['client_id']}")
                print(f"   Client Secret: {self.correct_oauth['client_secret'][:20]}...")
                return True
            else:
                print("❌ OAuth 憑證格式不正確")
                return False

        except Exception as e:
            print(f"❌ 載入 OAuth 憑證失敗: {e}")
            return False

    def backup_config(self, config_type, config_path):
        """備份配置文件"""
        if not config_path.exists():
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{config_type}_google_fix_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(config_path, backup_path)
        print(f"✅ 已備份 {config_type} -> {backup_path}")
        return backup_path

    def fix_config(self, config_type):
        """修復單個配置文件"""
        config_path = self.configs[config_type]

        if not config_path.exists():
            print(f"⚠️  {config_type} 配置文件不存在,跳過")
            return True

        try:
            # 讀取配置
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_type == 'claude-code':
                    full_config = json.load(f)
                    mcp_servers = full_config.get('mcpServers', {})
                else:
                    data = json.load(f)
                    mcp_servers = data.get('mcpServers', {})

            changes_made = False

            # 1. 修正 Google Workspace OAuth 憑證
            if 'google-workspace' in mcp_servers:
                workspace_config = mcp_servers['google-workspace']

                if 'env' in workspace_config:
                    old_secret = workspace_config['env'].get('GOOGLE_OAUTH_CLIENT_SECRET', '')
                    new_secret = self.correct_oauth['client_secret']

                    if old_secret != new_secret:
                        print(f"\n🔧 修正 {config_type} 的 Google Workspace OAuth 憑證")
                        print(f"   舊憑證: {old_secret[:20]}...")
                        print(f"   新憑證: {new_secret[:20]}...")

                        workspace_config['env']['GOOGLE_OAUTH_CLIENT_ID'] = self.correct_oauth['client_id']
                        workspace_config['env']['GOOGLE_OAUTH_CLIENT_SECRET'] = self.correct_oauth['client_secret']
                        changes_made = True

            # 2. 移除重複的 Google MCP
            removed = []
            for mcp_name in self.redundant_mcps:
                if mcp_name in mcp_servers:
                    del mcp_servers[mcp_name]
                    removed.append(mcp_name)
                    changes_made = True

            if removed:
                print(f"\n🗑️  從 {config_type} 移除重複的 MCP: {', '.join(removed)}")

            # 3. 寫回配置
            if changes_made:
                if config_type == 'claude-code':
                    full_config['mcpServers'] = mcp_servers
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(full_config, f, indent=2, ensure_ascii=False)
                else:
                    data['mcpServers'] = mcp_servers
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"✅ 已更新 {config_type}: {config_path}")
            else:
                print(f"ℹ️  {config_type} 無需更新")

            return True

        except Exception as e:
            print(f"❌ 修復 {config_type} 失敗: {e}")
            return False

    def run(self):
        """執行修復"""
        print("\n" + "="*60)
        print("🔧 Google MCP 配置修復工具")
        print("="*60)

        # 1. 載入正確的 OAuth 憑證
        print("\n📥 載入 OAuth 憑證...")
        if not self.load_oauth_credentials():
            print("\n❌ 無法載入 OAuth 憑證,終止修復")
            return False

        # 2. 備份所有配置
        print("\n📦 備份現有配置...")
        for config_type, config_path in self.configs.items():
            self.backup_config(config_type, config_path)

        # 3. 修復所有配置
        print("\n🔧 開始修復配置...")
        success = True

        for config_type in ['claude-code', 'roo-code', 'claude-desktop']:
            if not self.fix_config(config_type):
                success = False

        # 4. 顯示結果
        print("\n" + "="*60)
        if success:
            print("✨ 修復完成!")
            print("\n📋 變更摘要:")
            print("   ✅ 已修正 Google Workspace OAuth 憑證")
            print(f"   ✅ 已移除重複的 MCP: {', '.join(self.redundant_mcps)}")
            print(f"\n📁 備份位置: {self.backup_dir}")
            print("\n💡 下一步:")
            print("   1. 重啟 Claude Code")
            print("   2. 重新載入 Roo Code (重啟 VS Code)")
            print("   3. Claude Desktop 會自動重新載入")
            print("\n🧪 測試 Google Workspace:")
            print("   在 Claude Code 中嘗試使用 Google Workspace 相關功能")
            print("   首次使用會需要進行 OAuth 授權")
        else:
            print("❌ 修復過程中發生錯誤")
            print(f"💡 可以從備份恢復: {self.backup_dir}")

        print("="*60 + "\n")
        return success

def main():
    fixer = GoogleMCPFixer()

    # 顯示將要進行的操作
    print("\n📋 此腳本將執行以下操作:")
    print("   1. 修正 Google Workspace 的 OAuth 憑證")
    print("   2. 移除重複的 Google MCP (google-sheets, google-slides, gdrive)")
    print("   3. 同步到所有客戶端 (Claude Code, Roo Code, Claude Desktop)")
    print("   4. 自動備份所有配置")

    response = input("\n是否繼續? (y/n): ").strip().lower()
    if response != 'y':
        print("取消操作")
        return

    success = fixer.run()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
