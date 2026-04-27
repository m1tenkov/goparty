-- reset_database.sql
-- Полная очистка данных в БД goparty_bot.
-- Этот скрипт удаляет все строки из рабочих таблиц бота,
-- но НЕ удаляет сами таблицы и их структуру.
-- Используй его перед новым тестом, если хочешь начать с чистой БД.

USE goparty_bot;

DELETE FROM matches;
DELETE FROM interactions;
DELETE FROM pending_likes;
DELETE FROM user_photos;
DELETE FROM user_games;
DELETE FROM profiles;
DELETE FROM users;

-- Если у тебя есть старая резервная таблица после миграции, можно очистить и ее:
-- DELETE FROM users_legacy;

ALTER TABLE matches AUTO_INCREMENT = 1;
ALTER TABLE interactions AUTO_INCREMENT = 1;
ALTER TABLE pending_likes AUTO_INCREMENT = 1;
ALTER TABLE user_photos AUTO_INCREMENT = 1;
ALTER TABLE users AUTO_INCREMENT = 1;
