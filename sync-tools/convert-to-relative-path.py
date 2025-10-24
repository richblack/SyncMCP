#!/usr/bin/env python3
"""
將 image-gen-mcp 的絕對路徑轉換為相對路徑
支持多個 AI 客戶端配置
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil

class PathConverter:
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

    def backup_config(self, config_path: Path, name: str) -> Path:
        """備份配置文件"""
        if not config_path.exists():
            print(f"⚠️  {name} 配置不存在: {config_path}")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{name}_relative_path_{timestamp}.json"
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

    def convert_to_relative(self, config_name: str, config_path: Path) -> bool:
        """將絕對路徑轉換為相對路徑"""
        if not config_path.exists():
            print(f"⚠️  跳過 {config_name}: 配置文件不存在")
            return False

        try:
            # 載入配置
            data = self.load_json(config_path)

            # 檢查是否有 image-gen MCP
            if 'image-gen' not in data.get('mcpServers', {}):
                print(f"ℹ️  {config_name}: 無 image-gen MCP")
                return False

            image_gen = data['mcpServers']['image-gen']

            if 'args' not in image_gen:
                print(f"⚠️  {config_name}: image-gen 無 args 欄位")
                return False

            # 查找並轉換路徑
            updated = False
            for i, arg in enumerate(image_gen['args']):
                # 檢查是否是絕對路徑
                if isinstance(arg, str) and arg.startswith('/') and 'image-gen-mcp' in arg:
                    old_path = arg
                    # 轉換為相對路徑
                    new_path = './mcp-sources/image-gen-mcp'
                    image_gen['args'][i] = new_path
                    updated = True
                    print(f"   📝 {config_name}:")
                    print(f"      舊 (絕對): {old_path}")
                    print(f"      新 (相對): {new_path}")
                    break

            if not updated:
                # 檢查是否已經是相對路徑
                for arg in image_gen['args']:
                    if isinstance(arg, str) and arg.startswith('./') and 'image-gen-mcp' in arg:
                        print(f"✅ {config_name}: 已經使用相對路徑 ({arg})")
                        return False
                print(f"ℹ️  {config_name}: 未找到需要轉換的路徑")
                return False

            # 保存更新
            self.save_json(config_path, data)
            print(f"✅ {config_name}: 路徑已轉換為相對路徑")
            return True

        except Exception as e:
            print(f"❌ {config_name} 轉換失敗: {e}")
            return False

    def convert_all(self) -> dict:
        """轉換所有客戶端配置"""
        print("\n🔄 開始轉換 image-gen-mcp 路徑...")
        print("=" * 70)
        print("從: 絕對路徑 (/Users/.../SyncMCP/mcp-sources/image-gen-mcp)")
        print("到: 相對路徑 (./mcp-sources/image-gen-mcp)")
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

        # 2. 轉換路徑
        print("\n🔧 轉換路徑...")
        for name, config_path in self.configs.items():
            if self.convert_to_relative(name, config_path):
                results['success'].append(name)
            else:
                results['skipped'].append(name)

        # 3. 總結
        print("\n" + "=" * 70)
        print("✨ 路徑轉換完成!")
        print(f"📁 備份位置: {self.backup_dir}")

        print(f"\n📊 轉換結果:")
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
        """驗證轉換後的路徑"""
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
                        if isinstance(arg, str) and 'image-gen-mcp' in arg:
                            if arg.startswith('./'):
                                print(f"✅ {name}: {arg} (相對路徑)")
                            elif arg.startswith('/'):
                                print(f"⚠️  {name}: {arg} (仍是絕對路徑)")
                            else:
                                print(f"ℹ️  {name}: {arg}")
                            break
            except Exception as e:
                print(f"❌ {name}: 無法驗證 - {e}")

        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='將 image-gen-mcp 絕對路徑轉換為相對路徑',
        epilog='相對路徑更靈活，當目錄移動時不需要更新配置'
    )
    parser.add_argument('--yes', '-y', action='store_true', help='自動確認,不詢問')
    parser.add_argument('--verify-only', action='store_true', help='僅驗證路徑,不轉換')
    args = parser.parse_args()

    converter = PathConverter()

    if args.verify_only:
        converter.verify_paths()
        return

    print("\n📋 image-gen-mcp 路徑轉換工具")
    print("   - 將絕對路徑轉換為相對路徑")
    print("   - 自動備份所有配置")
    print("   - 支持所有 AI 客戶端")
    print("\n💡 為什麼使用相對路徑?")
    print("   - 更靈活: 當 SyncMCP 目錄移動時不需要更新")
    print("   - 更簡潔: 路徑更短更易讀")
    print("   - 更便攜: 適合不同機器間同步配置")

    if not args.yes:
        response = input("\n是否繼續轉換? (y/n): ").strip().lower()
        if response != 'y':
            print("取消操作")
            return

    # 執行轉換
    results = converter.convert_all()

    # 驗證
    converter.verify_paths()

    # 提示
    print("\n💡 重要提示:")
    print("   1. 相對路徑是相對於配置文件所在目錄")
    print("   2. 重啟 AI 客戶端以載入新配置")
    print("   3. 測試 image-gen 功能是否正常")
    print("\n📝 如需回復:")
    print(f"   從備份目錄恢復: {converter.backup_dir}")

    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
