import time

import unicodedata

from config import ENABLE_LIKE_NOTIFICATIONS, ENABLE_PROFILE_RESET_BUTTON
from database import (
    GAME_CODES,
    delete_user_data,
    enqueue_pending_like,
    get_profile_by_vk_user_id,
    is_profile_banned,
    is_bot_vk_user_id,
    mark_profile_delivery_unavailable,
    mark_pending_like_notified,
    record_interaction,
    reset_profile_delivery_status,
    resolve_pending_like,
)
from logger import log_action
from . import texts
from .text_formatters import (
    format_done_message,
    format_like_notification,
    format_match_message,
    format_report_message,
)

from .constants import (
    ACTION_DEBOUNCE_SECONDS,
    ABOUT_MAX_LENGTH,
    GENDER_LABELS,
    LIKE_MESSAGE_MAX_LENGTH,
    NO_GAMES_TEXT,
    REPORT_REASON_MAX_LENGTH,
    STATE_ABOUT,
    STATE_BROWSE,
    STATE_DEACTIVATE_CONFIRM,
    STATE_EDIT_MENU,
    STATE_GAMES,
    STATE_INCOMING_LIKE,
    STATE_LIKE_MESSAGE,
    STATE_PHOTO,
    STATE_PHOTO_APPEND,
    STATE_PHOTO_MORE,
    STATE_RESET_CONFIRM,
    STATE_REPORT_REASON,
    STATE_REG_AGE,
    STATE_REG_CITY,
    STATE_REG_GENDER,
    STATE_REG_LOOKING,
    STATE_REG_NAME,
    STATE_REVIEW,
    users,
)
from .keyboards import (
    EMPTY_KEYBOARD,
    get_age_registration_keyboard,
    get_browse_keyboard,
    get_city_edit_keyboard,
    get_deactivate_confirm_keyboard,
    get_edit_profile_keyboard,
    get_games_keyboard,
    get_gender_edit_keyboard,
    get_incoming_like_keyboard,
    get_keep_current_keyboard,
    get_like_message_keyboard,
    get_looking_keyboard,
    get_matches_keyboard,
    get_name_edit_keyboard,
    get_photo_edit_keyboard,
    get_photo_more_keyboard,
    get_report_cancel_keyboard,
    get_reset_confirm_keyboard,
    get_review_keyboard,
    get_age_edit_keyboard,
)
from .utils import (
    ask_next_required_field,
    apply_vk_defaults,
    build_photo_attachment,
    ensure_runtime_user,
    event_value,
    extract_photo_payload,
    extract_photo_attachments_from_message,
    fit_message_text,
    format_games_picker_prompt,
    format_games_summary,
    format_photo_more_prompt,
    format_profile,
    games_display,
    get_pending_like_profile,
    has_pending_likes,
    parse_payload,
    reactivate_profile_if_needed,
    save_games_state,
    save_photos_state,
    save_text_field,
    persist_runtime_user,
    show_current_or_next_candidate,
    show_next_candidate,
    show_previous_candidate,
    show_review,
    show_games_picker,
    start_games_flow,
    sync_profile_from_db,
    is_profile_complete,
)


# Укорачивает текст сообщения перед записью в логи.
def _preview_text(text, limit=300):
    text = (text or "").strip()
    return text[:limit]


# Удаляет невидимые управляющие символы из текста, который показывается пользователю.
def _clean_visible_text(text):
    text = str(text or "")
    cleaned = []
    for char in text:
        category = unicodedata.category(char)
        if category in {"Cf", "Cc", "Cs"} and char not in {"\n", "\r", "\t"}:
            continue
        cleaned.append(char)
    return "".join(cleaned).strip()


def _handle_banned_user(user, send):
    if user is not None:
        user["step"] = None
        user["current_candidate"] = None
        user["pending_like_profile"] = None
        user["like_message_target_vk_user_id"] = None
        user["like_message_resume_step"] = None
        user["report_target_vk_user_id"] = None
        user["report_resume_step"] = None
        user["resume_step"] = None
    send(texts.MSG_BANNED, keyboard=EMPTY_KEYBOARD)


# Защищает от случайной двойной обработки одного и того же действия пользователя.
def is_duplicate_action(user, action_key, window_seconds=ACTION_DEBOUNCE_SECONDS):
    now = time.monotonic()
    last_key = user.get("_last_action_key")
    last_at = user.get("_last_action_at", 0)
    if last_key == action_key and now - last_at < window_seconds:
        log_action(
            "duplicate_action_ignored",
            vk_user_id=user.get("vk_user_id"),
            step=user.get("step"),
            action_key=action_key,
        )
        return True

    user["_last_action_key"] = action_key
    user["_last_action_at"] = now
    return False


DELIVERY_UNAVAILABLE_ERROR_CODES = {"18", "900", "901"}


# Извлекает код ошибки VK API из исключения или его текстового представления.
def _extract_vk_error_code(error):
    code = getattr(error, "code", None)
    if code is not None:
        return str(code)

    text = str(error or "")
    if text.startswith("[") and "]" in text:
        return text[1:text.index("]")]
    return None


# Определяет, означает ли ошибка отправки VK, что пользователю нельзя доставить сообщение.
def _is_delivery_unavailable_error(error):
    code = _extract_vk_error_code(error)
    if code in DELIVERY_UNAVAILABLE_ERROR_CODES:
        return True

    text = str(error or "").lower()
    markers = (
        "can't send messages",
        "without permission",
        "privacy settings",
        "deleted or banned",
    )
    return any(marker in text for marker in markers)


# Безопасно отправляет сообщение VK и при необходимости помечает профиль как недоступный для доставки.
def safe_vk_send(vk, **kwargs):
    try:
        vk.messages.send(**kwargs)
        return True
    except Exception as error:
        recipient = kwargs.get("user_id") or kwargs.get("peer_id")
        error_code = _extract_vk_error_code(error)
        log_action(
            "vk_send_failed",
            recipient=recipient,
            error_code=error_code,
            error=str(error),
        )
        direct_user_id = kwargs.get("user_id")
        if direct_user_id and not is_bot_vk_user_id(direct_user_id) and _is_delivery_unavailable_error(error):
            mark_profile_delivery_unavailable(direct_user_id, error_code=error_code)
        return False


# Безопасно редактирует сообщение VK и логирует любые ошибки.
def safe_vk_edit(vk, **kwargs):
    try:
        vk.messages.edit(**kwargs)
        return True
    except Exception as error:
        log_action(
            "vk_edit_failed",
            peer_id=kwargs.get("peer_id"),
            error=str(error),
        )
        return False


# Безопасно отвечает на callback-событие VK, чтобы клиент перестал ждать.
def safe_vk_answer_event(vk, **kwargs):
    try:
        vk.messages.sendMessageEventAnswer(**kwargs)
        return True
    except Exception as error:
        log_action(
            "vk_event_answer_failed",
            peer_id=kwargs.get("peer_id"),
            user_id=kwargs.get("user_id"),
            error=str(error),
        )
        return False

# Переводит пользователя в состояние входящего лайка с указанным профилем лайкнувшего.
def activate_incoming_like(user, liker_profile, preserve_step=True):
    if not liker_profile:
        return False

    if preserve_step and user.get("step") != STATE_INCOMING_LIKE:
        user["resume_step"] = user.get("step")
    user["pending_like_profile"] = liker_profile
    user["step"] = STATE_INCOMING_LIKE
    return True


# Показывает экран входящего лайка для конкретного профиля.
def show_pending_like(user, liker_profile, send, preserve_step=True):
    if not activate_incoming_like(user, liker_profile, preserve_step=preserve_step):
        return False
    repeat_incoming_like_prompt(user, send)
    return True


# Загружает и показывает следующий необработанный входящий лайк, если он есть.
def show_next_pending_like_if_any(user, send):
    next_profile = get_pending_like_profile(user["vk_user_id"])
    if next_profile:
        return show_pending_like(user, next_profile, send, preserve_step=False)
    return False


# Возвращает пользователя в предыдущий сценарий после завершения обработки входящего лайка.
def resume_after_incoming_like(user, send):
    user["pending_like_profile"] = None
    previous_step = user.get("resume_step")
    suppress_post_match_prompt = user.get("suppress_post_match_prompt", False)
    user["suppress_post_match_prompt"] = False
    user["resume_step"] = None

    if show_next_pending_like_if_any(user, send):
        return

    if previous_step == STATE_BROWSE:
        show_current_or_next_candidate(user["vk_user_id"], send)
        return

    user["step"] = STATE_BROWSE
    return


# Возвращает профиль, который сейчас актуален для лайка, жалобы или сообщения.
def get_active_profile_for_feedback(user):
    if user.get("step") == STATE_INCOMING_LIKE and user.get("pending_like_profile"):
        return user.get("pending_like_profile")

    candidate_vk_user_id = user.get("current_candidate")
    if not candidate_vk_user_id:
        return None
    return get_profile_by_vk_user_id(candidate_vk_user_id)


# Запускает сценарий, в котором пользователь может добавить сообщение к лайку.
def start_like_message_flow(user, send):
    target_profile = get_active_profile_for_feedback(user)
    if not target_profile:
        send(texts.MSG_NO_PROFILES, keyboard=get_matches_keyboard())
        return

    user["like_message_target_vk_user_id"] = target_profile["vk_user_id"]
    user["like_message_resume_step"] = user.get("step")
    user["step"] = STATE_LIKE_MESSAGE
    send(texts.MSG_SEND_MESSAGE_PROMPT, keyboard=get_like_message_keyboard())


# Возвращает пользователя из сценария лайка с сообщением обратно в предыдущий сценарий.
def resume_after_like_message(user, send):
    previous_step = user.get("like_message_resume_step")
    user["like_message_resume_step"] = None
    user["like_message_target_vk_user_id"] = None

    if previous_step == STATE_INCOMING_LIKE:
        repeat_incoming_like_prompt(user, send)
        return
    if previous_step == STATE_BROWSE:
        show_current_or_next_candidate(user["vk_user_id"], send)
        return
    show_review(user, send)


# Отправляет пользователю уведомление о лайке с превью профиля лайкнувшего.
def send_like_notification(vk, target_vk_user_id, liker_profile):
    if is_bot_vk_user_id(target_vk_user_id):
        return
    target_user = ensure_runtime_user(vk, target_vk_user_id)
    activate_incoming_like(target_user, liker_profile, preserve_step=True)

    target_profile = get_profile_by_vk_user_id(target_vk_user_id) or {}
    target_name = target_profile.get("name") or texts.LABEL_MY_PROFILE_FALLBACK
    message = format_like_notification(
        target_name,
        format_profile(liker_profile, include_review=False),
        like_message=liker_profile.get("like_message"),
    )
    if safe_vk_send(
        vk,
        user_id=target_vk_user_id,
        message=fit_message_text(message),
        random_id=0,
        keyboard=get_incoming_like_keyboard(),
        attachment=build_photo_attachment(liker_profile),
    ):
        mark_pending_like_notified(target_vk_user_id, liker_profile["vk_user_id"])


# Отправляет уведомление о взаимном мэтче одной из сторон.
def send_match_notification(vk, recipient_vk_user_id, other_profile, like_message=None):
    if is_bot_vk_user_id(recipient_vk_user_id):
        return
    other_name = other_profile.get("name") or texts.LABEL_THIS_PERSON
    other_vk_user_id = other_profile.get("vk_user_id")
    vk_link = texts.LABEL_TEST_BOT if is_bot_vk_user_id(other_vk_user_id) else f"https://vk.com/id{other_vk_user_id}"
    message = format_match_message(
        format_profile(other_profile, include_review=False),
        other_name,
        vk_link,
        like_message=like_message,
    )
    safe_vk_send(
        vk,
        user_id=recipient_vk_user_id,
        message=fit_message_text(message),
        random_id=0,
        keyboard=get_matches_keyboard(),
        attachment=build_photo_attachment(other_profile),
    )


# Повторно показывает текущую подсказку о входящем лайке.
def repeat_incoming_like_prompt(user, send):
    liker_profile = user.get("pending_like_profile") or {}
    target_name = user.get("name") or texts.LABEL_MY_PROFILE_FALLBACK
    message = format_like_notification(
        target_name,
        format_profile(liker_profile, include_review=False),
        like_message=liker_profile.get("like_message"),
    )
    send(
        message,
        keyboard=get_incoming_like_keyboard(),
        attachment=build_photo_attachment(liker_profile),
    )


# Отправляет готовую жалобу на анкету в чат модерации.
def send_report_to_moderation(vk, reporter_user, candidate_profile, reason_text):
    report_chat_peer_id = 2000000001
    reporter_name = reporter_user.get("name") or f"VK {reporter_user['vk_user_id']}"
    reported_name = candidate_profile.get("name") or texts.LABEL_NO_NAME
    reporter_link = f"https://vk.com/gim237423541/convo/{reporter_user['vk_user_id']}"
    reported_link = f"https://vk.com/gim237423541/convo/{candidate_profile['vk_user_id']}"

    safe_vk_send(
        vk,
        peer_id=report_chat_peer_id,
        message=fit_message_text(
            format_report_message(
                format_profile(candidate_profile, include_review=False),
                reporter_name,
                reporter_link,
                reported_name,
                reported_link,
                reason_text,
            )
        ),
        random_id=0,
        attachment=build_photo_attachment(candidate_profile),
    )


# Запускает сценарий жалобы для текущего активного профиля.
def start_report_flow(user, send):
    target_profile = get_active_profile_for_feedback(user)
    if not target_profile:
        send(texts.MSG_NO_PROFILES, keyboard=get_matches_keyboard())
        return
    user["report_target_vk_user_id"] = target_profile["vk_user_id"]
    user["report_resume_step"] = user.get("step")
    user["step"] = STATE_REPORT_REASON
    send(texts.MSG_REPORT_REASON_PROMPT, keyboard=get_report_cancel_keyboard())


# Обрабатывает текст причины, который пользователь ввел в сценарии жалобы.
def handle_report_reason(vk, user, raw_text, attachments, send):
    normalized_text = raw_text.strip().lower()
    if normalized_text == texts.BUTTON_CANCEL_REPORT.lower():
        previous_step = user.get("report_resume_step")
        user["report_resume_step"] = None
        user["report_target_vk_user_id"] = None
        user["step"] = previous_step or STATE_BROWSE
        if user["step"] == STATE_INCOMING_LIKE:
            repeat_incoming_like_prompt(user, send)
            return
        show_current_or_next_candidate(user["vk_user_id"], send)
        return

    candidate_vk_user_id = user.get("report_target_vk_user_id")
    if not candidate_vk_user_id:
        user["step"] = STATE_BROWSE
        send(texts.MSG_NO_PROFILES, keyboard=get_matches_keyboard())
        return

    reason_text = raw_text.strip()
    if attachments or not reason_text or len(reason_text) > REPORT_REASON_MAX_LENGTH:
        send(texts.MSG_TEXT_500_ONLY, keyboard=get_report_cancel_keyboard())
        return

    candidate = get_profile_by_vk_user_id(candidate_vk_user_id)
    if not candidate or not candidate.get("is_active") or candidate.get("delivery_disabled"):
        user["step"] = STATE_BROWSE
        user["current_candidate"] = None
        show_next_candidate(user["vk_user_id"], send)
        return

    send_report_to_moderation(vk, user, candidate, reason_text)
    log_action("interaction_attempt", vk_user_id=user["vk_user_id"], target_vk_user_id=candidate["vk_user_id"], interaction_type="report_dislike")
    record_interaction(user["vk_user_id"], candidate["vk_user_id"], "dislike")
    resolve_pending_like(user["vk_user_id"], candidate["vk_user_id"], "dislike")
    log_action("interaction_saved", vk_user_id=user["vk_user_id"], target_vk_user_id=candidate["vk_user_id"], interaction_type="report_dislike")
    user["step"] = STATE_BROWSE
    user["report_resume_step"] = None
    user["report_target_vk_user_id"] = None
    user["current_candidate"] = None
    send(texts.MSG_REPORT_SENT, keyboard=get_matches_keyboard())
    show_next_candidate(user["vk_user_id"], send)


# Обрабатывает текст пользователя, когда он отправляет лайк вместе с сообщением.
def handle_like_message_input(vk, user, raw_text, attachments, send):
    normalized_text = raw_text.strip().lower()
    if normalized_text == texts.BUTTON_BACK_FROM_MESSAGE.lower():
        user["step"] = user.get("like_message_resume_step") or STATE_BROWSE
        resume_after_like_message(user, send)
        return

    message_text = raw_text.strip()
    if attachments or not message_text or len(message_text) > LIKE_MESSAGE_MAX_LENGTH:
        send(texts.MSG_TEXT_500_ONLY, keyboard=get_like_message_keyboard())
        return

    target_vk_user_id = user.get("like_message_target_vk_user_id")
    if not target_vk_user_id:
        user["step"] = STATE_BROWSE
        send(texts.MSG_NO_PROFILES, keyboard=get_matches_keyboard())
        return

    target_profile = get_profile_by_vk_user_id(target_vk_user_id)
    if not target_profile or not target_profile.get("is_active") or target_profile.get("delivery_disabled"):
        user["step"] = STATE_BROWSE
        user["current_candidate"] = None
        if user.get("browse_mode") == "history":
            user["browse_mode"] = "new"
            user["history_candidate_action"] = None
            user["history_cursor_id"] = None
            user["history_cursor_created_at"] = None
        resume_after_like_message(user, send)
        return
    if is_profile_banned(user["vk_user_id"]):
        user["current_candidate"] = None
        resume_after_like_message(user, send)
        return

    log_action("interaction_attempt", vk_user_id=user["vk_user_id"], target_vk_user_id=target_vk_user_id, interaction_type="like_message")
    result = record_interaction(user["vk_user_id"], target_vk_user_id, "like")
    if result.get("blocked_by_ban"):
        user["current_candidate"] = None
        resume_after_like_message(user, send)
        return
    resolve_pending_like(user["vk_user_id"], target_vk_user_id, "like")
    log_action("interaction_saved", vk_user_id=user["vk_user_id"], target_vk_user_id=target_vk_user_id, interaction_type="like_message", matched=result.get("matched"))

    liker_profile = get_profile_by_vk_user_id(user["vk_user_id"]) or user
    liker_profile["like_message"] = message_text

    if result["matched"]:
        match = result.get("target_profile") or target_profile
        send_match_notification(vk, user["vk_user_id"], match)
        send_match_notification(vk, target_vk_user_id, get_profile_by_vk_user_id(user["vk_user_id"]) or user, like_message=message_text)
        if user.get("like_message_resume_step") == STATE_INCOMING_LIKE:
            user["pending_like_profile"] = None
            user["resume_step"] = None
            user["suppress_post_match_prompt"] = True
            user["step"] = STATE_INCOMING_LIKE
            resume_after_incoming_like(user, send)
            return
        user["current_candidate"] = None
        resume_after_like_message(user, send)
        return

    if enqueue_pending_like(user["vk_user_id"], target_vk_user_id, message_text):
        if ENABLE_LIKE_NOTIFICATIONS:
            send_like_notification(vk, target_vk_user_id, liker_profile)

    user["current_candidate"] = None
    if user.get("browse_mode") == "history":
        user["browse_mode"] = "new"
        user["history_candidate_action"] = None
        user["history_cursor_id"] = None
        user["history_cursor_created_at"] = None
    resume_after_like_message(user, send)


# Обрабатывает ответ пользователя на входящий лайк.
def handle_incoming_like(vk, user, normalized_text, send):
    liker_profile = user.get("pending_like_profile")
    if not liker_profile:
        if show_next_pending_like_if_any(user, send):
            return
        resume_after_incoming_like(user, send)
        return

    if normalized_text == texts.EMOJI_LIKE:
        if is_duplicate_action(user, f"incoming:like:{liker_profile['vk_user_id']}"):
            return
        log_action("interaction_attempt", vk_user_id=user["vk_user_id"], target_vk_user_id=liker_profile["vk_user_id"], interaction_type="like")
        result = record_interaction(user["vk_user_id"], liker_profile["vk_user_id"], "like")
        resolve_pending_like(user["vk_user_id"], liker_profile["vk_user_id"], "like")
        log_action("interaction_saved", vk_user_id=user["vk_user_id"], target_vk_user_id=liker_profile["vk_user_id"], interaction_type="like", matched=result.get("matched"))
        if result["matched"]:
            match = result.get("target_profile") or liker_profile
            send_match_notification(vk, user["vk_user_id"], match)
            send_match_notification(vk, liker_profile["vk_user_id"], get_profile_by_vk_user_id(user["vk_user_id"]) or user)
            user["pending_like_profile"] = None
            user["current_candidate"] = None
            user["suppress_post_match_prompt"] = True
            user["step"] = STATE_INCOMING_LIKE
            resume_after_incoming_like(user, send)
            return
        resume_after_incoming_like(user, send)
        return

    if normalized_text == texts.EMOJI_MESSAGE:
        if is_duplicate_action(user, f"incoming:like_message:{liker_profile['vk_user_id']}"):
            return
        start_like_message_flow(user, send)
        return

    if normalized_text == texts.BUTTON_REPORT.lower():
        if is_duplicate_action(user, f"incoming:report:{liker_profile['vk_user_id']}"):
            return
        start_report_flow(user, send)
        return

    if normalized_text == texts.EMOJI_DISLIKE:
        if is_duplicate_action(user, f"incoming:dislike:{liker_profile['vk_user_id']}"):
            return
        log_action("interaction_attempt", vk_user_id=user["vk_user_id"], target_vk_user_id=liker_profile["vk_user_id"], interaction_type="dislike")
        record_interaction(user["vk_user_id"], liker_profile["vk_user_id"], "dislike")
        resolve_pending_like(user["vk_user_id"], liker_profile["vk_user_id"], "dislike")
        log_action("interaction_saved", vk_user_id=user["vk_user_id"], target_vk_user_id=liker_profile["vk_user_id"], interaction_type="dislike")
        resume_after_incoming_like(user, send)
        return

    repeat_incoming_like_prompt(user, send)

# Инициализирует или восстанавливает сценарий пользователя при начале диалога с ботом.
def start_bot_flow(vk, vk_user_id, send):
    existed_before = get_profile_by_vk_user_id(vk_user_id) is not None
    user = ensure_runtime_user(vk, vk_user_id)
    if user.get("is_banned"):
        _handle_banned_user(user, send)
        return
    apply_vk_defaults(vk_user_id, user)
    user = sync_profile_from_db(vk, vk_user_id)
    if user.get("is_banned"):
        _handle_banned_user(user, send)
        return

    if existed_before:
        send(texts.MSG_RETURNING)
        if is_profile_complete(user):
            if has_pending_likes(vk_user_id) and show_next_pending_like_if_any(user, send):
                return
            show_review(user, send)
            return

    if ask_next_required_field(user, send):
        return
    if has_pending_likes(vk_user_id) and show_next_pending_like_if_any(user, send):
        return
    show_review(user, send)


# Отправляет в VK подтверждение callback-события.
def answer_event(vk, event):
    obj = event.object
    safe_vk_answer_event(
        vk,
        event_id=event_value(obj, "event_id"),
        user_id=event_value(obj, "user_id"),
        peer_id=event_value(obj, "peer_id"),
    )


# Обновляет текст inline-сообщения и клавиатуру после callback-действия.
def edit_event_message(vk, event, text, keyboard):
    obj = event.object
    safe_vk_edit(
        vk,
        peer_id=event_value(obj, "peer_id"),
        conversation_message_id=event_value(obj, "conversation_message_id"),
        message=text,
        keyboard=keyboard,
    )


# Обрабатывает callback-события VK, в основном для inline-выбора игр.
def handle_message_event(vk, event):
    payload = parse_payload(event_value(event.object, "payload"))
    vk_user_id = event_value(event.object, "user_id")
    before_user = users.get(vk_user_id, {})
    log_action(
        "callback_event",
        vk_user_id=vk_user_id,
        step_before=before_user.get("step"),
        payload=payload,
    )
    should_persist = True
    try:
        user = users.get(vk_user_id) or ensure_runtime_user(vk, vk_user_id)
        reset_profile_delivery_status(vk_user_id)
        if user.get("is_banned"):
            answer_event(vk, event)
            safe_vk_send(
                vk,
                user_id=vk_user_id,
                message=fit_message_text(texts.MSG_BANNED),
                random_id=0,
                keyboard=EMPTY_KEYBOARD,
            )
            return
        cmd = payload.get("cmd")
        if user.get("step") == STATE_GAMES:
            if cmd == "toggle_game":
                should_persist = False
                field = payload.get("field")
                if field in GAME_CODES:
                    user[field] = 0 if user.get(field) else 1
                    edit_event_message(
                        vk,
                        event,
                        format_games_picker_prompt(),
                        get_games_keyboard(user),
                    )
                answer_event(vk, event)
                return
            if cmd == "games_done":
                if is_duplicate_action(user, "games:done"):
                    answer_event(vk, event)
                    return
                user["step"] = None
                user["games_step_completed"] = True
                save_games_state(user)
                edit_event_message(vk, event, format_games_summary(user), EMPTY_KEYBOARD)
                answer_event(vk, event)

                def send(message, keyboard=None, attachment=None):
                    safe_vk_send(
                        vk,
                        user_id=vk_user_id,
                        message=fit_message_text(message),
                        random_id=0,
                        keyboard=keyboard or EMPTY_KEYBOARD,
                        attachment=attachment,
                    )

                if ask_next_required_field(user, send):
                    return
                show_review(user, send)
                return
        answer_event(vk, event)
    finally:
        final_user = users.get(vk_user_id, {})
        if should_persist:
            persist_runtime_user(vk_user_id)
        log_action(
            "state_after_callback",
            vk_user_id=vk_user_id,
            step_after=final_user.get("step"),
            current_candidate=final_user.get("current_candidate"),
        )


# Проверяет и сохраняет имя пользователя при регистрации или редактировании.
def handle_reg_name(user, raw_text, normalized_text, send):
    vk_name = (user.get("vk_profile") or {}).get("name")
    if normalized_text == texts.BUTTON_KEEP_CURRENT.lower():
        show_review(user, send)
        return
    cleaned_raw_text = _clean_visible_text(raw_text)
    cleaned_vk_name = _clean_visible_text(vk_name)
    if cleaned_vk_name and cleaned_raw_text == cleaned_vk_name:
        save_text_field(user, "name", vk_name)
    else:
        candidate = cleaned_raw_text
        if not candidate or len(candidate) > 50:
            send(
                texts.MSG_INVALID_NAME,
                keyboard=get_name_edit_keyboard(vk_name),
            )
            return
        save_text_field(user, "name", candidate)
    if ask_next_required_field(user, send):
        return
    show_review(user, send)


# Проверяет и сохраняет возраст пользователя при регистрации или редактировании.
def handle_reg_age(user, normalized_text, send):
    vk_age = (user.get("vk_profile") or {}).get("age")
    if vk_age and normalized_text == str(vk_age):
        save_text_field(user, "age", vk_age)
    else:
        if not normalized_text.isdigit():
            send(texts.MSG_AGE_NUMBER, keyboard=get_age_registration_keyboard(vk_age))
            return
        age = int(normalized_text)
        if age < 14:
            send(texts.MSG_AGE_14PLUS, keyboard=get_age_registration_keyboard(vk_age))
            return
        if age > 99:
            send(texts.MSG_AGE_REAL, keyboard=get_age_registration_keyboard(vk_age))
            return
        save_text_field(user, "age", age)
    if ask_next_required_field(user, send):
        return
    show_review(user, send)


# Проверяет и сохраняет пол пользователя при регистрации или редактировании.
def handle_reg_gender(user, normalized_text, send):
    vk_gender = (user.get("vk_profile") or {}).get("gender")
    if normalized_text == texts.BUTTON_KEEP_CURRENT.lower():
        show_review(user, send)
        return
    if normalized_text == texts.BUTTON_GENDER_MALE.lower():
        save_text_field(user, "gender", "male")
    elif normalized_text == texts.BUTTON_GENDER_FEMALE.lower():
        save_text_field(user, "gender", "female")
    elif vk_gender and normalized_text == GENDER_LABELS[vk_gender].lower():
        save_text_field(user, "gender", vk_gender)
    else:
        send(texts.MSG_GENDER_BUTTON, keyboard=get_gender_edit_keyboard(GENDER_LABELS.get(vk_gender)))
        return
    if ask_next_required_field(user, send):
        return
    show_review(user, send)


# Проверяет и сохраняет город пользователя при регистрации или редактировании.
def handle_reg_city(user, raw_text, normalized_text, send):
    vk_city = (user.get("vk_profile") or {}).get("city")
    if normalized_text == texts.BUTTON_KEEP_CURRENT.lower():
        show_review(user, send)
        return
    cleaned_raw_text = _clean_visible_text(raw_text)
    cleaned_vk_city = _clean_visible_text(vk_city)
    if cleaned_vk_city and cleaned_raw_text == cleaned_vk_city:
        save_text_field(user, "city", vk_city)
    else:
        candidate = cleaned_raw_text
        if not candidate or len(candidate) > 50:
            send(
                texts.MSG_INVALID_CITY,
                keyboard=get_city_edit_keyboard(vk_city),
            )
            return
        save_text_field(user, "city", candidate)
    if ask_next_required_field(user, send):
        return
    show_review(user, send)


# Проверяет и сохраняет предпочтения пользователя при регистрации или редактировании.
def handle_reg_looking(user, normalized_text, send):
    if normalized_text == texts.BUTTON_KEEP_CURRENT.lower():
        show_review(user, send)
        return
    if normalized_text == texts.BUTTON_LOOKING_MALE.lower():
        save_text_field(user, "looking_for", "male")
    elif normalized_text == texts.BUTTON_LOOKING_FEMALE.lower():
        save_text_field(user, "looking_for", "female")
    elif normalized_text == texts.BUTTON_LOOKING_ANY.lower():
        save_text_field(user, "looking_for", "any")
    else:
        send(texts.MSG_LOOKING_BUTTON, keyboard=get_looking_keyboard())
        return
    if ask_next_required_field(user, send):
        return
    show_review(user, send)


# Проверяет и сохраняет текстовое описание «о себе» в анкете.
def handle_about(user, raw_text, attachments, send):
    has_existing_about = bool(_clean_visible_text(user.get("about")))
    invalid_about_keyboard = get_keep_current_keyboard() if has_existing_about else EMPTY_KEYBOARD

    if has_existing_about and _clean_visible_text(raw_text).lower() == texts.BUTTON_KEEP_CURRENT.lower():
        show_review(user, send)
        return
    candidate = _clean_visible_text(raw_text)
    if not candidate or attachments:
        send(texts.MSG_TEXT_2000_ONLY, keyboard=invalid_about_keyboard)
        return
    if len(candidate) > ABOUT_MAX_LENGTH:
        send(texts.MSG_TEXT_2000_ONLY, keyboard=invalid_about_keyboard)
        return
    save_text_field(user, "about", candidate)
    if ask_next_required_field(user, send):
        return
    show_review(user, send)


# Обрабатывает загруженные фото и управляет шагом фотографий в анкете.
def handle_photos(vk, user, raw_text, attachments, message_id, send):
    current_photos = [] if user.get("step") == STATE_PHOTO else list(user.get("photos", []))

    if user.get("step") == STATE_PHOTO and user.get("had_photos_before_edit") and raw_text.strip().lower() == texts.BUTTON_KEEP_CURRENT.lower():
        user["had_photos_before_edit"] = False
        show_review(user, send)
        return

    if user.get("step") == STATE_PHOTO_MORE and raw_text.strip() and raw_text.strip().lower() != texts.BUTTON_PHOTO_DONE.lower():
        send(format_photo_more_prompt(len(current_photos)), keyboard=get_photo_more_keyboard())
        return
    if raw_text.strip():
        send(texts.MSG_PHOTOS_ONLY)
        return

    new_photos, has_other_content = extract_photo_attachments_from_message(vk, message_id)
    if not new_photos and attachments:
        new_photos, has_other_content = extract_photo_payload(attachments)
    if not new_photos:
        if user.get("step") == STATE_PHOTO_MORE:
            if has_other_content:
                send(
                    f"{format_photo_more_prompt(len(current_photos))}\n{texts.MSG_SAVE_ONLY_PHOTOS}",
                    keyboard=get_photo_more_keyboard(),
                )
            else:
                send(format_photo_more_prompt(len(current_photos)), keyboard=get_photo_more_keyboard())
            return
        send(texts.MSG_PHOTOS_ONLY)
        return

    total_photos = current_photos + new_photos
    if len(total_photos) > 3:
        message = texts.MSG_PHOTOS_MAX
        if has_other_content:
            message += f"\n{texts.MSG_SAVE_ONLY_PHOTOS}"
        send(message)
        return

    save_photos_state(user, total_photos)
    if is_profile_complete(user) and user.get("is_active") != 1:
        save_text_field(user, "is_active", 1)
    if len(total_photos) < 3:
        user["step"] = STATE_PHOTO_MORE
        message = format_photo_more_prompt(len(total_photos))
        if has_other_content:
            message += f"\n{texts.MSG_SAVE_ONLY_PHOTOS}"
        send(message, keyboard=get_photo_more_keyboard())
        return

    show_review(user, send)


# Обрабатывает действие «завершить добавление фото» после первых загрузок.
def handle_photo_more(user, normalized_text, send):
    if normalized_text == texts.BUTTON_PHOTO_DONE.lower():
        show_review(user, send)
        return
    send(format_photo_more_prompt(len(user.get("photos", []))), keyboard=get_photo_more_keyboard())


# Обрабатывает нажатия кнопок на экране обзора анкеты.
def handle_review(user, normalized_text, send):
    if normalized_text == texts.BUTTON_REVIEW_BROWSE.lower():
        if is_duplicate_action(user, "review:browse"):
            return
        show_current_or_next_candidate(user["vk_user_id"], send)
        return
    if ENABLE_PROFILE_RESET_BUTTON and normalized_text == texts.BUTTON_RESET.lower():
        user["step"] = STATE_RESET_CONFIRM
        send(
            texts.MSG_RESET_CONFIRM,
            keyboard=get_reset_confirm_keyboard(),
        )
        return
    if normalized_text == texts.BUTTON_DEACTIVATE_PROFILE.lower():
        user["step"] = STATE_DEACTIVATE_CONFIRM
        send(texts.MSG_DEACTIVATE_CONFIRM, keyboard=get_deactivate_confirm_keyboard())
        return
    if normalized_text == texts.BUTTON_EDIT_PROFILE.lower():
        user["step"] = STATE_EDIT_MENU
        send(texts.MSG_WHAT_TO_EDIT, keyboard=get_edit_profile_keyboard())
        return
    if normalized_text == texts.BUTTON_EDIT_ABOUT.lower():
        user["step"] = STATE_ABOUT
        send(texts.MSG_ABOUT_EDIT_PROMPT, keyboard=get_keep_current_keyboard())
        return
    if normalized_text == texts.BUTTON_EDIT_GAMES.lower():
        start_games_flow(user, send, clear_reply_keyboard=True)
        return
    if normalized_text == texts.BUTTON_EDIT_PHOTO.lower():
        user["had_photos_before_edit"] = bool(user.get("photos"))
        user["step"] = STATE_PHOTO
        keyboard = get_photo_edit_keyboard() if user.get("had_photos_before_edit") else EMPTY_KEYBOARD
        send(texts.MSG_SEND_PHOTOS_PROMPT, keyboard=keyboard)
        return
    send(texts.MSG_REVIEW_FALLBACK, keyboard=get_review_keyboard())

# Обрабатывает нажатия кнопок в меню редактирования.
def handle_edit_menu(user, normalized_text, send):
    vk_profile = user.get("vk_profile") or {}
    if normalized_text == texts.BUTTON_EDIT_NAME.lower():
        user["step"] = STATE_REG_NAME
        send(texts.MSG_NAME_PROMPT, keyboard=get_name_edit_keyboard(vk_profile.get("name")))
        return
    if normalized_text == texts.BUTTON_EDIT_AGE.lower():
        user["step"] = STATE_REG_AGE
        send(texts.MSG_AGE_PROMPT, keyboard=get_age_edit_keyboard(user.get("age")))
        return
    if normalized_text == texts.BUTTON_EDIT_GENDER.lower():
        user["step"] = STATE_REG_GENDER
        send(
            texts.MSG_GENDER_PROMPT,
            keyboard=get_gender_edit_keyboard(GENDER_LABELS.get(vk_profile.get("gender"))),
        )
        return
    if normalized_text == texts.BUTTON_EDIT_LOOKING.lower():
        user["step"] = STATE_REG_LOOKING
        send(texts.MSG_LOOKING_PROMPT, keyboard=get_looking_keyboard())
        return
    if normalized_text == texts.BUTTON_EDIT_CITY.lower():
        user["step"] = STATE_REG_CITY
        send(texts.MSG_CITY_PROMPT, keyboard=get_city_edit_keyboard(vk_profile.get("city")))
        return
    if normalized_text == texts.BUTTON_BACK.lower():
        show_review(user, send)
        return
    send(texts.MSG_EDIT_MENU_FALLBACK, keyboard=get_edit_profile_keyboard())



# Обрабатывает действия пользователя во время просмотра чужих анкет.
def handle_browse(vk, user, normalized_text, send):
    vk_user_id = user["vk_user_id"]
    if normalized_text == texts.BUTTON_MY_PROFILE.lower():
        show_review(user, send)
        return
    if normalized_text == texts.BUTTON_BROWSE.lower():
        reactivate_profile_if_needed(user)
        user["browse_mode"] = "new"
        user["history_candidate_action"] = None
        user["history_cursor_id"] = None
        user["history_cursor_created_at"] = None
        user["current_candidate"] = None
        show_next_candidate(vk_user_id, send)
        return
    if normalized_text == texts.BUTTON_BACK_TO_PREVIOUS.lower():
        show_previous_candidate(vk_user_id, send)
        return
    if normalized_text == texts.BUTTON_BACK_TO_NEW.lower():
        user["browse_mode"] = "new"
        user["history_candidate_action"] = None
        user["history_cursor_id"] = None
        user["history_cursor_created_at"] = None
        user["current_candidate"] = None
        show_next_candidate(vk_user_id, send)
        return
    if normalized_text == texts.BUTTON_REPORT.lower():
        start_report_flow(user, send)
        return
    if normalized_text == texts.EMOJI_LIKE:
        candidate_vk_user_id = user.get("current_candidate")
        if user.get("browse_mode") == "history" and user.get("history_candidate_action") == "like":
            send(
                texts.MSG_LIKE_LOCKED,
                keyboard=get_browse_keyboard(viewing_history=True, history_action="like"),
            )
            return
        if is_duplicate_action(user, f"browse:like:{candidate_vk_user_id}"):
            return
        if not candidate_vk_user_id:
            send(texts.MSG_NO_PROFILES, keyboard=get_matches_keyboard())
            return
        candidate = get_profile_by_vk_user_id(candidate_vk_user_id)
        if not candidate or not candidate.get("is_active") or candidate.get("delivery_disabled"):
            user["current_candidate"] = None
            show_next_candidate(vk_user_id, send)
            return
        if candidate["vk_user_id"] == vk_user_id:
            user["current_candidate"] = None
            show_next_candidate(vk_user_id, send)
            return
        if is_profile_banned(vk_user_id):
            user["current_candidate"] = None
            show_next_candidate(vk_user_id, send)
            return
        liker_profile = get_profile_by_vk_user_id(vk_user_id) or user
        log_action("interaction_attempt", vk_user_id=vk_user_id, target_vk_user_id=candidate["vk_user_id"], interaction_type="like")
        result = record_interaction(vk_user_id, candidate["vk_user_id"], "like")
        if result.get("blocked_by_ban"):
            user["current_candidate"] = None
            show_next_candidate(vk_user_id, send)
            return
        resolve_pending_like(vk_user_id, candidate["vk_user_id"], "like")
        log_action("interaction_saved", vk_user_id=vk_user_id, target_vk_user_id=candidate["vk_user_id"], interaction_type="like", matched=result.get("matched"))
        if result["matched"]:
            match = result.get("target_profile") or {}
            send_match_notification(vk, vk_user_id, match)
            send_match_notification(vk, candidate["vk_user_id"], liker_profile)
            user["current_candidate"] = None
            user["step"] = STATE_BROWSE
            return
        if enqueue_pending_like(vk_user_id, candidate["vk_user_id"]):
            if ENABLE_LIKE_NOTIFICATIONS:
                send_like_notification(vk, candidate["vk_user_id"], liker_profile)
        user["current_candidate"] = None
        if user.get("browse_mode") == "history":
            user["browse_mode"] = "new"
            user["history_candidate_action"] = None
            user["history_cursor_id"] = None
            user["history_cursor_created_at"] = None
        show_next_candidate(vk_user_id, send)
        return
    if normalized_text == texts.EMOJI_MESSAGE:
        candidate_vk_user_id = user.get("current_candidate")
        if user.get("browse_mode") == "history" and user.get("history_candidate_action") == "like":
            send(
                texts.MSG_LIKE_LOCKED,
                keyboard=get_browse_keyboard(viewing_history=True, history_action="like"),
            )
            return
        if is_duplicate_action(user, f"browse:like_message:{candidate_vk_user_id}"):
            return
        if is_profile_banned(vk_user_id):
            user["current_candidate"] = None
            show_next_candidate(vk_user_id, send)
            return
        start_like_message_flow(user, send)
        return
    if normalized_text == texts.EMOJI_DISLIKE:
        candidate_vk_user_id = user.get("current_candidate")
        if user.get("browse_mode") == "history" and user.get("history_candidate_action") == "like":
            send(
                texts.MSG_LIKE_LOCKED,
                keyboard=get_browse_keyboard(viewing_history=True, history_action="like"),
            )
            return
        if is_duplicate_action(user, f"browse:dislike:{candidate_vk_user_id}"):
            return
        if not candidate_vk_user_id:
            send(texts.MSG_NO_PROFILES, keyboard=get_matches_keyboard())
            return
        candidate = get_profile_by_vk_user_id(candidate_vk_user_id)
        if not candidate or not candidate.get("is_active") or candidate.get("delivery_disabled"):
            user["current_candidate"] = None
            show_next_candidate(vk_user_id, send)
            return
        if candidate["vk_user_id"] == vk_user_id:
            user["current_candidate"] = None
            show_next_candidate(vk_user_id, send)
            return
        log_action("interaction_attempt", vk_user_id=vk_user_id, target_vk_user_id=candidate["vk_user_id"], interaction_type="dislike")
        record_interaction(vk_user_id, candidate["vk_user_id"], "dislike")
        resolve_pending_like(vk_user_id, candidate["vk_user_id"], "dislike")
        log_action("interaction_saved", vk_user_id=vk_user_id, target_vk_user_id=candidate["vk_user_id"], interaction_type="dislike")
        user["current_candidate"] = None
        if user.get("browse_mode") == "history":
            user["browse_mode"] = "new"
            user["history_candidate_action"] = None
            user["history_cursor_id"] = None
            user["history_cursor_created_at"] = None
        show_next_candidate(vk_user_id, send)
        return
    if not user.get("current_candidate"):
        send(texts.MSG_NO_PROFILES, keyboard=get_matches_keyboard())
        return
    send(
        texts.MSG_CHOOSE_ACTION,
        keyboard=get_browse_keyboard(
            viewing_history=user.get("browse_mode") == "history",
            history_action=user.get("history_candidate_action"),
        ),
    )


# Обрабатывает подтверждение или отмену отключения анкеты.
def handle_deactivate_confirm(user, normalized_text, send):
    if normalized_text == texts.BUTTON_BACK.lower():
        show_review(user, send)
        return
    if normalized_text == texts.BUTTON_DEACTIVATE.lower():
        save_text_field(user, "is_active", 0)
        user["step"] = STATE_BROWSE
        user["current_candidate"] = None
        name = user.get("name") or texts.LABEL_FRIEND
        send(format_done_message(name), keyboard=get_matches_keyboard())
        return
    send(texts.MSG_DEACTIVATE_CONFIRM, keyboard=get_deactivate_confirm_keyboard())


# Обрабатывает подтверждение или отмену полного сброса анкеты.
def handle_reset_confirm(vk, user, normalized_text, send):
    if normalized_text == texts.BUTTON_BACK.lower():
        show_review(user, send)
        return
    if ENABLE_PROFILE_RESET_BUTTON and normalized_text == texts.BUTTON_RESET.lower():
        vk_user_id = user["vk_user_id"]
        delete_user_data(vk_user_id)
        users.pop(vk_user_id, None)
        send(texts.MSG_RESET_DONE, keyboard=EMPTY_KEYBOARD)
        start_bot_flow(vk, vk_user_id, send)
        return
    send(
        texts.MSG_RESET_CONFIRM,
        keyboard=get_reset_confirm_keyboard(),
    )

# Главный обработчик входящего сообщения VK, который маршрутизирует его по текущему состоянию.
def handle_message(vk, vk_user_id, text, attachments, message_id=None, payload=None):
    before_user = users.get(vk_user_id, {})
    log_action(
        "incoming_message",
        vk_user_id=vk_user_id,
        step_before=before_user.get("step"),
        text=_preview_text(text),
        attachment_count=len(attachments or []),
        has_payload=bool(payload),
        message_id=message_id,
    )
    try:
        reset_profile_delivery_status(vk_user_id)

        def send(message, keyboard=None, attachment=None):
            current_user = users.get(vk_user_id, {})
            log_action(
                "bot_send",
                vk_user_id=vk_user_id,
                step=current_user.get("step"),
                text=_preview_text(message),
                has_keyboard=keyboard is not None and keyboard != EMPTY_KEYBOARD,
                has_attachment=bool(attachment),
            )
            safe_vk_send(
                vk,
                user_id=vk_user_id,
                message=fit_message_text(message),
                random_id=0,
                keyboard=keyboard,
                attachment=attachment,
            )

        raw_text = text or ""
        normalized_text = raw_text.strip().lower()
        parsed_payload = parse_payload(payload)

        if is_profile_banned(vk_user_id):
            user = users.get(vk_user_id) or ensure_runtime_user(vk, vk_user_id)
            _handle_banned_user(user, send)
            return

        game_buttons = {
            "dota 2": "dota2",
            "cs2": "cs2",
            "minecraft": "minecraft",
            "mlbb": "mlbb",
            "valorant": "valorant",
            "pubg": "pubg",
            "dead by daylight": "dbd",
            "genshin impact": "genshin",
        }

        if vk_user_id in users and get_profile_by_vk_user_id(vk_user_id) is None:
            users.pop(vk_user_id, None)

        if vk_user_id not in users:
            start_bot_flow(vk, vk_user_id, send)
            return

        if normalized_text == texts.BUTTON_START.lower() or parsed_payload.get("command") == "start":
            start_bot_flow(vk, vk_user_id, send)
            return

        user = users[vk_user_id]
        step = user.get("step")

        if step == STATE_REG_NAME:
            handle_reg_name(user, raw_text, normalized_text, send)
            return
        if step == STATE_REG_AGE:
            handle_reg_age(user, normalized_text, send)
            return
        if step == STATE_REG_GENDER:
            handle_reg_gender(user, normalized_text, send)
            return
        if step == STATE_REG_CITY:
            handle_reg_city(user, raw_text, normalized_text, send)
            return
        if step == STATE_REG_LOOKING:
            handle_reg_looking(user, normalized_text, send)
            return
        if step == STATE_GAMES:
            send(texts.MSG_CHOOSE_GAMES_WITH_BUTTONS)
            return
        if step == STATE_ABOUT:
            handle_about(user, raw_text, attachments, send)
            return
        if step in {STATE_PHOTO, STATE_PHOTO_APPEND}:
            handle_photos(vk, user, raw_text, attachments, message_id, send)
            return
        if step == STATE_PHOTO_MORE:
            if normalized_text == texts.BUTTON_PHOTO_DONE.lower():
                handle_photo_more(user, normalized_text, send)
            else:
                handle_photos(vk, user, raw_text, attachments, message_id, send)
            return
        if step == STATE_REVIEW:
            handle_review(user, normalized_text, send)
            return
        if step == STATE_EDIT_MENU:
            handle_edit_menu(user, normalized_text, send)
            return
        if step == STATE_INCOMING_LIKE:
            handle_incoming_like(vk, user, normalized_text, send)
            return
        if step == STATE_LIKE_MESSAGE:
            handle_like_message_input(vk, user, raw_text, attachments, send)
            return
        if step == STATE_REPORT_REASON:
            handle_report_reason(vk, user, raw_text, attachments, send)
            return
        if step == STATE_DEACTIVATE_CONFIRM:
            handle_deactivate_confirm(user, normalized_text, send)
            return
        if step == STATE_RESET_CONFIRM:
            handle_reset_confirm(vk, user, normalized_text, send)
            return
        if step == STATE_BROWSE:
            handle_browse(vk, user, normalized_text, send)
            return

        start_bot_flow(vk, vk_user_id, send)
    finally:
        final_user = users.get(vk_user_id, {})
        persist_runtime_user(vk_user_id)
        log_action(
            "state_after_message",
            vk_user_id=vk_user_id,
            step_after=final_user.get("step"),
            current_candidate=final_user.get("current_candidate"),
        )
