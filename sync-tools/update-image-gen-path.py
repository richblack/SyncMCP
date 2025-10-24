#!/usr/bin/env python3
"""
更新所有客戶端配置中的 image-gen-mcp 路徑

從: /Users/youlinhsieh/Documents/mcps/image-gen-mcp
到: /Users/youlinhsieh/Documents/mcps/mcp-sources/image-gen-mcp
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil

class ImageGenPathUpdater:
    def __init__(self):
        self.home = Path.home()

        # 配置文件路徑
        self.configs = {
            'claude-code': self.home / '.claude.json',
            'roo-code': self.home / 'Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json',
            'claude-desktop': self.home / 'Library/Application Support/Claude/claude_desktop_config.json',
            'gemini-cli': self.home / '.gemini/settings.json'
        }

        # 路徑配置
        self.old_path = "/Users/youlinhsieh/Documents/mcps/image-gen-mcp"
        self.new_path = "/Users/youlinhsieh/Documents/mcps/mcp-sources/image-gen-mcp"

        # 備份目錄設置為項目內的 backup/
        script_dir = Path(__file__).resolve().parent.parent
        self.backup_dir = script_dir / 'backup'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

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

    def update_path_in_config(self, config_name: str, config_path: Path) -> bool:
        """更新單個配置文件中的路徑"""
        if not config_path.exists():
            print(f"⚠️  跳過 {config_name}: 配置文件不存在")
            return False

        try:
            # 載入配置
            data = self.load_json(config_path)

            # 檢查是否有 image-gen MCP
            if 'image-gen' not in data.get('mcpServers', {}):
                print(f"⚠️  {config_name}: 無 image-gen MCP")
                return False

            # 獲取 image-gen 配置
            image_gen = data['mcpServers']['image-gen']

            # 檢查 args 中是否有舊路徑
            if 'args' not in image_gen:
                print(f"⚠️  {config_name}: image-gen 無 args 欄位")
                return False

            # 查找並更新路徑
            updated = False
            for i, arg in enumerate(image_gen['args']):
                if arg == self.old_path:
                    image_gen['args'][i] = self.new_path
                    updated = True
                    break

            if not updated:
                print(f"ℹ️  {config_name}: 路徑已是最新 (或格式不同)")
                return False

            # 保存更新
            self.save_json(config_path, data)
            print(f"✅ {config_name}: 路徑已更新")
            return True

        except Exception as e:
            print(f"❌ {config_name} 更新失敗: {e}")
            return False

    def update_all(self) -> dict:
        """更新所有客戶端配置"""
        print("\n🔄 開始更新 image-gen-mcp 路徑...")
        print("=" * 60)
        print(f"從: {self.old_path}")
        print(f"到: {self.new_path}")
        print("=" * 60)

        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }

        # 1. 備份所有配置
        print("\n📦 備份配置...")
        for name, config_path in self.configs.items():
            self.backup_config(config_path, name)

        # 2. 更新路徑
        print("\n🔧 更新路徑...")
        for name, config_path in self.configs.items():
            if self.update_path_in_config(name, config_path):
                results['success'].append(name)
            else:
                results['skipped'].append(name)

        # 3. 總結
        print("\n" + "=" * 60)
        print("✨ 路徑更新完成!")
        print(f"📁 備份位置: {self.backup_dir}")

        print(f"\n📊 更新結果:")
        print(f"   ✅ 成功: {len(results['success'])} 個")
        if results['success']:
            for name in results['success']:
                print(f"      - {name}")

        if results['skipped']:
            print(f"   ⚠️  跳過: {len(results['skipped'])} 個")
            for name in results['skipped']:
                print(f"      - {name}")

        if results['failed']:
            print(f"   ❌ 失敗: {len(results['failed'])} 個")
            for name in results['failed']:
                print(f"      - {name}")

        return results

    def verify_paths(self):
        """驗證更新後的路徑"""
        print("\n🔍 驗證路徑...")
        print("=" * 60)

        for name, config_path in self.configs.items():
            if not config_path.exists():
                continue

            try:
                data = self.load_json(config_path)
                if 'image-gen' in data.get('mcpServers', {}):
                    args = data['mcpServers']['image-gen'].get('args', [])
                    if len(args) > 1:
                        path = args[1]
                        if path == self.new_path:
                            print(f"✅ {name}: {path}")
                        else:
                            print(f"⚠️  {name}: {path} (不是預期路徑)")
            except Exception as e:
                print(f"❌ {name}: 無法驗證 - {e}")

        print("=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='更新 image-gen-mcp 路徑')
    parser.add_argument('--yes', '-y', action='store_true', help='自動確認,不詢問')
    parser.add_argument('--verify-only', action='store_true', help='僅驗證路徑,不更新')
    args = parser.parse_args()

    updater = ImageGenPathUpdater()

    if args.verify_only:
        updater.verify_paths()
        return

    print("\n📋 image-gen-mcp 路徑更新工具")
    print("   - 更新所有 AI 客戶端配置中的 image-gen-mcp 路徑")
    print("   - 自動備份所有配置")
    print(f"   - 從: {updater.old_path}")
    print(f"   - 到: {updater.new_path}")

    if not args.yes:
        response = input("\n是否繼續? (y/n): ").strip().lower()
        if response != 'y':
            print("取消操作")
            return

    # 執行更新
    results = updater.update_all()

    # 驗證
    updater.verify_paths()

    # 提示
    print("\n💡 下一步:")
    print("   1. 重啟 AI 客戶端以載入新配置")
    print("   2. 測試 image-gen 功能是否正常")
    print("   3. 如有問題,可從備份恢復:")
    print(f"      從備份目錄: {updater.backup_dir}")

    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
