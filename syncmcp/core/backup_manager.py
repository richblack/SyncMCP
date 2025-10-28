"""
備份管理器 - 管理配置備份和恢復
"""

import json
import shutil
from datetime import datetime
from pathlib import Path


class BackupManager:
    """備份管理器"""

    def __init__(self, backup_dir: Path = None):
        self.backup_dir = backup_dir or Path.home() / ".syncmcp/backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, configs: dict[str, "ClientConfig"]) -> str:
        """創建備份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir()

        # 保存所有配置
        for client_name, config in configs.items():
            if config.file_path.exists():
                dest = backup_path / f"{client_name}.json"
                shutil.copy2(config.file_path, dest)

        # 保存 metadata
        metadata = {"id": backup_id, "timestamp": timestamp, "clients": list(configs.keys())}
        with open(backup_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return backup_id

    def restore(self, backup_id: str, adapters: dict):
        """從備份恢復"""
        backup_path = self.backup_dir / backup_id
        if not backup_path.exists():
            raise ValueError(f"備份不存在: {backup_id}")

        # 載入 metadata
        with open(backup_path / "metadata.json", encoding="utf-8") as f:
            metadata = json.load(f)

        # 恢復每個客戶端
        for client_name in metadata["clients"]:
            backup_file = backup_path / f"{client_name}.json"
            if backup_file.exists() and client_name in adapters:
                target_path = adapters[client_name].get_config_path()
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, target_path)

    def list_backups(self) -> list[dict]:
        """列出所有備份"""
        backups = []
        for backup_path in sorted(self.backup_dir.iterdir(), reverse=True):
            if backup_path.is_dir():
                metadata_file = backup_path / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, encoding="utf-8") as f:
                        backups.append(json.load(f))
        return backups

    def cleanup_old_backups(self, keep: int = 10):
        """清理舊備份，保留最近的 N 個"""
        backups = self.list_backups()
        if len(backups) <= keep:
            return

        for backup in backups[keep:]:
            backup_path = self.backup_dir / backup["id"]
            shutil.rmtree(backup_path)
