-- ban_profile.sql
-- Блокирует анкету пользователя по его VK ID и сохраняет причину блокировки.
-- Укажи VK ID пользователя в переменной @vk_user_id и причину в @ban_reason.

USE goparty_bot;

SET @vk_user_id = '542646585';
SET @ban_reason = 'Жалобы / нарушение правил';

UPDATE profiles p
JOIN users u ON u.id = p.user_id
SET p.is_banned = 1,
    p.is_active = 0,
    p.banned_at = NOW(),
    p.ban_reason = @ban_reason
WHERE u.vk_user_id = @vk_user_id;
