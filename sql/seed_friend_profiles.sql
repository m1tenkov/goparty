-- seed_friend_profiles.sql
-- Заполняет БД goparty_bot только анкетами реальных пользователей-друзей.
-- Используй после reset_database.sql, если хочешь тестировать бота без тестовых ботов.

USE goparty_bot;

START TRANSACTION;

INSERT INTO users (vk_user_id)
VALUES
('253285471'),
('214882562'),
('209282144'),
('367019544'),
('186649696'),
('441225203'),
('173997528'),
('203397534');

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Sergey', 23, 'Иваново', 'Нет', 'male', 'any', 1
FROM users WHERE vk_user_id = '253285471';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Леонид', 21, 'Москва', 'Игрушка', 'male', 'any', 1
FROM users WHERE vk_user_id = '214882562';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Елизавета', 23, 'Тюмень', 'Я Кирилл', 'female', 'any', 1
FROM users WHERE vk_user_id = '209282144';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Полина', 21, 'Королёв', 'Кукареку', 'female', 'any', 1
FROM users WHERE vk_user_id = '367019544';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Кирилл', 22, 'Сыктывкар', 'информативное описание анкеты 😖☺😹', 'male', 'any', 1
FROM users WHERE vk_user_id = '186649696';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Алан', 22, 'Нальчик', 'керил', 'male', 'any', 1
FROM users WHERE vk_user_id = '441225203';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Андрей', 22, 'Новокузнецк', 'Вовоов', 'male', 'any', 1
FROM users WHERE vk_user_id = '173997528';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Макар', 23, 'Сыктывкар', 'Яяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяяЯяяя́яяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяяЯяяяяяяяяяя', 'male', 'any', 1
FROM users WHERE vk_user_id = '203397534';

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'minecraft'
WHERE u.vk_user_id = '253285471';

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'dota2'
WHERE u.vk_user_id IN ('214882562', '186649696', '441225203', '203397534');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'cs2'
WHERE u.vk_user_id IN ('214882562', '186649696', '173997528', '203397534');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'minecraft'
WHERE u.vk_user_id IN ('214882562', '186649696', '203397534');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'mlbb'
WHERE u.vk_user_id IN ('214882562', '367019544', '203397534');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'valorant'
WHERE u.vk_user_id IN ('214882562', '367019544', '203397534');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'pubg'
WHERE u.vk_user_id IN ('214882562', '203397534');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'dbd'
WHERE u.vk_user_id IN ('214882562', '203397534');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'genshin'
WHERE u.vk_user_id IN ('214882562', '209282144', '367019544', '203397534');

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239052', 1
FROM users WHERE vk_user_id = '253285471';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239053', 2
FROM users WHERE vk_user_id = '253285471';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239054', 3
FROM users WHERE vk_user_id = '253285471';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239056', 1
FROM users WHERE vk_user_id = '214882562';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239057', 2
FROM users WHERE vk_user_id = '214882562';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239058', 3
FROM users WHERE vk_user_id = '214882562';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239055', 1
FROM users WHERE vk_user_id = '209282144';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239050', 1
FROM users WHERE vk_user_id = '367019544';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239059', 1
FROM users WHERE vk_user_id = '186649696';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239066', 1
FROM users WHERE vk_user_id = '441225203';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239067', 2
FROM users WHERE vk_user_id = '441225203';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239068', 3
FROM users WHERE vk_user_id = '441225203';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239064', 1
FROM users WHERE vk_user_id = '173997528';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239070', 1
FROM users WHERE vk_user_id = '203397534';

INSERT INTO user_photos (user_id, photo_token, sort_order)
SELECT id, '-237423541_457239071', 2
FROM users WHERE vk_user_id = '203397534';

COMMIT;
