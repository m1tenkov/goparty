import time
from types import SimpleNamespace

from bot_handlers import handle_message, handle_message_event
from logger import bot_logger, log_action, log_error


EVENT_MESSAGE_NEW = "message_new"
EVENT_MESSAGE_EVENT = "message_event"


def _build_callback_event(event_type, event_object):
    return SimpleNamespace(type=event_type, object=event_object)


def process_event(vk, event):
    started_at = time.perf_counter()
    event_name = str(getattr(event, "type", "unknown"))
    vk_user_id = None
    try:
        if event_name == EVENT_MESSAGE_NEW:
            message = getattr(getattr(event, "object", None), "message", None)
            if message is None and isinstance(getattr(event, "object", None), dict):
                message = event.object.get("message", {})
            message = message or {}
            vk_user_id = message.get("from_id")
            text = message.get("text", "")
            message_id = message.get("id")
            attachments = message.get("attachments", [])
            payload = message.get("payload")
            handle_message(vk, vk_user_id, text, attachments, message_id, payload)

        if event_name == EVENT_MESSAGE_EVENT:
            event_object = getattr(event, "object", None)
            if isinstance(event_object, dict):
                vk_user_id = event_object.get("user_id")
            else:
                vk_user_id = getattr(event_object, "user_id", None)
            handle_message_event(vk, event)
    except Exception as error:
        log_error("Event handler failed", event_type=event_name, vk_user_id=vk_user_id, error=str(error))
    finally:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        log_action("event_processed", event_type=event_name, vk_user_id=vk_user_id, duration_ms=duration_ms)
        if duration_ms >= 1500:
            bot_logger.warning("Slow event | %s", {"event_type": event_name, "vk_user_id": vk_user_id, "duration_ms": duration_ms})


def process_callback_payload(vk, payload):
    event_type = str(payload.get("type") or "")
    event_object = payload.get("object") or {}
    if event_type == EVENT_MESSAGE_NEW:
        callback_event = _build_callback_event(event_type, {"message": event_object.get("message", {})})
        process_event(vk, callback_event)
    elif event_type == EVENT_MESSAGE_EVENT:
        callback_event = _build_callback_event(event_type, event_object)
        process_event(vk, callback_event)
