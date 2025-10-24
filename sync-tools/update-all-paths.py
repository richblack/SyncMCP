#!/usr/bin/env python3
"""
更新所有配置中的路徑
當 SyncMCP 目錄改變位置或名稱時使用
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil
import os

class PathUpdater:
    def __init__(self):
        self.home = Path.home()

        # 配置文件路徑
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

    def detect_current_path(self) -> str:
        """偵測當前腳本所在的路徑"""
        script_path = Path(__file__).resolve()
        # 從 /path/to/SyncMCP/sync-tools/update-all-paths.py
        # 取得 /path/to/SyncMCP
        sync_mcp_dir = script_path.parent.parent
        return str(sync_mcp_dir)

    def backup_config(self, config_path: Path, name: str) -> Path:
        """備份配置文件"""
        if not config_path.exists():
            print(f"⚠️  {name} 配置不存在: {config_path}")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{name}_path_update_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(config_path, backup_path)
        print(f"✅ 已備份 {name} -> {backup_path.name}")
        return backup_path

    def load_json(self, path: Path) -> dict:
        """載入 JSON 配置"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_json(self, path: Path, data: dict):
        """保存 JSON 配置 (原子寫入)"""
        temp_path = path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(path)

    def update_image_gen_path(self, config_name: str, config_path: Path, new_base_path: str) -> bool:
        """更新 image-gen MCP 路徑"""
        if not config_path.exists():
            print(f"⚠️  跳過 {config_name}: 配置文件不存在")
            return False

        try:
            data = self.load_json(config_path)

            if 'image-gen' not in data.get('mcpServers', {}):
                print(f"ℹ️  {config_name}: 無 image-gen MCP")
                return False

            image_gen = data['mcpServers']['image-gen']

            if 'args' not in image_gen:
                print(f"⚠️  {config_name}: image-gen 無 args 欄位")
                return False

            # 更新路徑
            new_path = f"{new_base_path}/mcp-sources/image-gen-mcp"
            updated = False

            for i, arg in enumerate(image_gen['args']):
                if 'image-gen-mcp' in arg:
                    old_path = arg
                    image_gen['args'][i] = new_path
                    updated = True
                    print(f"   📝 {config_name}:")
                    print(f"      舊: {old_path}")
                    print(f"      新: {new_path}")
                    break

            if not updated:
                print(f"ℹ️  {config_name}: 未找到需要更新的路徑")
                return False

            self.save_json(config_path, data)
            print(f"✅ {config_name}: 路徑已更新")
            return True

        except Exception as e:
            print(f"❌ {config_name} 更新失敗: {e}")
            return False

    def update_backup_dir_path(self, new_base_path: str):
        """更新同步腳本中的備份目錄路徑"""
        sync_tools_dir = Path(new_base_path) / 'sync-tools'

        scripts = [
            'sync-mcp-configs-smart.py',
            'sync-mcp-configs.py',
            'sync-to-gemini.py',
            'fix-google-mcp.py',
            'update-image-gen-path.py'
        ]

        print("\n🔧 更新同步腳本中的路徑引用...")

        for script_name in scripts:
            script_path = sync_tools_dir / script_name
            if not script_path.exists():
                continue

            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 不需要更新，因為使用 Path.home() 相對路徑
                if 'Path.home()' in content and 'Documents/mcp-config-backups' in content:
                    print(f"✅ {script_name}: 使用相對路徑，無需更新")
                else:
                    print(f"ℹ️  {script_name}: 檢查完成")

            except Exception as e:
                print(f"⚠️  {script_name}: {e}")

    def update_all(self, old_path: str = None, new_path: str = None) -> dict:
        """更新所有路徑"""
        # 自動偵測當前路徑
        if new_path is None:
            new_path = self.detect_current_path()

        print("\n🔄 開始更新所有路徑...")
        print("=" * 70)
        print(f"新的 SyncMCP 路徑: {new_path}")
        print("=" * 70)

        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }

        # 1. 備份所有配置
        print("\n📦 備份配置...")
        for name, config_path in self.configs.items():
            self.backup_config(config_path, name)

        # 2. 更新 image-gen-mcp 路徑
        print("\n🔧 更新 image-gen-mcp 路徑...")
        for name, config_path in self.configs.items():
            if self.update_image_gen_path(name, config_path, new_path):
                results['success'].append(name)
            else:
                results['skipped'].append(name)

        # 3. 檢查同步腳本
        self.update_backup_dir_path(new_path)

        # 4. 總結
        print("\n" + "=" * 70)
        print("✨ 路徑更新完成!")
        print(f"📁 備份位置: {self.backup_dir}")
        print(f"📁 新的 SyncMCP 位置: {new_path}")

        print(f"\n📊 更新結果:")
        if results['success']:
            print(f"   ✅ 成功: {len(results['success'])} 個")
            for name in results['success']:
                print(f"      - {name}")

        if results['skipped']:
            print(f"   ℹ️  跳過: {len(results['skipped'])} 個")
            for name in results['skipped']:
                print(f"      - {name}")

        if results['failed']:
            print(f"   ❌ 失敗: {len(results['failed'])} 個")
            for name in results['failed']:
                print(f"      - {name}")

        return results

    def verify_paths(self):
        """驗證所有路徑"""
        print("\n🔍 驗證路徑...")
        print("=" * 70)

        for name, config_path in self.configs.items():
            if not config_path.exists():
                continue

            try:
                data = self.load_json(config_path)
                if 'image-gen' in data.get('mcpServers', {}):
                    args = data['mcpServers']['image-gen'].get('args', [])
                    for arg in args:
                        if 'image-gen-mcp' in arg:
                            print(f"✅ {name}:")
                            print(f"   {arg}")
                            break
            except Exception as e:
                print(f"❌ {name}: 無法驗證 - {e}")

        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='更新所有配置中的 SyncMCP 路徑',
        epilog='當 SyncMCP 目錄被重命名或移動時使用此工具'
    )
    parser.add_argument('--yes', '-y', action='store_true', help='自動確認,不詢問')
    parser.add_argument('--verify-only', action='store_true', help='僅驗證路徑,不更新')
    parser.add_argument('--new-path', help='手動指定新的 SyncMCP 路徑')
    args = parser.parse_args()

    updater = PathUpdater()

    if args.verify_only:
        updater.verify_paths()
        return

    # 偵測當前路徑
    current_path = updater.detect_current_path()

    print("\n📋 SyncMCP 路徑更新工具")
    print("   - 自動偵測當前 SyncMCP 位置")
    print("   - 更新所有 AI 客戶端配置")
    print("   - 自動備份所有變更")
    print(f"\n📍 偵測到的 SyncMCP 路徑:")
    print(f"   {current_path}")

    if args.new_path:
        current_path = args.new_path
        print(f"\n⚠️  使用手動指定的路徑: {current_path}")

    if not args.yes:
        response = input("\n是否使用此路徑更新配置? (y/n): ").strip().lower()
        if response != 'y':
            print("取消操作")
            return

    # 執行更新
    results = updater.update_all(new_path=current_path)

    # 驗證
    updater.verify_paths()

    # 提示
    print("\n💡 重要提示:")
    print("   1. 重啟所有 AI 客戶端以載入新配置")
    print("   2. 測試 image-gen MCP 功能")
    print("   3. 同步腳本無需修改 (使用相對路徑)")
    print("\n📝 如需回復:")
    print(f"   從備份目錄恢復: {updater.backup_dir}")

    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
