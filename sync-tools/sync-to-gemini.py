#!/usr/bin/env python3
"""
同步 MCP 配置到 Gemini CLI
從 Claude Code 讀取 MCP 配置並同步到 Gemini CLI
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil

class GeminiMCPSync:
    def __init__(self):
        self.home = Path.home()
        self.claude_config = self.home / '.claude.json'
        self.gemini_config = self.home / '.gemini/settings.json'

        # 備份目錄設置為項目內的 backup/
        script_dir = Path(__file__).resolve().parent.parent
        self.backup_dir = script_dir / 'backup'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_config(self, config_path: Path, name: str) -> Path:
        """備份配置文件"""
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{name}_gemini_sync_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(config_path, backup_path)
        print(f"✅ 已備份 {name} -> {backup_path.name}")
        return backup_path

    def load_json(self, path: Path) -> dict:
        """載入 JSON 配置"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_json(self, path: Path, data: dict):
        """保存 JSON 配置"""
        # 原子寫入
        temp_path = path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(path)

    def normalize_mcp_config(self, name: str, config: dict) -> dict:
        """標準化 MCP 配置為 Gemini CLI 格式"""
        normalized = config.copy()

        # Gemini CLI 支援 stdio 和 streamable-http
        # HTTP MCP 需要轉換為 streamable-http
        if normalized.get('type') == 'http':
            normalized['type'] = 'streamable-http'

        return normalized

    def sync(self) -> bool:
        """執行同步"""
        print("\n🔄 開始同步 MCP 配置到 Gemini CLI...")
        print("=" * 60)

        try:
            # 1. 備份
            print("\n📦 備份現有配置...")
            self.backup_config(self.claude_config, "claude-code")
            self.backup_config(self.gemini_config, "gemini-cli")

            # 2. 載入配置
            print("\n📥 載入配置...")
            claude_data = self.load_json(self.claude_config)
            gemini_data = self.load_json(self.gemini_config)

            claude_mcps = claude_data.get('mcpServers', {})
            print(f"   ✅ Claude Code: {len(claude_mcps)} 個 MCP 伺服器")

            # 3. 處理每個 MCP
            print("\n🔧 處理 MCP 配置...")
            new_mcps = {}
            skipped = []

            for name, config in claude_mcps.items():
                normalized = self.normalize_mcp_config(name, config)

                # 檢查是否有無效配置
                if not normalized.get('command') and not normalized.get('url'):
                    print(f"   ⚠️  跳過 {name}: 缺少 command 或 url")
                    skipped.append(name)
                    continue

                new_mcps[name] = normalized
                print(f"   ✅ {name}")

            # 4. 更新 Gemini 配置
            print("\n💾 更新 Gemini CLI 配置...")
            gemini_data['mcpServers'] = new_mcps
            self.save_json(self.gemini_config, gemini_data)
            print(f"✅ 已更新: {self.gemini_config}")

            # 5. 總結
            print("\n" + "=" * 60)
            print("✨ 同步完成!")
            print(f"📁 備份位置: {self.backup_dir}")
            print(f"\n📊 同步結果:")
            print(f"   - 成功同步: {len(new_mcps)} 個 MCP")
            if skipped:
                print(f"   - 跳過: {', '.join(skipped)}")

            print(f"\n📱 Gemini CLI MCP 列表:")
            for i, name in enumerate(sorted(new_mcps.keys()), 1):
                print(f"   {i}. {name}")

            print("\n💡 提示:")
            print("   - 重啟 Gemini CLI 以載入新配置")
            print("   - 執行 'gemini mcp list' 查看 MCP 狀態")

            return True

        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description='同步 MCP 配置到 Gemini CLI')
    parser.add_argument('--yes', '-y', action='store_true', help='自動確認,不詢問')
    args = parser.parse_args()

    syncer = GeminiMCPSync()

    print("\n📋 Gemini CLI MCP 同步工具")
    print("   - 從 Claude Code 複製 MCP 配置到 Gemini CLI")
    print("   - 自動備份現有配置")
    print("   - 處理格式差異")

    if not args.yes:
        response = input("\n是否繼續? (y/n): ").strip().lower()
        if response != 'y':
            print("取消操作")
            return

    success = syncer.sync()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
