-- seed_friend_profiles.sql
-- Р—Р°РїРѕР»РЅСЏРµС‚ Р‘Р” goparty_bot С‚РѕР»СЊРєРѕ Р°РЅРєРµС‚Р°РјРё СЂРµР°Р»СЊРЅС‹С… РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№-РґСЂСѓР·РµР№.
-- РСЃРїРѕР»СЊР·СѓР№ РїРѕСЃР»Рµ reset_database.sql, РµСЃР»Рё С…РѕС‡РµС€СЊ С‚РµСЃС‚РёСЂРѕРІР°С‚СЊ Р±РѕС‚Р° Р±РµР· С‚РµСЃС‚РѕРІС‹С… Р±РѕС‚РѕРІ.

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

INSERT INTO profiles (user_id, name, age, city, about, gender, is_active)
SELECT id, 'Sergey', 23, 'РРІР°РЅРѕРІРѕ', 'РќРµС‚', 'male', 1
FROM users WHERE vk_user_id = '253285471';

INSERT INTO profiles (user_id, name, age, city, about, gender, is_active)
SELECT id, 'Р›РµРѕРЅРёРґ', 21, 'РњРѕСЃРєРІР°', 'РРіСЂСѓС€РєР°', 'male', 1
FROM users WHERE vk_user_id = '214882562';

INSERT INTO profiles (user_id, name, age, city, about, gender, is_active)
SELECT id, 'Р•Р»РёР·Р°РІРµС‚Р°', 23, 'РўСЋРјРµРЅСЊ', 'РЇ РљРёСЂРёР»Р»', 'female', 1
FROM users WHERE vk_user_id = '209282144';

INSERT INTO profiles (user_id, name, age, city, about, gender, is_active)
SELECT id, 'РџРѕР»РёРЅР°', 21, 'РљРѕСЂРѕР»С‘РІ', 'РљСѓРєР°СЂРµРєСѓ', 'female', 1
FROM users WHERE vk_user_id = '367019544';

INSERT INTO profiles (user_id, name, age, city, about, gender, is_active)
SELECT id, 'РљРёСЂРёР»Р»', 22, 'РЎС‹РєС‚С‹РІРєР°СЂ', 'РёРЅС„РѕСЂРјР°С‚РёРІРЅРѕРµ РѕРїРёСЃР°РЅРёРµ Р°РЅРєРµС‚С‹ рџ–вєрџ№', 'male', 1
FROM users WHERE vk_user_id = '186649696';

INSERT INTO profiles (user_id, name, age, city, about, gender, is_active)
SELECT id, 'РђР»Р°РЅ', 22, 'РќР°Р»СЊС‡РёРє', 'РєРµСЂРёР»', 'male', 1
FROM users WHERE vk_user_id = '441225203';

INSERT INTO profiles (user_id, name, age, city, about, gender, is_active)
SELECT id, 'РђРЅРґСЂРµР№', 22, 'РќРѕРІРѕРєСѓР·РЅРµС†Рє', 'Р’РѕРІРѕРѕРІ', 'male', 1
FROM users WHERE vk_user_id = '173997528';

INSERT INTO profiles (user_id, name, age, city, about, gender, is_active)
SELECT id, 'РњР°РєР°СЂ', 23, 'РЎС‹РєС‚С‹РІРєР°СЂ', 'РЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏМЃСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏРЇСЏСЏСЏСЏСЏСЏСЏСЏСЏСЏ', 'male', 1
FROM users WHERE vk_user_id = '203397534';

INSERT INTO user_filters (user_id, looking_for)
SELECT id, 'any' FROM users;

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

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239052', 1
FROM users WHERE vk_user_id = '253285471';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239053', 2
FROM users WHERE vk_user_id = '253285471';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239054', 3
FROM users WHERE vk_user_id = '253285471';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239056', 1
FROM users WHERE vk_user_id = '214882562';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239057', 2
FROM users WHERE vk_user_id = '214882562';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239058', 3
FROM users WHERE vk_user_id = '214882562';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239055', 1
FROM users WHERE vk_user_id = '209282144';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239050', 1
FROM users WHERE vk_user_id = '367019544';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239059', 1
FROM users WHERE vk_user_id = '186649696';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239066', 1
FROM users WHERE vk_user_id = '441225203';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239067', 2
FROM users WHERE vk_user_id = '441225203';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239068', 3
FROM users WHERE vk_user_id = '441225203';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239064', 1
FROM users WHERE vk_user_id = '173997528';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239070', 1
FROM users WHERE vk_user_id = '203397534';

INSERT INTO user_photos (user_id, photo_path, vk_photo_token, sort_order)
SELECT id, '', '-237423541_457239071', 2
FROM users WHERE vk_user_id = '203397534';

COMMIT;
