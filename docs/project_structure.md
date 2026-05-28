# Структура проекта GoParty

## Общее описание

`GoParty` - VK-бот на Python, работающий через `VK Callback API`. Проект хранит анкеты, игровые интересы, пути к фотографиям, фильтры поиска, историю взаимодействий и runtime-состояние пользователей в MySQL, а сами файлы фотографий размещаются на сервере.

Ниже описана актуальная структура репозитория и назначение ключевых модулей.

## Корень проекта

[app.py](/c:/Projects/VS%20Code/app.py:1)  
FastAPI-приложение, принимающее `POST /vk/callback` и `GET /health`.

[event_processing.py](/c:/Projects/VS%20Code/event_processing.py:1)  
Транспортный слой обработки callback-событий. Разделяет `message_new` и `message_event`, оборачивает вызов прикладной логики и логирует длительность обработки.

[vk_bot.py](/c:/Projects/VS%20Code/vk_bot.py:1)  
Создает VK API-клиент для работы с `messages`, `users`, `photos` и загрузкой изображений.

[config.py](/c:/Projects/VS%20Code/config.py:1)  
Загружает конфигурацию из env и `secrets/`: токен VK, callback-secret, confirmation token, параметры БД, путь к SSL CA и feature-флаги.

[database.py](/c:/Projects/VS%20Code/database.py:1)  
Слой доступа к БД. Отвечает за runtime-миграции схемы, профили, игры, сведения о фотографиях, лайки, мэтчи, фильтры, историю и пользовательские сессии.

[logger.py](/c:/Projects/VS%20Code/logger.py:1)  
Настройка технического лога и структурированного журнала действий.

[button_flags.py](/c:/Projects/VS%20Code/button_flags.py:1)  
Feature-флаги для включения отдельных кнопок, например очистки истории или полного сброса профиля.

## Папка `bot_handlers`

[bot_handlers/router.py](/c:/Projects/VS%20Code/bot_handlers/router.py:1)  
Главный контроллер диалогов. Здесь живут регистрация, просмотр анкет, история, лайки, жалобы, фильтры, деактивация и сброс анкеты.

[bot_handlers/utils.py](/c:/Projects/VS%20Code/bot_handlers/utils.py:1)  
Вспомогательный runtime-слой: восстановление пользователя, автозаполнение из VK, работа с локальными фото, показ кандидатов, сохранение сессий и фильтров.

[bot_handlers/keyboards.py](/c:/Projects/VS%20Code/bot_handlers/keyboards.py:1)  
Фабрика VK-клавиатур: reply и inline-клавиатуры для регистрации, редактирования, фильтров, просмотра анкет и входящих лайков.

[bot_handlers/constants.py](/c:/Projects/VS%20Code/bot_handlers/constants.py:1)  
Строковые идентификаторы состояний, лимиты текста, debounce-настройки и глобальное runtime-хранилище `users`.

[bot_handlers/texts.py](/c:/Projects/VS%20Code/bot_handlers/texts.py:1)  
Пользовательские тексты, подписи кнопок, emoji-константы и шаблоны сообщений.

[bot_handlers/text_formatters.py](/c:/Projects/VS%20Code/bot_handlers/text_formatters.py:1)  
Форматирование текста анкеты, лайка, мэтча, жалобы и коротких служебных сообщений.

## Папка `docs`

[docs/bot_logic_description.md](/c:/Projects/VS%20Code/docs/bot_logic_description.md:1)  
Подробное описание сценариев и внутренних состояний бота.

[docs/database_structure.md](/c:/Projects/VS%20Code/docs/database_structure.md:1)  
Описание структуры БД, таблиц и их роли в системе.

[docs/fastapi_callback_setup.md](/c:/Projects/VS%20Code/docs/fastapi_callback_setup.md:1)  
Инструкция по запуску и настройке Callback API.

[docs/project_structure.md](/c:/Projects/VS%20Code/docs/project_structure.md:1)  
Этот файл.

[docs/user_sessions_session_json.md](/c:/Projects/VS%20Code/docs/user_sessions_session_json.md:1)  
Описание того, что именно сохраняется в `user_sessions.session_json`.

[docs/user_flow_diagram_tz.md](/c:/Projects/VS%20Code/docs/user_flow_diagram_tz.md:1)  
Техническое задание на генерацию User Flow диаграммы ВК-бота.

## Папка `sql`

[sql/reset_database.sql](/c:/Projects/VS%20Code/sql/reset_database.sql:1)  
Полная очистка рабочих таблиц.

[sql/reset_history.sql](/c:/Projects/VS%20Code/sql/reset_history.sql:1)  
Очистка истории взаимодействий, мэтчей и pending likes без удаления анкет.

[sql/ban_profile.sql](/c:/Projects/VS%20Code/sql/ban_profile.sql:1)  
Ручной бан анкеты по `vk_user_id`.

[sql/unban_profile.sql](/c:/Projects/VS%20Code/sql/unban_profile.sql:1)  
Снятие блокировки и повторная активация анкеты.

[sql/seed_friend_profiles.sql](/c:/Projects/VS%20Code/sql/seed_friend_profiles.sql:1)  
Заполнение БД тестовыми профилями.

## Папка `storage`

`storage/photos/`  
Локальное файловое хранилище фотографий пользователей. Новая версия бота сохраняет фото не только как VK token, но и как локальные файлы с повторной загрузкой в сообщения VK при необходимости.

## Как части проекта работают вместе

1. `config.py` загружает секреты и параметры окружения.
2. `app.py` принимает callback-запрос от VK.
3. `event_processing.py` маршрутизирует тип события.
4. `router.py` определяет прикладной сценарий по текущему `step`.
5. `utils.py` восстанавливает runtime-состояние, подтягивает VK defaults и показывает нужный экран.
6. `database.py` сохраняет анкеты, фильтры, пути к фотографиям, лайки, мэтчи и сессии.
7. `logger.py` фиксирует действия и ошибки.

## Что важно помнить при дальнейших изменениях

- Если меняется логика сценариев, в первую очередь нужно смотреть [bot_handlers/router.py](/c:/Projects/VS%20Code/bot_handlers/router.py:1) и [bot_handlers/utils.py](/c:/Projects/VS%20Code/bot_handlers/utils.py:1).
- Если меняются кнопки и тексты, правки обычно находятся в [bot_handlers/keyboards.py](/c:/Projects/VS%20Code/bot_handlers/keyboards.py:1) и [bot_handlers/texts.py](/c:/Projects/VS%20Code/bot_handlers/texts.py:1).
- Если меняется структура подбора, фильтров или runtime-состояния, главный файл - [database.py](/c:/Projects/VS%20Code/database.py:1).
- В проекте есть runtime-миграция `ensure_runtime_schema()`, поэтому новые служебные поля и таблицы должны быть согласованы с ней.
