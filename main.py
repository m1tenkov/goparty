import sys
import time

from vk_api.bot_longpoll import VkBotEventType

from bot_handlers import handle_message, handle_message_event
from bot_handlers import texts
from logger import bot_logger, log_action, log_error
from vk_bot import create_longpoll, vk

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

print(texts.MSG_CONSOLE_STARTED)
bot_logger.info("Bot started")


def process_event(event):
    started_at = time.perf_counter()
    event_name = str(event.type)
    vk_user_id = None
    try:
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            vk_user_id = message["from_id"]
            text = message.get("text", "")
            message_id = message.get("id")
            attachments = message.get("attachments", [])
            payload = message.get("payload")

            handle_message(vk, vk_user_id, text, attachments, message_id, payload)

        if event.type == VkBotEventType.MESSAGE_EVENT:
            vk_user_id = event.object.get("user_id") if isinstance(event.object, dict) else getattr(event.object, "user_id", None)
            handle_message_event(vk, event)
    except Exception as error:
        log_error("Event handler failed", event_type=event_name, vk_user_id=vk_user_id, error=str(error))
    finally:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        log_action("event_processed", event_type=event_name, vk_user_id=vk_user_id, duration_ms=duration_ms)
        if duration_ms >= 1500:
            bot_logger.warning("Slow event | %s", {"event_type": event_name, "vk_user_id": vk_user_id, "duration_ms": duration_ms})


while True:
    try:
        longpoll = create_longpoll()

        for event in longpoll.listen():
            process_event(event)
    except Exception as error:
        log_error("Long Poll reconnect after error", error=str(error))
        print(f"{texts.MSG_CONSOLE_LONGPOLL_RECONNECT}{error}")
        time.sleep(3)
