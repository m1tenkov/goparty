-- unban_profile.sql
-- Снимает блокировку анкеты пользователя по его VK ID.
-- Укажи VK ID пользователя в переменной @vk_user_id.

USE goparty_bot;

SET @vk_user_id = '542646585';

UPDATE profiles p
JOIN users u ON u.id = p.user_id
SET p.is_banned = 0,
    p.is_active = 1,
    p.banned_at = NULL,
    p.ban_reason = NULL
WHERE u.vk_user_id = @vk_user_id;
