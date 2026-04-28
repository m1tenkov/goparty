# Структура Проекта GoParty

Этот документ описывает назначение основных папок и файлов проекта.

## Общее описание проекта

`GoParty` — это VK-бот для знакомств среди геймеров. Он работает через VK Long Poll, хранит анкеты и историю взаимодействий в MySQL, а временное состояние диалога сохраняет как в памяти процесса, так и в базе данных.

## Файлы в корне проекта

[`main.py`](/abs/c:/Projects/VS%20Code/main.py)
Точка входа в приложение. Запускает прослушивание Long Poll, принимает события VK, распределяет `MESSAGE_NEW` и `MESSAGE_EVENT`, логирует время обработки и переподключается после ошибок Long Poll.

[`config.py`](/abs/c:/Projects/VS%20Code/config.py)
Загружает конфигурацию и секреты. Читает токен VK, ID группы, feature-флаги и настройки подключения к MySQL из переменных окружения или файлов в папке `secrets/`.

[`vk_bot.py`](/abs/c:/Projects/VS%20Code/vk_bot.py)
Инициализирует `vk_api.VkApi`, создает клиент VK API и предоставляет функцию `create_longpoll()`, которую использует `main.py`.

[`database.py`](/abs/c:/Projects/VS%20Code/database.py)
Основной слой работы с базой данных. Открывает подключение к MySQL, проверяет и дополняет runtime-схему, читает и сохраняет анкеты, игры, фото, лайки, мэтчи, pending likes, состояние пользовательских сессий и служебные поля вроде банов и ошибок доставки.

[`logger.py`](/abs/c:/Projects/VS%20Code/logger.py)
Утилиты логирования проекта. Пишет текстовые логи в `logs/bot.log` и структурированные логи действий в `logs/actions.jsonl`.

[`requirements.txt`](/abs/c:/Projects/VS%20Code/requirements.txt)
Список Python-зависимостей, используемых при развертывании проекта на сервере.

[.gitignore](/abs/c:/Projects/VS%20Code/.gitignore)
Правила исключения файлов из Git. Защищает секреты, логи и локальные/сгенерированные файлы от попадания в репозиторий.

## Папка `bot_handlers`

[`bot_handlers/__init__.py`](/abs/c:/Projects/VS%20Code/bot_handlers/__init__.py)
Небольшой экспортный модуль. Повторно экспортирует публичные обработчики из `router.py`.

[`bot_handlers/router.py`](/abs/c:/Projects/VS%20Code/bot_handlers/router.py)
Главный контроллер диалоговой логики бота. Содержит маршрутизацию сообщений, переходы между состояниями, логику просмотра анкет, сценарий входящих лайков, сценарий жалоб, safe-обертки над отправкой сообщений в VK и обработку callback-событий.

[`bot_handlers/utils.py`](/abs/c:/Projects/VS%20Code/bot_handlers/utils.py)
Вспомогательный слой для runtime-состояния пользователя и логики представления. Создает runtime-объекты пользователей, синхронизирует состояние с БД, получает данные профиля из VK, форматирует анкеты, извлекает фотографии и обслуживает общие сценарии, например экран анкеты и просмотр кандидатов.

[`bot_handlers/constants.py`](/abs/c:/Projects/VS%20Code/bot_handlers/constants.py)
Содержит названия состояний диалога, лимиты длины текстов, debounce-настройки и глобальное in-memory хранилище `users`.

[`bot_handlers/texts.py`](/abs/c:/Projects/VS%20Code/bot_handlers/texts.py)
Хранит все пользовательские тексты, подписи кнопок, emoji-константы, шаблоны сообщений и служебные консольные сообщения.

[`bot_handlers/text_formatters.py`](/abs/c:/Projects/VS%20Code/bot_handlers/text_formatters.py)
Содержит функции форматирования текста анкеты, уведомлений о лайках, уведомлений о мэтчах, сообщений для модерации и коротких итоговых сообщений.

[`bot_handlers/keyboards.py`](/abs/c:/Projects/VS%20Code/bot_handlers/keyboards.py)
Фабрика VK-клавиатур. Создает reply-клавиатуры и inline callback-клавиатуры для регистрации, просмотра анкет, лайков, жалоб, выбора игр и подтверждающих сценариев.

## Папка `docs`

[`docs/bot_logic_description.txt`](/abs/c:/Projects/VS%20Code/docs/bot_logic_description.txt)
Большое текстовое описание логики работы бота: запуск, состояния, регистрация, просмотр анкет, лайки, жалобы, сброс данных, callback-обработка и восстановление runtime-состояния.

[`docs/project_structure.md`](/abs/c:/Projects/VS%20Code/docs/project_structure.md)
Этот файл. Содержит обзор структуры репозитория и назначение основных файлов проекта.

## Папка `scripts`

[`scripts/fix_encoding.py`](/abs/c:/Projects/VS%20Code/scripts/fix_encoding.py)
Вспомогательный скрипт для исправления проблем с кодировкой в файлах проекта или экспортированных текстах.

## Папка `secrets`

[`secrets/token.txt`](/abs/c:/Projects/VS%20Code/secrets/token.txt)
Локальный файл с токеном VK-бота, не предназначенный для хранения в Git. Нужен для запуска, если не задана переменная окружения `VK_BOT_TOKEN`.

[`secrets/local_db.example.json`](/abs/c:/Projects/VS%20Code/secrets/local_db.example.json)
Шаблон с примером настроек подключения к локальной базе данных. Реальный рабочий файл в окружении должен называться `secrets/local_db.json`.

[`secrets/README.md`](/abs/c:/Projects/VS%20Code/secrets/README.md)
Краткое описание того, какие секреты ожидаются в этой папке.

## Папка `sql`

[`sql/reset_database.sql`](/abs/c:/Projects/VS%20Code/sql/reset_database.sql)
Скрипт полного сброса базы данных для чистого старта.

[`sql/reset_history.sql`](/abs/c:/Projects/VS%20Code/sql/reset_history.sql)
Скрипт очистки истории взаимодействий: лайков, мэтчей и pending likes, без полного пересоздания всей базы.

[`sql/seed_bot_profiles.sql`](/abs/c:/Projects/VS%20Code/sql/seed_bot_profiles.sql)
Заполняет базу тестовыми бот-анкетами для разработки и отладки.

[`sql/seed_friend_profiles.sql`](/abs/c:/Projects/VS%20Code/sql/seed_friend_profiles.sql)
Заполняет базу анкетами реальных друзей для более реалистичного тестирования.

[`sql/ban_profile.sql`](/abs/c:/Projects/VS%20Code/sql/ban_profile.sql)
Ручной модерационный скрипт для блокировки анкеты пользователя по VK ID с сохранением причины блокировки.

[`sql/unban_profile.sql`](/abs/c:/Projects/VS%20Code/sql/unban_profile.sql)
Ручной модерационный скрипт для снятия блокировки с анкеты пользователя.

## Папка `logs`

[`logs/bot.log`](/abs/c:/Projects/VS%20Code/logs/bot.log)
Основной лог-файл с предупреждениями и ошибками работающего бота.

`logs/actions.jsonl`
Структурированный лог в формате JSON Lines с действиями пользователей, внутренними событиями и технической телеметрией. Создается автоматически через `logger.py`.

## Как части проекта работают вместе

1. `main.py` запускает бота и начинает слушать события VK через Long Poll.
2. `vk_bot.py` предоставляет VK-сессию и объект Long Poll.
3. `router.py` решает, как именно обрабатывать каждое входящее событие.
4. `utils.py` и `keyboards.py` помогают строить ответы и управлять состоянием диалога.
5. `database.py` сохраняет анкеты, лайки, мэтчи и runtime-состояние.
6. `texts.py` и `text_formatters.py` определяют, как бот формирует сообщения пользователю.
7. `logger.py` записывает важные действия, ошибки и технические детали для отладки.

## Подсказки для разработки

- Если меняется основная логика бота, чаще всего нужно смотреть в `bot_handlers/router.py`, `bot_handlers/utils.py`, `database.py` и `bot_handlers/texts.py`.
- Если меняются тексты интерфейса или кнопки, в первую очередь нужно открывать `bot_handlers/texts.py` и `bot_handlers/keyboards.py`.
- Если меняется логика хранения данных, модерации или мэтчей, начинать лучше с `database.py` и связанных SQL-скриптов в папке `sql/`.
- Секреты серверного окружения нельзя коммитить в репозиторий; их нужно хранить в `secrets/` или в переменных окружения.
