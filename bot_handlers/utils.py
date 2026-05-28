import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import hashlib
import requests
from vk_api.upload import VkUpload

from config import BASE_DIR, PHOTO_STORAGE_DIR
from database import (
    DEFAULT_FILTERS,
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
    save_user_filters,
    save_runtime_state,
)

from .constants import (
    ABOUT_MAX_LENGTH,
    GENDER_LABELS,
    LOOKING_LABELS,
    NO_GAMES_TEXT,
    STATE_ABOUT,
    STATE_BROWSE,
    STATE_FILTERS,
    STATE_GAMES,
    STATE_PHOTO,
    STATE_PHOTO_APPEND,
    STATE_PHOTO_MORE,
    STATE_REG_AGE,
    STATE_REG_CITY,
    STATE_REG_GENDER,
    STATE_REG_LOOKING,
    STATE_REG_MICROPHONE,
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
    get_microphone_keyboard,
    get_looking_keyboard,
    get_matches_keyboard,
    get_no_profiles_keyboard,
    get_review_keyboard,
)


LOCAL_PHOTO_PREFIX = "storage/photos/"
DEFAULT_PHOTO_PATH = BASE_DIR / "storage" / "photos" / "default_photo.png"
_vk_api_method = None


def set_vk_transport(vk):
    global _vk_api_method
    _vk_api_method = vk

# Преобразует payload VK в словарь независимо от исходного формата.
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


# Безопасно читает значение из словаря или атрибута объекта.
def event_value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


# Вычисляет возраст по дате рождения VK, если в ней указан год.
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


# Запрашивает открытые данные VK-профиля для автозаполнения анкеты.
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


# Собирает базовую in-memory структуру пользователя из данных базы.
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
        "uses_microphone": int(profile.get("uses_microphone")) if profile.get("uses_microphone") is not None else None,
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
        "filter_sort": profile.get("filter_sort", DEFAULT_FILTERS["filter_sort"]),
        "filter_age_min": profile.get("filter_age_min", DEFAULT_FILTERS["filter_age_min"]),
        "filter_age_max": profile.get("filter_age_max", DEFAULT_FILTERS["filter_age_max"]),
        "filter_required_games": list(profile.get("filter_required_games", DEFAULT_FILTERS["filter_required_games"])),
        "filter_microphone": profile.get("filter_microphone", DEFAULT_FILTERS["filter_microphone"]),
    }
    for code in GAME_CODES:
        runtime[code] = 1 if code in runtime["games"] else 0
    return runtime


# Восстанавливает или создает runtime-состояние пользователя из БД, памяти и данных VK.
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


# Обновляет runtime-объект пользователя из актуального сохраненного состояния.
def sync_profile_from_db(vk, vk_user_id):
    return ensure_runtime_user(vk, vk_user_id)


# Сохраняет важные runtime-поля пользователя в таблицу сессий.
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


def persist_user_filters(user):
    save_user_filters(
        user["vk_user_id"],
        {
            "filter_sort": user.get("filter_sort", DEFAULT_FILTERS["filter_sort"]),
            "filter_age_min": user.get("filter_age_min", DEFAULT_FILTERS["filter_age_min"]),
            "filter_age_max": user.get("filter_age_max", DEFAULT_FILTERS["filter_age_max"]),
            "filter_required_games": list(user.get("filter_required_games", DEFAULT_FILTERS["filter_required_games"])),
            "filter_microphone": user.get("filter_microphone", DEFAULT_FILTERS["filter_microphone"]),
            "looking_for": user.get("looking_for", DEFAULT_FILTERS["looking_for"]),
        },
    )


# Возвращает список кодов игр, которые сейчас выбраны в runtime-состоянии.
def selected_games(user):
    return [code for code in GAME_CODES if user.get(code)]


# Проверяет, что у пользователя нет выбранных игр и нужен fallback-маркер отсутствия игр.
def has_no_games_marker(user):
    return not selected_games(user)


# Возвращает список игр в виде, в котором он показывается в анкете.
def games_display(user):
    games = [GAME_TITLES[code] for code in selected_games(user)]
    if not games and has_no_games_marker(user):
        return [NO_GAMES_TEXT]
    return games


# Обрезает текст сообщения под лимиты VK, не ломая отображение.
def fit_message_text(text, limit=VK_MESSAGE_MAX_LENGTH):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


# Форматирует текущий набор игр в короткое итоговое сообщение.
def format_games_summary(user):
    games = games_display(user)
    games_text = ", ".join(games) if games else NO_GAMES_TEXT
    return build_games_summary_text(games_text)


# Возвращает стандартный текст-подсказку для шага выбора игр.
def format_games_picker_prompt():
    return texts.MSG_GAMES_PICKER


def format_games_buttons_message():
    return texts.MSG_GAMES_BUTTONS


def format_filter_games_picker_prompt():
    return texts.MSG_FILTER_GAME_PROMPT


def format_filter_games_buttons_message():
    return texts.MSG_FILTER_GAMES_BUTTONS


def format_filter_games_done_message():
    return texts.MSG_FILTER_GAMES_DONE


def format_filters_message(user):
    looking_label = LOOKING_LABELS.get(user.get("looking_for"), LOOKING_LABELS[DEFAULT_FILTERS["looking_for"]])
    sort_label = texts.MSG_FILTERS_SORT_GAMES if user.get("filter_sort", "games") == "games" else texts.MSG_FILTERS_SORT_CITY
    age_min = user.get("filter_age_min")
    age_max = user.get("filter_age_max")
    age_label = f"{age_min}-{age_max}" if age_min is not None and age_max is not None else texts.MSG_FILTERS_AGE_ANY
    required_games = user.get("filter_required_games") or []
    game_titles = {
        "dota2": "Dota 2",
        "cs2": "CS2",
        "minecraft": "Minecraft",
        "mlbb": "MLBB",
        "valorant": "Valorant",
        "pubg": "PUBG",
        "dbd": "Dead by Daylight",
        "genshin": "Genshin Impact",
    }
    game_label = ", ".join(game_titles[code] for code in required_games if code in game_titles) or texts.MSG_FILTERS_GAMES_ANY
    filter_microphone = user.get("filter_microphone")
    if filter_microphone in (1, True):
        microphone_label = texts.MSG_FILTERS_MICROPHONE_YES
    else:
        microphone_label = texts.MSG_FILTERS_MICROPHONE_ANY
    return (
        f"{texts.MSG_WHAT_TO_FILTER}\n\n"
        f"{texts.MSG_FILTERS_LOOKING_LABEL}: {looking_label}\n"
        f"{texts.MSG_FILTERS_SORT_LABEL}: {sort_label}\n"
        f"{texts.MSG_FILTERS_AGE_LABEL}: {age_label}\n"
        f"{texts.MSG_FILTERS_GAMES_LABEL}: {game_label}\n"
        f"{texts.MSG_FILTERS_MICROPHONE_LABEL}: {microphone_label}"
    )


# Формирует подсказку после загрузки меньше трех фотографий.
def format_photo_more_prompt(current_count):
    remaining = max(0, 3 - int(current_count))
    if remaining <= 0:
        return texts.MSG_PHOTOS_ENOUGH
    if remaining == 1:
        return texts.MSG_ADD_ONE_PHOTO
    return texts.MSG_ADD_ONE_TWO_PHOTOS


# Форматирует runtime-профиль пользователя или кандидата в читаемый текст.
def format_profile(user, include_review=False):
    name = user.get("name") or texts.LABEL_NO_NAME
    age = user.get("age") or "?"
    city = user.get("city") or texts.LABEL_NO_CITY
    about = user.get("about") or ""
    games_text = ", ".join(games_display(user)) if games_display(user) else texts.LABEL_GAMES_UNSPECIFIED
    uses_microphone = user.get("uses_microphone")
    microphone_text = "Играю с микрофоном" if uses_microphone in (1, True) else "Играю без микрофона"
    microphone_emoji = texts.EMOJI_MICROPHONE_ON if uses_microphone in (1, True) else texts.EMOJI_MICROPHONE_OFF
    return fit_message_text(
        format_profile_text(
            name,
            age,
            city,
            games_text,
            microphone_text,
            about,
            include_review=include_review,
            microphone_emoji=microphone_emoji,
        )
    )


# Возвращает True, если строка похожа на локальный путь к фото в хранилище проекта.
def _is_local_photo_reference(value):
    normalized = str(value or "").replace("\\", "/").strip()
    return normalized.startswith(LOCAL_PHOTO_PREFIX)


def _normalize_photo_entry(photo):
    if isinstance(photo, dict):
        return {
            "path": str(photo.get("path") or "").strip(),
            "vk_token": str(photo.get("vk_token") or "").strip() or None,
        }
    value = str(photo or "").strip()
    if not value:
        return {"path": "", "vk_token": None}
    if _is_local_photo_reference(value):
        return {"path": value, "vk_token": None}
    return {"path": value, "vk_token": value}


# Преобразует относительный путь из БД в абсолютный путь на диске.
def resolve_local_photo_path(photo_reference):
    normalized = str(photo_reference or "").replace("\\", "/").strip()
    if not normalized or not _is_local_photo_reference(normalized):
        return None
    return (BASE_DIR / Path(normalized)).resolve()


def resolve_default_photo_path():
    return DEFAULT_PHOTO_PATH if DEFAULT_PHOTO_PATH.exists() else None


# Удаляет локальные фотофайлы, которые больше не используются в анкете.
def delete_local_photo_files(photo_references):
    for reference in photo_references or []:
        photo_entry = _normalize_photo_entry(reference)
        absolute_path = resolve_local_photo_path(photo_entry.get("path"))
        if not absolute_path:
            continue
        try:
            absolute_path.unlink(missing_ok=True)
        except OSError:
            continue


def _pick_best_photo_url(photo):
    sizes = photo.get("sizes") or []
    best_url = None
    best_area = -1
    for item in sizes:
        url = item.get("url")
        if not url:
            continue
        width = int(item.get("width") or 0)
        height = int(item.get("height") or 0)
        area = width * height
        if area >= best_area:
            best_url = url
            best_area = area
    return best_url or (photo.get("orig_photo") or {}).get("url")


def _photo_extension_from_url(url):
    suffix = Path(urlparse(str(url)).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return suffix
    return ".jpg"


def _download_photo_to_storage(vk_user_id, photo, sort_index):
    url = _pick_best_photo_url(photo)
    if not url:
        return None
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    content = response.content
    digest = hashlib.sha1(content).hexdigest()[:16]
    user_dir = PHOTO_STORAGE_DIR / str(vk_user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_dir / f"{sort_index}_{digest}{_photo_extension_from_url(url)}"
    file_path.write_bytes(content)
    return {
        "path": file_path.relative_to(BASE_DIR).as_posix(),
        "vk_token": None,
    }


def _is_vk_photo_token_valid(vk, token):
    if vk is None or not token:
        return False
    token_value = str(token).strip()
    if token_value.startswith("photo"):
        token_value = token_value[5:]
    try:
        response = vk.photos.getById(photos=token_value)
    except Exception:
        return False
    return bool(response)


# Извлекает фото из вложений VK, скачивает их в локальное хранилище и отмечает наличие других типов вложений.
def extract_photo_payload(attachments, vk_user_id):
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
            stored_path = _download_photo_to_storage(vk_user_id, photo, len(photos) + 1)
            if stored_path:
                photos.append(stored_path)
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
        if not photo_value or not str(photo_value).startswith(("http://", "https://")):
            continue
        stored_path = _download_photo_to_storage(
            vk_user_id,
            {
                "sizes": [{"url": photo_value}],
            },
            len(photos) + 1,
        )
        if stored_path:
            photos.append(stored_path)

    return photos, has_other_content


# Возвращает только пути к фото из общего payload вложений.
def extract_photo_attachments(attachments, vk_user_id):
    photos, _ = extract_photo_payload(attachments, vk_user_id)
    return photos or None


# Загружает photo-вложения напрямую из сообщения VK по его message ID и сохраняет их локально.
def extract_photo_attachments_from_message(vk, vk_user_id, message_id):
    if not message_id:
        return [], False
    try:
        response = vk.messages.getById(message_ids=message_id)
    except Exception:
        return [], False
    items = response.get("items") or []
    if not items:
        return [], False
    return extract_photo_payload(items[0].get("attachments") or [], vk_user_id)


# Преобразует сохраненные локальные файлы или старые VK token в строку attachment для VK.
def build_photo_attachment(vk_or_profile, profile=None, peer_id=None):
    vk = vk_or_profile if profile is not None else _vk_api_method
    profile = profile or vk_or_profile
    attachments = []
    local_photo_entries = []
    normalized_photos = []
    for raw_photo in profile.get("photos", []):
        photo = _normalize_photo_entry(raw_photo)
        normalized_photos.append(photo)
        token = str(photo.get("vk_token") or "").strip()
        path = str(photo.get("path") or "").strip()
        if not token and not path:
            continue
        absolute_path = resolve_local_photo_path(path) if _is_local_photo_reference(path) else None
        has_local_file = bool(absolute_path and absolute_path.exists())
        if token and (has_local_file or _is_vk_photo_token_valid(vk, token)):
            if not token.startswith("photo"):
                token = f"photo{token}"
            attachments.append(token)
            continue
        if has_local_file:
            local_photo_entries.append((photo, str(absolute_path)))
            continue
        default_photo_path = resolve_default_photo_path()
        if default_photo_path:
            local_photo_entries.append((photo, str(default_photo_path)))

    if local_photo_entries:
        if vk is None:
            return ",".join(attachments) or None
        uploaded = VkUpload(vk).photo_messages([absolute_path for _, absolute_path in local_photo_entries], peer_id=peer_id)
        for (photo, _), item in zip(local_photo_entries, uploaded):
            owner_id = item.get("owner_id")
            photo_id = item.get("id")
            access_key = item.get("access_key")
            if owner_id is None or photo_id is None:
                continue
            token_value = f"{owner_id}_{photo_id}"
            if access_key:
                token_value = f"{token_value}_{access_key}"
            photo["vk_token"] = token_value
            attachments.append(f"photo{token_value}")

    profile["photos"] = normalized_photos
    if profile.get("vk_user_id") is not None:
        save_photos(profile["vk_user_id"], normalized_photos)

    return ",".join(attachments) or None


# Сохраняет одно простое поле анкеты и в памяти, и в базе данных.
def save_text_field(user, field, value):
    user[field] = value
    save_profile_fields(user["vk_user_id"], {field: value})


# Сохраняет текущий выбранный набор игр из runtime-состояния в базу.
def save_games_state(user):
    user["games"] = selected_games(user)
    save_games(user["vk_user_id"], user["games"])


# Сохраняет текущий набор фотографий из runtime-состояния в базу.
def save_photos_state(user, photos):
    previous_photos = [_normalize_photo_entry(photo) for photo in user.get("photos", [])]
    user["photos"] = [_normalize_photo_entry(photo) for photo in photos[:3]]
    save_photos(user["vk_user_id"], user["photos"])
    delete_local_photo_files(
        [
            photo for photo in previous_photos
            if photo not in user["photos"] and _is_local_photo_reference(photo.get("path"))
        ]
    )


# Отправляет inline-клавиатуру для выбора игр.
def show_games_picker(user, send):
    send(format_games_buttons_message(), keyboard=get_games_keyboard(user))


# Запускает шаг выбора игр и при необходимости скрывает предыдущую reply-клавиатуру.
def start_games_flow(user, send, clear_reply_keyboard=False):
    user["step"] = STATE_GAMES
    if clear_reply_keyboard:
        send(format_games_picker_prompt(), keyboard=EMPTY_KEYBOARD)
    else:
        send(format_games_picker_prompt())
    show_games_picker(user, send)


# Повторно активирует ранее отключенную анкету при возвращении к просмотру.
def reactivate_profile_if_needed(user):
    if user.get("is_active") == 0:
        save_text_field(user, "is_active", 1)


# Проверяет, заполнены ли все обязательные поля анкеты.
def is_profile_complete(user):
    return all(
        [
            user.get("name"),
            user.get("age"),
            user.get("gender"),
            user.get("city"),
            user.get("looking_for"),
            user.get("uses_microphone") in (0, 1, False, True),
            games_display(user),
            user.get("about"),
            user.get("photos"),
        ]
    )


# Отправляет следующий обязательный шаг регистрации для незаполненной анкеты.
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
    if user.get("uses_microphone") not in (0, 1, False, True):
        user["step"] = STATE_REG_MICROPHONE
        send(texts.MSG_MICROPHONE_PROMPT, keyboard=get_microphone_keyboard())
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


# Показывает пользователю его заполненную анкету с клавиатурой обзора.
def show_review(user, send):
    user["step"] = STATE_REVIEW
    user["browse_mode"] = "new"
    user["history_candidate_action"] = None
    user["history_cursor_id"] = None
    user["history_cursor_created_at"] = None
    send(
        format_profile(user, include_review=True),
        keyboard=get_review_keyboard(user),
        attachment=build_photo_attachment(user),
    )


# Формирует текст кандидата для режима просмотра и истории.
def _candidate_browse_text(candidate, viewing_history=False, history_action=None):
    text = format_profile(candidate, include_review=False)
    if viewing_history and history_action == "like":
        text += f"\n\n{texts.MSG_PROFILE_IN_HISTORY_LIKED}"
    return text


# Показывает следующую новую анкету, подходящую текущему пользователю.
def show_next_candidate(vk_user_id, send):
    user = users[vk_user_id]
    reactivate_profile_if_needed(user)
    candidate = get_random_candidate(vk_user_id, user)
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


# Повторно показывает текущую анкету в просмотре или подгружает следующую при необходимости.
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


# Открывает предыдущее взаимодействие из режима истории.
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


# Возвращает следующий профиль с входящим pending like для пользователя.
def get_pending_like_profile(vk_user_id):
    return get_next_pending_like_profile(vk_user_id)


# Проверяет, есть ли у пользователя сейчас необработанные входящие лайки.
def has_pending_likes(vk_user_id):
    return has_pending_like_for_target(vk_user_id)


# Заполняет пустые поля анкеты данными, полученными из VK-профиля.
def apply_vk_defaults(vk_user_id, user):
    vk_profile = user.get("vk_profile") or {}
    updates = {}
    for field in ("name", "age", "city", "gender"):
        if not user.get(field) and vk_profile.get(field):
            user[field] = vk_profile[field]
            updates[field] = vk_profile[field]
    if updates:
        save_profile_fields(vk_user_id, updates)
