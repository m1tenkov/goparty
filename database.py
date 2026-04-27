# -*- coding: utf-8 -*-

import json

import pymysql

from config import DB_CA_PATH, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


connection_kwargs = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}
if DB_CA_PATH:
    connection_kwargs["ssl"] = {"ca": str(DB_CA_PATH)}


# Подключение к MySQL.
connection = pymysql.connect(**connection_kwargs)


def _add_column_if_missing(cursor, table_name, column_name, column_definition):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
          AND column_name = %s
        LIMIT 1
        """,
        (DB_NAME, table_name, column_name),
    )
    if cursor.fetchone() is None:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def ensure_runtime_schema():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_likes (
                id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
                liker_user_id BIGINT(20) UNSIGNED NOT NULL,
                target_user_id BIGINT(20) UNSIGNED NOT NULL,
                like_message TEXT DEFAULT NULL,
                response_action ENUM('like', 'dislike') DEFAULT NULL,
                notified_at TIMESTAMP NULL DEFAULT NULL,
                responded_at TIMESTAMP NULL DEFAULT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uq_pending_like_pair (liker_user_id, target_user_id),
                KEY idx_pending_likes_target_pending (target_user_id, responded_at, created_at),
                CONSTRAINT fk_pending_likes_liker FOREIGN KEY (liker_user_id) REFERENCES users (id) ON DELETE CASCADE,
                CONSTRAINT fk_pending_likes_target FOREIGN KEY (target_user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        _add_column_if_missing(cursor, "pending_likes", "like_message", "TEXT DEFAULT NULL")
        _add_column_if_missing(cursor, "profiles", "is_banned", "TINYINT(1) NOT NULL DEFAULT 0")
        _add_column_if_missing(cursor, "profiles", "banned_at", "TIMESTAMP NULL DEFAULT NULL")
        _add_column_if_missing(cursor, "profiles", "ban_reason", "VARCHAR(255) DEFAULT NULL")
        _add_column_if_missing(cursor, "profiles", "delivery_disabled", "TINYINT(1) NOT NULL DEFAULT 0")
        _add_column_if_missing(cursor, "profiles", "delivery_error_code", "VARCHAR(32) DEFAULT NULL")
        _add_column_if_missing(cursor, "profiles", "delivery_error_at", "TIMESTAMP NULL DEFAULT NULL")
        _add_column_if_missing(cursor, "profiles", "games_step_completed", "TINYINT(1) NOT NULL DEFAULT 0")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id BIGINT(20) UNSIGNED NOT NULL,
                session_json LONGTEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id),
                CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
    connection.commit()


GAME_CODES = (
    "dota2",
    "cs2",
    "minecraft",
    "mlbb",
    "valorant",
    "pubg",
    "dbd",
    "genshin",
)
GAME_TITLES = {
    "dota2": "Dota 2",
    "cs2": "CS2",
    "minecraft": "Minecraft",
    "mlbb": "MLBB",
    "valorant": "Valorant",
    "pubg": "PUBG",
    "dbd": "Dead by Daylight",
    "genshin": "Genshin Impact",
}


def _db_vk_user_id(vk_user_id):
    return str(vk_user_id)


def _public_vk_user_id(vk_user_id):
    value = str(vk_user_id)
    return int(value) if value.isdigit() else value


def is_bot_vk_user_id(vk_user_id):
    return str(vk_user_id).startswith("бот-")


# Создаёт пользователя в таблице users, если его там ещё нет.
def get_or_create_user(vk_user_id):
    db_vk_user_id = _db_vk_user_id(vk_user_id)
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, vk_user_id FROM users WHERE vk_user_id = %s", (db_vk_user_id,))
        row = cursor.fetchone()
        if row:
            row["vk_user_id"] = _public_vk_user_id(row["vk_user_id"])
            return row

        cursor.execute("INSERT INTO users (vk_user_id) VALUES (%s)", (db_vk_user_id,))
        connection.commit()
        return {"id": cursor.lastrowid, "vk_user_id": _public_vk_user_id(db_vk_user_id)}


# Ищет внутренний user_id по vk_user_id.
def get_user_row_by_vk_user_id(vk_user_id):
    db_vk_user_id = _db_vk_user_id(vk_user_id)
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, vk_user_id FROM users WHERE vk_user_id = %s", (db_vk_user_id,))
        row = cursor.fetchone()
        if row:
            row["vk_user_id"] = _public_vk_user_id(row["vk_user_id"])
        return row


# Возвращает выбранные пользователем игры из связующей таблицы.
def _load_game_codes(db_user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT g.code
            FROM user_games ug
            JOIN games g ON g.id = ug.game_id
            WHERE ug.user_id = %s
            ORDER BY g.id
            """,
            (db_user_id,),
        )
        return [row["code"] for row in cursor.fetchall()]


# Возвращает сохранённые фото пользователя в нужном порядке.
def _load_photos(db_user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT photo_token
            FROM user_photos
            WHERE user_id = %s
            ORDER BY sort_order
            """,
            (db_user_id,),
        )
        return [row["photo_token"] for row in cursor.fetchall()]


# Собирает единый профиль пользователя из нескольких таблиц.
def _build_profile(base_row):
    if not base_row:
        return None

    profile = {
        "db_user_id": base_row["db_user_id"],
        "vk_user_id": _public_vk_user_id(base_row["vk_user_id"]),
        "name": base_row.get("name"),
        "age": base_row.get("age"),
        "city": base_row.get("city"),
        "about": base_row.get("about"),
        "gender": base_row.get("gender"),
        "looking_for": base_row.get("looking_for"),
        "is_active": base_row.get("is_active", 1),
        "is_banned": base_row.get("is_banned", 0),
        "banned_at": base_row.get("banned_at"),
        "ban_reason": base_row.get("ban_reason"),
        "delivery_disabled": base_row.get("delivery_disabled", 0),
        "delivery_error_code": base_row.get("delivery_error_code"),
        "delivery_error_at": base_row.get("delivery_error_at"),
        "games_step_completed": base_row.get("games_step_completed", 0),
        "games": _load_game_codes(base_row["db_user_id"]),
        "photos": _load_photos(base_row["db_user_id"]),
    }

    for code in GAME_CODES:
        profile[code] = 1 if code in profile["games"] else 0

    return profile


# Загружает полный профиль пользователя по его VK ID.
def get_profile_by_vk_user_id(vk_user_id):
    db_vk_user_id = _db_vk_user_id(vk_user_id)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                u.id AS db_user_id,
                u.vk_user_id,
                p.name,
                p.age,
                p.city,
                p.about,
                p.gender,
                p.looking_for,
                p.is_active,
                p.is_banned,
                p.banned_at,
                p.ban_reason,
                p.delivery_disabled,
                p.delivery_error_code,
                p.delivery_error_at,
                p.games_step_completed
            FROM users u
            LEFT JOIN profiles p ON p.user_id = u.id
            WHERE u.vk_user_id = %s
            """,
            (db_vk_user_id,),
        )
        return _build_profile(cursor.fetchone())


def clear_received_dislikes(vk_user_id):
    user_row = get_user_row_by_vk_user_id(vk_user_id)
    if not user_row:
        return 0

    with connection.cursor() as cursor:
        deleted = cursor.execute(
            """
            DELETE FROM interactions
            WHERE to_user_id = %s
              AND action = 'dislike'
            """,
            (user_row["id"],),
        )
    connection.commit()
    return deleted


def _load_interacted_target_ids(db_user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT to_user_id
            FROM interactions
            WHERE from_user_id = %s
              AND action IN ('like', 'dislike')
            """,
            (db_user_id,),
        )
        return {row["to_user_id"] for row in cursor.fetchall()}


def has_pending_like_for_target(vk_user_id):
    user_row = get_user_row_by_vk_user_id(vk_user_id)
    if not user_row:
        return False

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM pending_likes
            WHERE target_user_id = %s
              AND responded_at IS NULL
            LIMIT 1
            """,
            (user_row["id"],),
        )
        return cursor.fetchone() is not None


def get_next_pending_like_profile(vk_user_id):
    user_row = get_user_row_by_vk_user_id(vk_user_id)
    if not user_row:
        return None

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.vk_user_id, pl.like_message
            FROM pending_likes pl
            JOIN users u ON u.id = pl.liker_user_id
            JOIN profiles p ON p.user_id = u.id
            WHERE pl.target_user_id = %s
              AND pl.responded_at IS NULL
              AND p.is_active = 1
              AND p.is_banned = 0
              AND COALESCE(p.delivery_disabled, 0) = 0
            ORDER BY pl.created_at, pl.id
            LIMIT 1
            """,
            (user_row["id"],),
        )
        row = cursor.fetchone()

    if not row:
        return None

    profile = get_profile_by_vk_user_id(row["vk_user_id"])
    if profile is not None:
        profile["like_message"] = row.get("like_message")
    return profile


def enqueue_pending_like(liker_vk_user_id, target_vk_user_id, like_message=None):
    liker_user = get_or_create_user(liker_vk_user_id)
    target_user = get_or_create_user(target_vk_user_id)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS pending_count
            FROM pending_likes
            WHERE target_user_id = %s
              AND responded_at IS NULL
            """,
            (target_user["id"],),
        )
        pending_before = cursor.fetchone()["pending_count"]
        inserted = cursor.execute(
            """
            INSERT IGNORE INTO pending_likes (liker_user_id, target_user_id, like_message)
            VALUES (%s, %s, %s)
            """,
            (liker_user["id"], target_user["id"], (like_message or "").strip() or None),
        )
    connection.commit()
    return inserted == 1 and pending_before == 0


def mark_pending_like_notified(target_vk_user_id, liker_vk_user_id):
    target_user = get_user_row_by_vk_user_id(target_vk_user_id)
    liker_user = get_user_row_by_vk_user_id(liker_vk_user_id)
    if not target_user or not liker_user:
        return False

    with connection.cursor() as cursor:
        updated = cursor.execute(
            """
            UPDATE pending_likes
            SET notified_at = COALESCE(notified_at, CURRENT_TIMESTAMP)
            WHERE liker_user_id = %s
              AND target_user_id = %s
              AND responded_at IS NULL
            """,
            (liker_user["id"], target_user["id"]),
        )
    connection.commit()
    return updated > 0


def resolve_pending_like(target_vk_user_id, liker_vk_user_id, response_action):
    if response_action not in ("like", "dislike"):
        raise ValueError("Unsupported response action")

    target_user = get_user_row_by_vk_user_id(target_vk_user_id)
    liker_user = get_user_row_by_vk_user_id(liker_vk_user_id)
    if not target_user or not liker_user:
        return False

    with connection.cursor() as cursor:
        updated = cursor.execute(
            """
            UPDATE pending_likes
            SET response_action = %s,
                responded_at = CURRENT_TIMESTAMP,
                notified_at = COALESCE(notified_at, CURRENT_TIMESTAMP)
            WHERE liker_user_id = %s
              AND target_user_id = %s
              AND responded_at IS NULL
            """,
            (response_action, liker_user["id"], target_user["id"]),
        )
    connection.commit()
    return updated > 0


# Сохраняет простые поля анкеты в profiles.
def save_profile_fields(vk_user_id, fields):
    if not fields:
        return False

    user_row = get_or_create_user(vk_user_id)
    db_user_id = user_row["id"]
    previous_profile = get_profile_by_vk_user_id(vk_user_id) or {}

    allowed = {
        key: value
        for key, value in fields.items()
        if key in {"name", "age", "city", "about", "gender", "looking_for", "is_active"}
    }
    if not allowed:
        return False

    columns = ["user_id", *allowed.keys()]
    values = [db_user_id, *allowed.values()]
    updates = ", ".join(f"{column} = VALUES({column})" for column in allowed.keys())

    with connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO profiles ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))}) "
            f"ON DUPLICATE KEY UPDATE {updates}",
            values,
        )
    connection.commit()

    changed_fields = {
        key for key, value in allowed.items()
        if previous_profile.get(key) != value
    }
    if changed_fields & {"name", "age", "city", "about", "gender"}:
        clear_received_dislikes(vk_user_id)

    return True


def mark_profile_delivery_unavailable(vk_user_id, error_code=None):
    user_row = get_or_create_user(vk_user_id)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO profiles (user_id, delivery_disabled, delivery_error_code, delivery_error_at)
            VALUES (%s, 1, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                delivery_disabled = 1,
                delivery_error_code = VALUES(delivery_error_code),
                delivery_error_at = VALUES(delivery_error_at)
            """,
            (user_row["id"], str(error_code)[:32] if error_code else None),
        )
    connection.commit()
    return True


def reset_profile_delivery_status(vk_user_id):
    user_row = get_user_row_by_vk_user_id(vk_user_id)
    if not user_row:
        return False

    with connection.cursor() as cursor:
        updated = cursor.execute(
            """
            UPDATE profiles
            SET delivery_disabled = 0,
                delivery_error_code = NULL,
                delivery_error_at = NULL
            WHERE user_id = %s
              AND (delivery_disabled <> 0 OR delivery_error_code IS NOT NULL OR delivery_error_at IS NOT NULL)
            """,
            (user_row["id"],),
        )
    connection.commit()
    return updated > 0


def load_runtime_state(vk_user_id):
    user_row = get_user_row_by_vk_user_id(vk_user_id)
    if not user_row:
        return {}

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT session_json
            FROM user_sessions
            WHERE user_id = %s
            """,
            (user_row["id"],),
        )
        row = cursor.fetchone()

    if not row or not row.get("session_json"):
        return {}

    try:
        return json.loads(row["session_json"])
    except json.JSONDecodeError:
        return {}


def save_runtime_state(vk_user_id, state):
    user_row = get_or_create_user(vk_user_id)

    with connection.cursor() as cursor:
        if not state:
            cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_row["id"],))
            connection.commit()
            return True

        payload = json.dumps(state, ensure_ascii=False)
        cursor.execute(
            """
            INSERT INTO user_sessions (user_id, session_json)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE session_json = VALUES(session_json)
            """,
            (user_row["id"], payload),
        )
    connection.commit()
    return True


def delete_user_data(vk_user_id):
    user_row = get_user_row_by_vk_user_id(vk_user_id)
    if not user_row:
        return False

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_row["id"],))
    connection.commit()
    return True


def get_previous_interaction(vk_user_id, before_created_at=None, before_id=None):
    user_row = get_user_row_by_vk_user_id(vk_user_id)
    if not user_row:
        return None

    query = """
        SELECT
            i.id,
            i.action,
            i.created_at,
            u.vk_user_id
        FROM interactions i
        JOIN users u ON u.id = i.to_user_id
        WHERE i.from_user_id = %s
    """
    params = [user_row["id"]]

    if before_created_at is not None and before_id is not None:
        query += """
          AND (
                i.created_at < %s
                OR (i.created_at = %s AND i.id < %s)
          )
        """
        params.extend([before_created_at, before_created_at, before_id])

    query += """
        ORDER BY i.created_at DESC, i.id DESC
        LIMIT 1
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()

    if not row:
        return None

    profile = get_profile_by_vk_user_id(row["vk_user_id"]) or {"vk_user_id": _public_vk_user_id(row["vk_user_id"])}
    return {
        "id": row["id"],
        "action": row["action"],
        "created_at": row["created_at"].isoformat(sep=" ") if row.get("created_at") else None,
        "profile": profile,
    }


# Полностью пересохраняет список игр пользователя.
def save_games(vk_user_id, selected_game_codes):
    user_row = get_or_create_user(vk_user_id)
    db_user_id = user_row["id"]
    previous_profile = get_profile_by_vk_user_id(vk_user_id) or {}
    selected_game_codes = [code for code in selected_game_codes if code in GAME_CODES]
    previous_games = set(previous_profile.get("games", []))

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO profiles (user_id, games_step_completed)
            VALUES (%s, 1)
            ON DUPLICATE KEY UPDATE games_step_completed = VALUES(games_step_completed)
            """,
            (db_user_id,),
        )
        cursor.execute("DELETE FROM user_games WHERE user_id = %s", (db_user_id,))

        if selected_game_codes:
            cursor.execute(
                f"SELECT id, code FROM games WHERE code IN ({', '.join(['%s'] * len(selected_game_codes))})",
                selected_game_codes,
            )
            game_rows = cursor.fetchall()
            pairs = [(db_user_id, row["id"]) for row in game_rows]
            if pairs:
                cursor.executemany(
                    "INSERT INTO user_games (user_id, game_id) VALUES (%s, %s)",
                    pairs,
                )

    connection.commit()

    if previous_games != set(selected_game_codes):
        clear_received_dislikes(vk_user_id)

    return True


# Полностью пересохраняет до трёх фото пользователя.
def save_photos(vk_user_id, photos):
    user_row = get_or_create_user(vk_user_id)
    db_user_id = user_row["id"]
    previous_profile = get_profile_by_vk_user_id(vk_user_id) or {}
    photos = list(photos[:3])

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM user_photos WHERE user_id = %s", (db_user_id,))
        if photos:
            cursor.executemany(
                "INSERT INTO user_photos (user_id, photo_token, sort_order) VALUES (%s, %s, %s)",
                [(db_user_id, photo, index + 1) for index, photo in enumerate(photos)],
            )
    connection.commit()

    if list(previous_profile.get("photos", [])) != photos:
        clear_received_dislikes(vk_user_id)

    return True


# Ищет следующую подходящую анкету для показа пользователю.
def get_random_candidate(vk_user_id):
    current_profile = get_profile_by_vk_user_id(vk_user_id)
    if not current_profile:
        return None

    current_db_user_id = current_profile["db_user_id"]
    current_gender = current_profile.get("gender")
    current_looking_for = current_profile.get("looking_for")
    current_age = current_profile.get("age")

    query = """
        SELECT
            u.id AS db_user_id,
            u.vk_user_id,
            COUNT(DISTINCT current_ug.game_id) AS shared_games,
            ABS(COALESCE(p.age, 0) - %s) AS age_distance,
            u.created_at AS user_created_at
        FROM users u
        JOIN profiles p ON p.user_id = u.id
        LEFT JOIN user_games candidate_ug ON candidate_ug.user_id = u.id
        LEFT JOIN user_games current_ug
            ON current_ug.user_id = %s
           AND current_ug.game_id = candidate_ug.game_id
        WHERE u.id <> %s
          AND p.is_active = 1
          AND p.is_banned = 0
          AND COALESCE(p.delivery_disabled, 0) = 0
          AND p.name IS NOT NULL
          AND p.age IS NOT NULL
          AND p.city IS NOT NULL
          AND p.gender IS NOT NULL
          AND p.looking_for IS NOT NULL
          AND p.about IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM interactions i
              WHERE i.from_user_id = %s
                AND i.to_user_id = u.id
                AND i.action IN ('like', 'dislike')
          )
          AND NOT EXISTS (
              SELECT 1
              FROM interactions i
              WHERE i.from_user_id = u.id
                AND i.to_user_id = %s
                AND i.action = 'dislike'
          )
    """
    params = [
        int(current_age) if current_age is not None else 0,
        current_db_user_id,
        current_db_user_id,
        current_db_user_id,
        current_db_user_id,
    ]

    if current_looking_for in ("male", "female"):
        query += " AND p.gender = %s"
        params.append(current_looking_for)

    if current_gender in ("male", "female"):
        query += " AND (p.looking_for = 'any' OR p.looking_for = %s)"
        params.append(current_gender)

    query += """
        GROUP BY u.id, u.vk_user_id, p.age, u.created_at
        ORDER BY shared_games DESC, age_distance ASC, user_created_at DESC, u.id DESC
        LIMIT 1
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        candidate_row = cursor.fetchone()

    if not candidate_row:
        return None

    return get_profile_by_vk_user_id(candidate_row["vk_user_id"])


# Сохраняет лайк или дизлайк и проверяет, произошёл ли взаимный лайк.
def record_interaction(from_vk_user_id, to_vk_user_id, action):
    if action not in ("like", "dislike"):
        raise ValueError("Unsupported action")
    if from_vk_user_id == to_vk_user_id:
        return {"matched": False, "target_profile": get_profile_by_vk_user_id(to_vk_user_id)}

    from_user = get_or_create_user(from_vk_user_id)
    to_user = get_or_create_user(to_vk_user_id)
    matched = False

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO interactions (from_user_id, to_user_id, action)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE action = VALUES(action), created_at = CURRENT_TIMESTAMP
            """,
            (from_user["id"], to_user["id"], action),
        )

        if action == "like":
            cursor.execute(
                """
                SELECT 1
                FROM interactions
                WHERE from_user_id = %s AND to_user_id = %s AND action = 'like'
                LIMIT 1
                """,
                (to_user["id"], from_user["id"]),
            )
            matched = cursor.fetchone() is not None
            if matched:
                user1_id = min(from_user["id"], to_user["id"])
                user2_id = max(from_user["id"], to_user["id"])
                cursor.execute(
                    "INSERT IGNORE INTO matches (user1_id, user2_id) VALUES (%s, %s)",
                    (user1_id, user2_id),
                )

    connection.commit()
    return {
        "matched": matched,
        "target_profile": get_profile_by_vk_user_id(to_vk_user_id),
    }


ensure_runtime_schema()
