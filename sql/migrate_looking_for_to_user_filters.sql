-- migrate_looking_for_to_user_filters.sql
-- Moves the "who I am looking for" setting from profiles to user_filters.
-- Adds user_filters.looking_for, copies data from profiles.looking_for,
-- then removes profiles.looking_for. Safe to run more than once.

USE goparty_bot;

SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'user_filters'
      AND column_name = 'looking_for'
);

SET @ddl := IF(
    @column_exists = 0,
    'ALTER TABLE user_filters ADD COLUMN looking_for ENUM(''male'', ''female'', ''any'') DEFAULT NULL AFTER user_id',
    'SELECT 1'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @profile_column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'profiles'
      AND column_name = 'looking_for'
);

SET @migrate_sql := IF(
    @profile_column_exists = 1,
    'INSERT INTO user_filters (user_id, looking_for)
     SELECT user_id, looking_for
     FROM profiles
     WHERE looking_for IS NOT NULL
     ON DUPLICATE KEY UPDATE
         looking_for = COALESCE(user_filters.looking_for, VALUES(looking_for))',
    'SELECT 1'
);

PREPARE stmt FROM @migrate_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @drop_sql := IF(
    @profile_column_exists = 1,
    'ALTER TABLE profiles DROP COLUMN looking_for',
    'SELECT 1'
);

PREPARE stmt FROM @drop_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
