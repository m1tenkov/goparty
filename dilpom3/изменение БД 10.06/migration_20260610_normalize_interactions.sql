USE goparty_bot;

SET @sql = (
    SELECT IF(
        EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'interactions'
              AND column_name = 'like_message'
        ),
        'SELECT ''interactions.like_message already exists'' AS status',
        'ALTER TABLE interactions ADD COLUMN like_message TEXT NULL AFTER action'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
    SELECT IF(
        EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = 'pending_likes'
        ),
        'INSERT INTO interactions (from_user_id, to_user_id, action, like_message, created_at)
         SELECT liker_user_id, target_user_id, ''like'', like_message, created_at
         FROM pending_likes
         ON DUPLICATE KEY UPDATE
             action = ''like'',
             like_message = COALESCE(interactions.like_message, VALUES(like_message))',
        'SELECT ''pending_likes already migrated'' AS status'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
    SELECT IF(
        EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = 'pending_likes'
        ),
        'DROP TABLE pending_likes',
        'SELECT ''pending_likes table does not exist'' AS status'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
    SELECT IF(
        EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = 'matches'
        ),
        'DROP TABLE matches',
        'SELECT ''matches table does not exist'' AS status'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
    SELECT IF(
        EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'profiles'
              AND column_name = 'looking_for'
        ),
        'INSERT INTO user_filters (user_id, looking_for)
         SELECT user_id, looking_for
         FROM profiles
         WHERE looking_for IS NOT NULL
         ON DUPLICATE KEY UPDATE
             looking_for = COALESCE(user_filters.looking_for, VALUES(looking_for))',
        'SELECT ''profiles.looking_for already migrated'' AS status'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
    SELECT IF(
        EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'profiles'
              AND column_name = 'looking_for'
        ),
        'ALTER TABLE profiles DROP COLUMN looking_for',
        'SELECT ''profiles.looking_for does not exist'' AS status'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
    SELECT IF(
        EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'user_games'
              AND column_name = 'created_at'
        ),
        'ALTER TABLE user_games DROP COLUMN created_at',
        'SELECT ''user_games.created_at does not exist'' AS status'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
    SELECT IF(
        EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'user_photos'
              AND column_name = 'created_at'
        ),
        'ALTER TABLE user_photos DROP COLUMN created_at',
        'SELECT ''user_photos.created_at does not exist'' AS status'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
    SELECT IF(
        EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'profiles'
              AND column_name = 'games_step_completed'
        ),
        'ALTER TABLE profiles DROP COLUMN games_step_completed',
        'SELECT ''profiles.games_step_completed does not exist'' AS status'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE profiles MODIFY is_active TINYINT(1) NOT NULL DEFAULT 0;

UPDATE profiles p
SET p.is_active = 0
WHERE p.is_active = 1
  AND (
      p.name IS NULL
      OR p.age IS NULL
      OR p.city IS NULL
      OR p.gender IS NULL
      OR p.uses_microphone IS NULL
      OR p.about IS NULL
      OR NOT EXISTS (
          SELECT 1
          FROM user_filters uf
          WHERE uf.user_id = p.user_id
            AND uf.looking_for IS NOT NULL
      )
      OR NOT EXISTS (
          SELECT 1
          FROM user_games ug
          WHERE ug.user_id = p.user_id
      )
      OR NOT EXISTS (
          SELECT 1
          FROM user_photos up
          WHERE up.user_id = p.user_id
      )
  );

UPDATE user_sessions
SET session_json = JSON_UNQUOTE(JSON_REMOVE(session_json, '$.games_step_completed'))
WHERE JSON_VALID(session_json)
  AND JSON_CONTAINS_PATH(session_json, 'one', '$.games_step_completed');

SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND table_name IN ('pending_likes', 'matches');

SELECT
    column_name
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name = 'interactions'
  AND column_name = 'like_message';

SELECT
    column_name
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name = 'profiles'
  AND column_name = 'games_step_completed';

SELECT
    column_default
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name = 'profiles'
  AND column_name = 'is_active';

SELECT
    p.user_id
FROM profiles p
WHERE p.is_active = 1
  AND (
      p.name IS NULL
      OR p.age IS NULL
      OR p.city IS NULL
      OR p.gender IS NULL
      OR p.uses_microphone IS NULL
      OR p.about IS NULL
      OR NOT EXISTS (
          SELECT 1
          FROM user_filters uf
          WHERE uf.user_id = p.user_id
            AND uf.looking_for IS NOT NULL
      )
      OR NOT EXISTS (
          SELECT 1
          FROM user_games ug
          WHERE ug.user_id = p.user_id
      )
      OR NOT EXISTS (
          SELECT 1
          FROM user_photos up
          WHERE up.user_id = p.user_id
      )
  );
