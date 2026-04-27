-- seed_bot_profiles.sql
-- Анкеты ботов для БД goparty_bot.
-- Используй после reset_database.sql, чтобы быстро заполнить базу 15 анкетами для тестов.

USE goparty_bot;

START TRANSACTION;

INSERT INTO users (vk_user_id)
VALUES
('бот-001'),
('бот-002'),
('бот-003'),
('бот-004'),
('бот-005'),
('бот-006'),
('бот-007'),
('бот-008'),
('бот-009'),
('бот-010'),
('бот-011'),
('бот-012'),
('бот-013'),
('бот-014'),
('бот-015');

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Артём', 21, 'Москва', 'Люблю вечерние катки и спокойное общение', 'male', 'female', 1
FROM users WHERE vk_user_id = 'бот-001';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Лиза', 20, 'Санкт-Петербург', 'Ищу тиммейта для совместных игр и общения', 'female', 'male', 1
FROM users WHERE vk_user_id = 'бот-002';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Игорь', 24, 'Казань', 'Чаще всего онлайн после работы', 'male', 'female', 1
FROM users WHERE vk_user_id = 'бот-003';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Соня', 19, 'Екатеринбург', 'Люблю кооп, мемы и уютные разговоры', 'female', 'any', 1
FROM users WHERE vk_user_id = 'бот-004';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Максим', 23, 'Новосибирск', 'Хочу найти девушку для игр и общения', 'male', 'female', 1
FROM users WHERE vk_user_id = 'бот-005';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Алина', 22, 'Краснодар', 'Люблю играть без токсичности и спешки', 'female', 'male', 1
FROM users WHERE vk_user_id = 'бот-006';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Никита', 25, 'Самара', 'Нравятся соревновательные игры и вечерний онлайн', 'male', 'any', 1
FROM users WHERE vk_user_id = 'бот-007';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Катя', 21, 'Пермь', 'Ищу веселую компанию и приятного человека', 'female', 'male', 1
FROM users WHERE vk_user_id = 'бот-008';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Дима', 26, 'Воронеж', 'Люблю голосовой чат и долгие игровые сессии', 'male', 'female', 1
FROM users WHERE vk_user_id = 'бот-009';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Маша', 23, 'Тюмень', 'Хочу найти кого-то близкого по вайбу', 'female', 'any', 1
FROM users WHERE vk_user_id = 'бот-010';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Кирилл', 22, 'Уфа', 'Люблю вечерние рейтинги и нормальный вайб без токсика', 'male', 'female', 1
FROM users WHERE vk_user_id = 'бот-011';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Настя', 19, 'Нижний Новгород', 'Часто играю по вечерам и обожаю кооператив', 'female', 'male', 1
FROM users WHERE vk_user_id = 'бот-012';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Егор', 27, 'Ростов-на-Дону', 'Люблю шутеры, мемы и голосовой чат', 'male', 'female', 1
FROM users WHERE vk_user_id = 'бот-013';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Полина', 24, 'Челябинск', 'Ищу человека для стабильных каток и общения', 'female', 'any', 1
FROM users WHERE vk_user_id = 'бот-014';

INSERT INTO profiles (user_id, name, age, city, about, gender, looking_for, is_active)
SELECT id, 'Влад', 20, 'Омск', 'Люблю быстрые матчи и лёгкое общение без напряга', 'male', 'female', 1
FROM users WHERE vk_user_id = 'бот-015';

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'dota2'
WHERE u.vk_user_id IN ('бот-001', 'бот-003', 'бот-005', 'бот-007', 'бот-009', 'бот-011');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'cs2'
WHERE u.vk_user_id IN ('бот-001', 'бот-007', 'бот-009', 'бот-013', 'бот-015');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'minecraft'
WHERE u.vk_user_id IN ('бот-002', 'бот-004', 'бот-006', 'бот-008', 'бот-010', 'бот-012');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'mlbb'
WHERE u.vk_user_id IN ('бот-004', 'бот-006', 'бот-010', 'бот-014');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'valorant'
WHERE u.vk_user_id IN ('бот-003', 'бот-005', 'бот-007', 'бот-011', 'бот-013');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'pubg'
WHERE u.vk_user_id IN ('бот-011', 'бот-013', 'бот-015');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'dbd'
WHERE u.vk_user_id IN ('бот-012', 'бот-014');

INSERT INTO user_games (user_id, game_id)
SELECT u.id, g.id
FROM users u
JOIN games g ON g.code = 'genshin'
WHERE u.vk_user_id IN ('бот-010', 'бот-012');

COMMIT;
