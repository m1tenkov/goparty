# Структура проекта GoParty

## Общее описание

`GoParty` — VK-бот на Python, который работает через `VK Long Poll`, хранит анкеты и историю взаимодействий в MySQL и поддерживает восстановление пользовательского сценария через runtime-сессии.

Ниже описана актуальная структура репозитория и назначение основных файлов.

## Корень проекта

[main.py](/abs/c:/Projects/VS%20Code/main.py)
Точка входа. Запускает Long Poll, принимает события VK, разделяет `MESSAGE_NEW` и `MESSAGE_EVENT`, логирует длительность обработки и переподключается после ошибок.

[vk_bot.py](/abs/c:/Projects/VS%20Code/vk_bot.py)
Создает VK-сессию, объект API и фабрику `create_longpoll()` для первичного запуска и переподключения.

[config.py](/abs/c:/Projects/VS%20Code/config.py)
Загружает конфигурацию из переменных окружения и файлов в `secrets/`. Читает VK-токен, ID группы, feature-флаги и параметры подключения к MySQL, включая optional SSL CA.

[database.py](/abs/c:/Projects/VS%20Code/database.py)
Слой доступа к БД. Открывает соединение, поддерживает runtime-схему, загружает и сохраняет профили, игры, фотографии, лайки, pending likes, мэтчи, историю взаимодействий и пользовательские сессии.

[logger.py](/abs/c:/Projects/VS%20Code/logger.py)
Настраивает обычный лог `logs/bot.log` и структурированный лог действий `logs/actions.jsonl`. Экспортирует `log_action(...)` и `log_error(...)`.

[requirements.txt](/abs/c:/Projects/VS%20Code/requirements.txt)
Список Python-зависимостей проекта.

[.gitignore](/abs/c:/Projects/VS%20Code/.gitignore)
Исключает логи, секреты и локальные артефакты из Git.

## Папка `bot_handlers`

[bot_handlers/__init__.py](/abs/c:/Projects/VS%20Code/bot_handlers/__init__.py)
Переэкспортирует публичные обработчики `handle_message` и `handle_message_event`.

[bot_handlers/router.py](/abs/c:/Projects/VS%20Code/bot_handlers/router.py)
Главный контроллер диалогов. Здесь находятся:

- маршрутизация сообщений по `step`;
- старт и восстановление сценария;
- сценарии регистрации и редактирования;
- просмотр анкет и история;
- входящие лайки;
- лайк с сообщением;
- жалобы;
- деактивация и сброс анкеты;
- безопасная отправка, редактирование и callback-ответы VK;
- debounce-защита от повторных действий.

[bot_handlers/utils.py](/abs/c:/Projects/VS%20Code/bot_handlers/utils.py)
Вспомогательный слой для runtime-логики. Отвечает за:

- восстановление пользователя из БД и памяти;
- сохранение runtime-состояния в `user_sessions`;
- автозаполнение анкеты данными VK;
- проверку полноты анкеты;
- переходы по обязательным шагам;
- форматирование анкеты;
- извлечение фото из вложений;
- показ текущей, новой и исторической анкеты.

[bot_handlers/constants.py](/abs/c:/Projects/VS%20Code/bot_handlers/constants.py)
Хранит строковые идентификаторы состояний, лимиты текста, debounce-настройку и глобальное in-memory-хранилище `users`.

[bot_handlers/keyboards.py](/abs/c:/Projects/VS%20Code/bot_handlers/keyboards.py)
Фабрика VK-клавиатур. Создает reply- и inline-клавиатуры для регистрации, просмотра анкет, входящих лайков, жалоб, подтверждений, редактирования и выбора игр.

[bot_handlers/texts.py](/abs/c:/Projects/VS%20Code/bot_handlers/texts.py)
Содержит все пользовательские тексты, подписи кнопок, emoji-константы и строковые шаблоны сообщений.

[bot_handlers/text_formatters.py](/abs/c:/Projects/VS%20Code/bot_handlers/text_formatters.py)
Форматирует итоговые пользовательские сообщения: текст анкеты, сводку по играм, уведомление о лайке, уведомление о мэтче, жалобу в модерацию и короткие done-сообщения.

## Папка `docs`

[docs/bot_logic_description.md](/abs/c:/Projects/VS%20Code/docs/bot_logic_description.md)
Подробное текстовое описание актуальной логики бота: старт, состояния, регистрация, просмотр анкет, лайки, мэтчи, жалобы, деактивация, сброс и восстановление сессий.

[docs/project_structure.md](/abs/c:/Projects/VS%20Code/docs/project_structure.md)
Этот файл. Описывает актуальную структуру репозитория и назначение основных файлов.

## Папка `sql`

[sql/reset_database.sql](/abs/c:/Projects/VS%20Code/sql/reset_database.sql)
Полностью очищает рабочие таблицы бота, но не удаляет саму схему. Используется для чистого старта тестов.

[sql/reset_history.sql](/abs/c:/Projects/VS%20Code/sql/reset_history.sql)
Очищает только историю взаимодействий: `matches`, `interactions`, `pending_likes`. Анкеты, фото и игры не трогает.

[sql/ban_profile.sql](/abs/c:/Projects/VS%20Code/sql/ban_profile.sql)
Ручной SQL-скрипт модерации для блокировки анкеты по `vk_user_id` с сохранением причины бана и отключением активности профиля.

[sql/unban_profile.sql](/abs/c:/Projects/VS%20Code/sql/unban_profile.sql)
Ручной SQL-скрипт для снятия блокировки и повторной активации анкеты.

## Папка `scripts`

[scripts/fix_encoding.py](/abs/c:/Projects/VS%20Code/scripts/fix_encoding.py)
Вспомогательный скрипт для исправления проблем с кодировкой в текстовых файлах проекта.

## Папка `secrets`

Папка для локальных секретов и конфигурации, которые не должны попадать в репозиторий.

[secrets/token.txt](/abs/c:/Projects/VS%20Code/secrets/token.txt)
Локальный файл с VK-токеном, используется как fallback, если не задан `VK_BOT_TOKEN`.

`secrets/local_db.json`
Ожидаемый локальный JSON-файл с параметрами подключения к БД. Может отсутствовать в репозитории и подхватывается `config.py`, если нет env-переменных.

## Папка `logs`

`logs/bot.log`
Основной технический лог бота с ошибками и предупреждениями.

`logs/actions.jsonl`
Структурированный JSON Lines-лог действий пользователей и внутренних событий.

## Как части проекта работают вместе

1. `config.py` загружает секреты и параметры окружения.
2. `vk_bot.py` поднимает VK API и Long Poll.
3. `database.py` подключается к MySQL и проверяет runtime-схему.
4. `main.py` начинает слушать события VK.
5. `bot_handlers/router.py` определяет, какой сценарий запустить для пользователя.
6. `bot_handlers/utils.py` восстанавливает состояние, синхронизирует профиль и помогает показывать анкеты.
7. `database.py` сохраняет все изменения анкеты и взаимодействий.
8. `logger.py` пишет технические и структурированные логи.

## Что важно помнить при дальнейших изменениях

- Если меняется диалоговая логика, в первую очередь нужно смотреть [bot_handlers/router.py](/abs/c:/Projects/VS%20Code/bot_handlers/router.py) и [bot_handlers/utils.py](/abs/c:/Projects/VS%20Code/bot_handlers/utils.py).
- Если меняются тексты или кнопки, правки обычно находятся в [bot_handlers/texts.py](/abs/c:/Projects/VS%20Code/bot_handlers/texts.py) и [bot_handlers/keyboards.py](/abs/c:/Projects/VS%20Code/bot_handlers/keyboards.py).
- Если меняется логика хранения профилей, мэтчей, pending likes или runtime-сессий, главный файл — [database.py](/abs/c:/Projects/VS%20Code/database.py).
- В проекте есть runtime-миграция схемы через `ensure_runtime_schema()`, поэтому новые служебные поля и таблицы нужно согласовывать с этим кодом.
- Секреты должны оставаться в `secrets/` или в переменных окружения, а не в Git.
