-- reset_history.sql
-- Очистка истории просмотров, лайков, дизлайков, мэтчей и очереди входящих лайков в БД goparty_bot.
-- Анкеты пользователей, фото и игры этот скрипт НЕ удаляет.
-- Используй его, если хочешь заново протестировать выдачу анкет и систему мэтчей.

USE goparty_bot;

DELETE FROM interactions;

ALTER TABLE interactions AUTO_INCREMENT = 1;
