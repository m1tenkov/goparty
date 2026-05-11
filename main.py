import sys
import time

from bot_handlers import texts
from event_processing import process_event
from logger import bot_logger, log_action, log_error
from vk_bot import create_vk_transport

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

print(texts.MSG_CONSOLE_STARTED)
bot_logger.info("Bot started")


while True:
    try:
        vk_session, vk, longpoll = create_vk_transport()
        log_action("longpoll_connected")

        for event in longpoll.listen():
            process_event(vk, event)
    except Exception as error:
        log_error("Long Poll reconnect after error", error=str(error))
        print(f"{texts.MSG_CONSOLE_LONGPOLL_RECONNECT}{error}")
        time.sleep(3)
