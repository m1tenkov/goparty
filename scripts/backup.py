#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
SECRETS_DIR = BASE_DIR / "secrets"
DEFAULT_BACKUP_DIR = BASE_DIR / "backups"
DEFAULT_PHOTOS_DIR = BASE_DIR / "storage" / "photos"


def load_json_secret(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_db_config():
    file_values = load_json_secret(SECRETS_DIR / "local_db.json")
    return {
        "host": os.getenv("DB_HOST", file_values.get("host", "localhost")),
        "port": int(os.getenv("DB_PORT", file_values.get("port", 3306))),
        "name": os.getenv("DB_NAME", file_values.get("name", "goparty_bot")),
        "user": os.getenv("DB_USER", file_values.get("user", "root")),
        "password": os.getenv("DB_PASSWORD", file_values.get("password", "")),
        "ssl_ca": os.getenv("DB_SSL_CA", file_values.get("ssl_ca")),
    }


def require_mysqldump(executable):
    resolved = shutil.which(executable)
    if resolved is None:
        raise RuntimeError(
            f"Could not find {executable!r}. Install MySQL client tools or set MYSQLDUMP_BIN."
        )
    return resolved


def dump_database(mysqldump_bin, db_config, output_path):
    command = [
        mysqldump_bin,
        f"--host={db_config['host']}",
        f"--port={db_config['port']}",
        f"--user={db_config['user']}",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--events",
        "--default-character-set=utf8mb4",
    ]
    if db_config.get("ssl_ca"):
        command.append(f"--ssl-ca={db_config['ssl_ca']}")
    command.append(db_config["name"])

    env = os.environ.copy()
    if db_config.get("password"):
        env["MYSQL_PWD"] = db_config["password"]

    with output_path.open("wb") as dump_file:
        result = subprocess.run(command, stdout=dump_file, stderr=subprocess.PIPE, env=env)

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"mysqldump failed: {stderr}")


def add_directory_to_zip(archive, source_dir, archive_prefix):
    if not source_dir.exists():
        return 0

    file_count = 0
    for path in source_dir.rglob("*"):
        if path.is_file():
            archive.write(path, Path(archive_prefix) / path.relative_to(source_dir))
            file_count += 1
    return file_count


def prune_old_backups(backup_dir, keep):
    if keep <= 0:
        return []

    backups = sorted(
        backup_dir.glob("goparty_backup_*.zip"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    removed = []
    for old_backup in backups[keep:]:
        old_backup.unlink()
        removed.append(old_backup)
    return removed


def create_backup(args):
    db_config = build_db_config()
    mysqldump_bin = require_mysqldump(args.mysqldump_bin)
    backup_dir = args.output_dir.resolve()
    photos_dir = args.photos_dir.resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_path = backup_dir / f"goparty_backup_{timestamp}.zip"

    with tempfile.TemporaryDirectory(prefix="goparty_backup_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        dump_path = temp_dir / "database.sql"
        dump_database(mysqldump_bin, db_config, dump_path)

        manifest = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "database": {
                "host": db_config["host"],
                "port": db_config["port"],
                "name": db_config["name"],
                "user": db_config["user"],
            },
            "photos_dir": str(photos_dir),
        }

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(dump_path, "database.sql")
            photo_count = add_directory_to_zip(archive, photos_dir, "storage/photos")
            manifest["photo_files"] = photo_count
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    removed = prune_old_backups(backup_dir, args.keep)
    return archive_path, removed


def parse_args():
    parser = argparse.ArgumentParser(description="Create a GoParty bot backup archive.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.getenv("BACKUP_DIR", DEFAULT_BACKUP_DIR)),
        help="Directory where backup archives are stored.",
    )
    parser.add_argument(
        "--photos-dir",
        type=Path,
        default=Path(os.getenv("PHOTO_STORAGE_DIR", DEFAULT_PHOTOS_DIR)),
        help="Directory with local user photos.",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=int(os.getenv("BACKUP_KEEP", "14")),
        help="How many newest backup archives to keep. Use 0 to disable pruning.",
    )
    parser.add_argument(
        "--mysqldump-bin",
        default=os.getenv("MYSQLDUMP_BIN", "mysqldump"),
        help="mysqldump executable name or absolute path.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        archive_path, removed = create_backup(args)
    except Exception as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1

    print(f"Backup created: {archive_path}")
    if removed:
        print(f"Removed old backups: {len(removed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
