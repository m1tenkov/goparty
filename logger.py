import json
import logging
from datetime import datetime, timezone
from pathlib import Path


LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

ACTIONS_LOG_PATH = LOGS_DIR / "actions.jsonl"
BOT_LOG_PATH = LOGS_DIR / "bot.log"


bot_logger = logging.getLogger("goparty_bot")
if not bot_logger.handlers:
    bot_logger.setLevel(logging.INFO)
    handler = logging.FileHandler(BOT_LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    bot_logger.addHandler(handler)
    bot_logger.propagate = False


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


def _sanitize(value):
    if isinstance(value, str):
        return value[:1000]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    return str(value)


def log_action(action, **fields):
    payload = {
        "time": _timestamp(),
        "action": action,
        **{key: _sanitize(value) for key, value in fields.items()},
    }
    with ACTIONS_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def log_error(message, **fields):
    if fields:
        bot_logger.error("%s | %s", message, json.dumps({k: _sanitize(v) for k, v in fields.items()}, ensure_ascii=False))
    else:
        bot_logger.error("%s", message)

