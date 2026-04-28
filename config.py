import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SECRETS_DIR = BASE_DIR / "secrets"
SECRETS_DIR.mkdir(exist_ok=True)


# Читает текстовый секрет из файла и возвращает None, если файла нет.
def _read_secret_file(path):
    secret_path = Path(path)
    if not secret_path.exists():
        return None
    return secret_path.read_text(encoding="utf-8").strip() or None


# Возвращает значение из env, затем из файла, затем использует значение по умолчанию.
def _env_or_file(env_name, file_path, default=None):
    return os.getenv(env_name) or _read_secret_file(file_path) or default


# Загружает JSON-файл с секретом в словарь или возвращает пустой словарь.
def _load_json_secret(path):
    secret_path = Path(path)
    if not secret_path.exists():
        return {}
    return json.loads(secret_path.read_text(encoding="utf-8"))


# Собирает конфиг базы данных из env, файла с секретом и значений по умолчанию.
def _build_db_config(file_name, defaults=None):
    defaults = defaults or {}
    file_values = _load_json_secret(SECRETS_DIR / file_name)
    return {
        "host": os.getenv("DB_HOST", file_values.get("host", defaults.get("host"))),
        "port": int(os.getenv("DB_PORT", file_values.get("port", defaults.get("port", 3306)))),
        "name": os.getenv("DB_NAME", file_values.get("name", defaults.get("name"))),
        "user": os.getenv("DB_USER", file_values.get("user", defaults.get("user"))),
        "password": os.getenv("DB_PASSWORD", file_values.get("password", defaults.get("password"))),
        "ssl_ca": Path(os.getenv("DB_SSL_CA", file_values.get("ssl_ca", defaults.get("ssl_ca", "")) or ""))
        if (os.getenv("DB_SSL_CA") or file_values.get("ssl_ca") or defaults.get("ssl_ca"))
        else None,
    }


TOKEN = _env_or_file("VK_BOT_TOKEN", SECRETS_DIR / "token.txt")
GROUP_ID = int(os.getenv("VK_GROUP_ID", "237423541"))
ENABLE_LIKE_NOTIFICATIONS = os.getenv("ENABLE_LIKE_NOTIFICATIONS", "true").strip().lower() in {"1", "true", "yes", "on"}
ENABLE_PROFILE_RESET_BUTTON = True

DB_CONFIG = _build_db_config(
    file_name="local_db.json",
    defaults={
        "host": "localhost",
        "port": 3306,
        "name": "goparty_bot",
        "user": "root",
        "password": "",
        "ssl_ca": None,
    },
)

DB_HOST = DB_CONFIG["host"]
DB_PORT = DB_CONFIG["port"]
DB_NAME = DB_CONFIG["name"]
DB_USER = DB_CONFIG["user"]
DB_PASSWORD = DB_CONFIG["password"]
DB_CA_PATH = DB_CONFIG["ssl_ca"]

if not TOKEN:
    raise RuntimeError("VK token not found. Set VK_BOT_TOKEN or put it into secrets/token.txt")
