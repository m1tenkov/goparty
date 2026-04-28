import json
from datetime import date

from database import (
    GAME_CODES,
    GAME_TITLES,
    get_or_create_user,
    get_next_pending_like_profile,
    get_previous_interaction,
    get_profile_by_vk_user_id,
    get_random_candidate,
    has_pending_like_for_target,
    load_runtime_state,
    save_games,
    save_photos,
    save_profile_fields,
    save_runtime_state,
)

from .constants import (
    ABOUT_MAX_LENGTH,
    GENDER_LABELS,
    LOOKING_LABELS,
    NO_GAMES_TEXT,
    STATE_ABOUT,
    STATE_BROWSE,
    STATE_GAMES,
    STATE_PHOTO,
    STATE_PHOTO_APPEND,
    STATE_PHOTO_MORE,
    STATE_REG_AGE,
    STATE_REG_CITY,
    STATE_REG_GENDER,
    STATE_REG_LOOKING,
    STATE_REG_NAME,
    STATE_REVIEW,
    VK_MESSAGE_MAX_LENGTH,
    users,
)
from . import texts
from .text_formatters import format_games_summary as build_games_summary_text, format_profile_text
from .keyboards import (
    EMPTY_KEYBOARD,
    get_browse_keyboard,
    get_games_keyboard,
    get_gender_keyboard,
    get_looking_keyboard,
    get_matches_keyboard,
    get_no_profiles_keyboard,
    get_review_keyboard,
)

def parse_payload(payload):
    if not payload:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {}
    return {}


def event_value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _calculate_age_from_bdate(bdate):
    if not bdate:
        return None

    parts = bdate.split(".")
    if len(parts) != 3:
        return None

    try:
        birth_day, birth_month, birth_year = map(int, parts)
        today = date.today()
        age = today.year - birth_year
        if (today.month, today.day) < (birth_month, birth_day):
            age -= 1
    except ValueError:
        return None

    if 14 <= age <= 99:
        return age
    return None


def fetch_vk_profile(vk, user_id):
    try:
        user_info = vk.users.get(user_ids=user_id, fields="bdate,city,sex")[0]
    except Exception:
        return {}

    profile = {
        "name": user_info.get("first_name"),
        "age": None,
        "gender": None,
        "city": user_info.get("city", {}).get("title") if user_info.get("city") else None,
    }

    if user_info.get("sex") == 1:
        profile["gender"] = "female"
    elif user_info.get("sex") == 2:
        profile["gender"] = "male"

    age = _calculate_age_from_bdate(user_info.get("bdate"))
    if age is not None:
        profile["age"] = age

    return profile


def base_runtime_user(vk_user_id):
    profile = get_profile_by_vk_user_id(vk_user_id) or {}
    runtime = {
        "vk_user_id": vk_user_id,
        "db_user_id": profile.get("db_user_id"),
        "name": profile.get("name"),
        "age": profile.get("age"),
        "city": profile.get("city"),
        "about": profile.get("about"),
        "gender": profile.get("gender"),
        "looking_for": profile.get("looking_for"),
        "games": list(profile.get("games", [])),
        "photos": list(profile.get("photos", [])),
        "delivery_disabled": profile.get("delivery_disabled", 0),
        "delivery_error_code": profile.get("delivery_error_code"),
        "delivery_error_at": profile.get("delivery_error_at"),
        "step": None,
        "current_candidate": None,
        "games_step_completed": bool(profile.get("games_step_completed", 0)),
        "browse_mode": "new",
        "history_candidate_action": None,
        "history_cursor_id": None,
        "history_cursor_created_at": None,
        "pending_like_profile": None,
        "like_message_target_vk_user_id": None,
        "like_message_resume_step": None,
        "report_target_vk_user_id": None,
        "report_resume_step": None,
        "had_photos_before_edit": False,
        "resume_step": None,
        "suppress_post_match_prompt": False,
        "vk_profile": {},
    }
    for code in GAME_CODES:
        runtime[code] = 1 if code in runtime["games"] else 0
    return runtime


def ensure_runtime_user(vk, vk_user_id):
    get_or_create_user(vk_user_id)
    runtime = base_runtime_user(vk_user_id)
    persisted = load_runtime_state(vk_user_id)
    existing = users.get(vk_user_id, {})
    for source in (persisted, existing):
        runtime["step"] = source.get("step", runtime["step"])
        runtime["current_candidate"] = source.get("current_candidate", runtime["current_candidate"])
        runtime["games_step_completed"] = source.get("games_step_completed", runtime["games_step_completed"])
        runtime["browse_mode"] = source.get("browse_mode", runtime["browse_mode"])
        runtime["history_candidate_action"] = source.get("history_candidate_action", runtime["history_candidate_action"])
        runtime["history_cursor_id"] = source.get("history_cursor_id", runtime["history_cursor_id"])
        runtime["history_cursor_created_at"] = source.get("history_cursor_created_at", runtime["history_cursor_created_at"])
        runtime["pending_like_profile"] = source.get("pending_like_profile", runtime["pending_like_profile"])
        runtime["like_message_target_vk_user_id"] = source.get("like_message_target_vk_user_id", runtime["like_message_target_vk_user_id"])
        runtime["like_message_resume_step"] = source.get("like_message_resume_step", runtime["like_message_resume_step"])
        runtime["report_target_vk_user_id"] = source.get("report_target_vk_user_id", runtime["report_target_vk_user_id"])
        runtime["report_resume_step"] = source.get("report_resume_step", runtime["report_resume_step"])
        runtime["had_photos_before_edit"] = source.get("had_photos_before_edit", runtime["had_photos_before_edit"])
        runtime["resume_step"] = source.get("resume_step", runtime["resume_step"])
        runtime["suppress_post_match_prompt"] = source.get("suppress_post_match_prompt", runtime.get("suppress_post_match_prompt", False))
        runtime["_last_action_key"] = source.get("_last_action_key", runtime.get("_last_action_key"))
        runtime["_last_action_at"] = source.get("_last_action_at", runtime.get("_last_action_at", 0))
    runtime["vk_profile"] = fetch_vk_profile(vk, vk_user_id)
    users[vk_user_id] = runtime
    return runtime


def sync_profile_from_db(vk, vk_user_id):
    return ensure_runtime_user(vk, vk_user_id)


def persist_runtime_user(vk_user_id):
    user = users.get(vk_user_id)
    if not user:
        save_runtime_state(vk_user_id, None)
        return

    save_runtime_state(
        vk_user_id,
        {
            "step": user.get("step"),
            "current_candidate": user.get("current_candidate"),
            "games_step_completed": user.get("games_step_completed", False),
            "browse_mode": user.get("browse_mode", "new"),
            "history_candidate_action": user.get("history_candidate_action"),
            "history_cursor_id": user.get("history_cursor_id"),
            "history_cursor_created_at": user.get("history_cursor_created_at"),
            "pending_like_profile": user.get("pending_like_profile"),
            "like_message_target_vk_user_id": user.get("like_message_target_vk_user_id"),
            "like_message_resume_step": user.get("like_message_resume_step"),
            "report_target_vk_user_id": user.get("report_target_vk_user_id"),
            "report_resume_step": user.get("report_resume_step"),
            "had_photos_before_edit": user.get("had_photos_before_edit", False),
            "resume_step": user.get("resume_step"),
            "suppress_post_match_prompt": user.get("suppress_post_match_prompt", False),
        },
    )


def selected_games(user):
    return [code for code in GAME_CODES if user.get(code)]


def has_no_games_marker(user):
    return not selected_games(user)


def games_display(user):
    games = [GAME_TITLES[code] for code in selected_games(user)]
    if not games and has_no_games_marker(user):
        return [NO_GAMES_TEXT]
    return games


def fit_message_text(text, limit=VK_MESSAGE_MAX_LENGTH):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def format_games_summary(user):
    games = games_display(user)
    games_text = ", ".join(games) if games else NO_GAMES_TEXT
    return build_games_summary_text(games_text)


def format_games_picker_prompt():
    return texts.MSG_GAMES_PICKER


def format_photo_more_prompt(current_count):
    remaining = max(0, 3 - int(current_count))
    if remaining <= 0:
        return texts.MSG_PHOTOS_ENOUGH
    if remaining == 1:
        return texts.MSG_ADD_ONE_PHOTO
    return texts.MSG_ADD_ONE_TWO_PHOTOS


def format_profile(user, include_review=False):
    name = user.get("name") or texts.LABEL_NO_NAME
    age = user.get("age") or "?"
    city = user.get("city") or texts.LABEL_NO_CITY
    about = user.get("about") or ""
    games_text = ", ".join(games_display(user)) if games_display(user) else texts.LABEL_GAMES_UNSPECIFIED
    return fit_message_text(format_profile_text(name, age, city, games_text, about, include_review=include_review))


def extract_photo_payload(attachments):
    if not attachments:
        return [], False

    photos = []
    has_other_content = False
    if isinstance(attachments, list):
        for attachment in attachments:
            if attachment.get("type") != "photo":
                has_other_content = True
                continue
            photo = attachment.get("photo") or {}
            owner_id = photo.get("owner_id")
            photo_id = photo.get("id")
            access_key = photo.get("access_key")
            if owner_id is None or photo_id is None:
                continue
            token = f"{owner_id}_{photo_id}"
            if access_key:
                token = f"{token}_{access_key}"
            photos.append(token)
        return photos, has_other_content

    photo_keys = []
    for key, value in attachments.items():
        if not key.endswith("_type"):
            continue
        if value == "photo":
            photo_keys.append(key[:-5])
        else:
            has_other_content = True

    for base_key in photo_keys:
        photo_value = attachments.get(base_key)
        if not photo_value:
            continue
        access_key = attachments.get(f"{base_key}_access_key")
        token = f"{photo_value}_{access_key}" if access_key else photo_value
        photos.append(token)

    return photos, has_other_content


def extract_photo_attachments(attachments):
    photos, _ = extract_photo_payload(attachments)
    return photos or None


def extract_photo_attachments_from_message(vk, message_id):
    if not message_id:
        return [], False
    try:
        response = vk.messages.getById(message_ids=message_id)
    except Exception:
        return [], False
    items = response.get("items") or []
    if not items:
        return [], False
    return extract_photo_payload(items[0].get("attachments") or [])


def build_photo_attachment(profile):
    photos = []
    for photo in profile.get("photos", []):
        token = str(photo).strip()
        if not token:
            continue
        if not token.startswith("photo"):
            token = f"photo{token}"
        photos.append(token)
    return ",".join(photos) or None


def save_text_field(user, field, value):
    user[field] = value
    save_profile_fields(user["vk_user_id"], {field: value})


def save_games_state(user):
    user["games"] = selected_games(user)
    save_games(user["vk_user_id"], user["games"])


def save_photos_state(user, photos):
    user["photos"] = list(photos[:3])
    save_photos(user["vk_user_id"], user["photos"])


def show_games_picker(user, send):
    send(format_games_picker_prompt(), keyboard=get_games_keyboard(user))


def start_games_flow(user, send, clear_reply_keyboard=False):
    user["step"] = STATE_GAMES
    if clear_reply_keyboard:
        # A visible service message is more reliable than a zero-width char for hiding VK reply keyboards.
        send(texts.MSG_CHOOSE_GAMES_WITH_BUTTONS, keyboard=EMPTY_KEYBOARD)
    show_games_picker(user, send)


def reactivate_profile_if_needed(user):
    if user.get("is_active") == 0:
        save_text_field(user, "is_active", 1)


def is_profile_complete(user):
    return all(
        [
            user.get("name"),
            user.get("age"),
            user.get("gender"),
            user.get("city"),
            user.get("looking_for"),
            games_display(user),
            user.get("about"),
            user.get("photos"),
        ]
    )


def ask_next_required_field(user, send):
    if not user.get("name"):
        user["step"] = STATE_REG_NAME
        send(texts.MSG_NAME_PROMPT)
        return True
    if not user.get("age"):
        user["step"] = STATE_REG_AGE
        send(texts.MSG_AGE_PROMPT)
        return True
    if not user.get("gender"):
        user["step"] = STATE_REG_GENDER
        send(texts.MSG_GENDER_PROMPT, keyboard=get_gender_keyboard())
        return True
    if not user.get("city"):
        user["step"] = STATE_REG_CITY
        send(texts.MSG_CITY_PROMPT)
        return True
    if not user.get("looking_for"):
        user["step"] = STATE_REG_LOOKING
        send(texts.MSG_LOOKING_PROMPT, keyboard=get_looking_keyboard())
        return True
    if not user.get("games_step_completed", False):
        start_games_flow(user, send)
        return True
    if not user.get("about"):
        user["step"] = STATE_ABOUT
        send(texts.MSG_ABOUT_PROMPT, keyboard=EMPTY_KEYBOARD)
        return True
    if not user.get("photos"):
        user["step"] = STATE_PHOTO
        send(texts.MSG_ADD_PHOTO_PROMPT, keyboard=EMPTY_KEYBOARD)
        return True
    return False


def show_review(user, send):
    user["step"] = STATE_REVIEW
    user["browse_mode"] = "new"
    user["history_candidate_action"] = None
    user["history_cursor_id"] = None
    user["history_cursor_created_at"] = None
    send(
        format_profile(user, include_review=True),
        keyboard=get_review_keyboard(),
        attachment=build_photo_attachment(user),
    )


def _candidate_browse_text(candidate, viewing_history=False, history_action=None):
    text = format_profile(candidate, include_review=False)
    if viewing_history and history_action == "like":
        text += f"\n\n{texts.MSG_PROFILE_IN_HISTORY_LIKED}"
    return text


def show_next_candidate(vk_user_id, send):
    user = users[vk_user_id]
    reactivate_profile_if_needed(user)
    candidate = get_random_candidate(vk_user_id)
    user["step"] = STATE_BROWSE
    user["browse_mode"] = "new"
    user["history_candidate_action"] = None
    user["history_cursor_id"] = None
    user["history_cursor_created_at"] = None
    user["current_candidate"] = candidate["vk_user_id"] if candidate else None

    if not candidate:
        send(texts.MSG_NO_PROFILES, keyboard=get_no_profiles_keyboard())
        return

    send(
        _candidate_browse_text(candidate),
        keyboard=get_browse_keyboard(),
        attachment=build_photo_attachment(candidate),
    )


def show_current_or_next_candidate(vk_user_id, send):
    user = users[vk_user_id]
    reactivate_profile_if_needed(user)
    if user.get("browse_mode") == "history":
        candidate_vk_user_id = user.get("current_candidate")
        if not candidate_vk_user_id:
            show_previous_candidate(vk_user_id, send)
            return
        candidate = get_profile_by_vk_user_id(candidate_vk_user_id)
        if not candidate:
            show_previous_candidate(vk_user_id, send)
            return
        send(
            _candidate_browse_text(candidate, viewing_history=True, history_action=user.get("history_candidate_action")),
            keyboard=get_browse_keyboard(viewing_history=True, history_action=user.get("history_candidate_action")),
            attachment=build_photo_attachment(candidate),
        )
        return
    candidate_vk_user_id = user.get("current_candidate")
    user["step"] = STATE_BROWSE
    if not candidate_vk_user_id:
        show_next_candidate(vk_user_id, send)
        return
    candidate = get_profile_by_vk_user_id(candidate_vk_user_id)
    if not candidate or not candidate.get("is_active") or candidate.get("delivery_disabled"):
        user["current_candidate"] = None
        show_next_candidate(vk_user_id, send)
        return
    send(
        _candidate_browse_text(candidate),
        keyboard=get_browse_keyboard(),
        attachment=build_photo_attachment(candidate),
    )


def show_previous_candidate(vk_user_id, send):
    user = users[vk_user_id]
    if user.get("browse_mode") == "history" and user.get("history_cursor_id") == 0:
        send(
            texts.MSG_NO_HISTORY,
            keyboard=get_matches_keyboard(),
        )
        return
    previous = get_previous_interaction(
        vk_user_id,
        before_created_at=user.get("history_cursor_created_at") if user.get("browse_mode") == "history" else None,
        before_id=user.get("history_cursor_id") if user.get("browse_mode") == "history" else None,
    )
    user["step"] = STATE_BROWSE
    user["browse_mode"] = "history"

    if not previous:
        user["current_candidate"] = None
        user["history_candidate_action"] = None
        user["history_cursor_id"] = 0
        user["history_cursor_created_at"] = ""
        send(
            texts.MSG_NO_HISTORY,
            keyboard=get_matches_keyboard(),
        )
        return

    candidate = previous["profile"]
    user["current_candidate"] = candidate.get("vk_user_id")
    user["history_candidate_action"] = previous.get("action")
    user["history_cursor_id"] = previous.get("id")
    user["history_cursor_created_at"] = previous.get("created_at")
    send(
        _candidate_browse_text(candidate, viewing_history=True, history_action=previous.get("action")),
        keyboard=get_browse_keyboard(viewing_history=True, history_action=previous.get("action")),
        attachment=build_photo_attachment(candidate),
    )


def get_pending_like_profile(vk_user_id):
    return get_next_pending_like_profile(vk_user_id)


def has_pending_likes(vk_user_id):
    return has_pending_like_for_target(vk_user_id)


def apply_vk_defaults(vk_user_id, user):
    vk_profile = user.get("vk_profile") or {}
    updates = {}
    for field in ("name", "age", "city", "gender"):
        if not user.get(field) and vk_profile.get(field):
            user[field] = vk_profile[field]
            updates[field] = vk_profile[field]
    if updates:
        save_profile_fields(vk_user_id, updates)
