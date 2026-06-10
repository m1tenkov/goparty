# Резервное копирование на Cloud.ru-сервере

Бот работает на сервере Cloud.ru, поэтому резервное копирование нужно запускать на этом сервере, в каталоге проекта. Локальный запуск на компьютере разработчика не сохранит реальные данные, если MySQL и фотографии находятся на удаленной машине.

Проект хранит пользовательские данные в двух местах:

- MySQL-база `goparty_bot`;
- локальные фотографии пользователей в `storage/photos`.

Скрипт `scripts/backup.py` собирает оба источника в один ZIP-архив.

## Что попадает в архив

Внутри архива:

- `database.sql` - дамп MySQL;
- `storage/photos/...` - локальные фотографии пользователей;
- `manifest.json` - время создания и служебная информация.

Архив называется по шаблону:

```text
goparty_backup_YYYYMMDD_HHMMSS.zip
```

## Подготовка сервера

Подключиться к Cloud.ru-серверу по SSH:

```bash
ssh <user>@<server-ip>
```

Перейти в каталог проекта:

```bash
cd /path/to/project
```

Проверить, что на сервере есть `mysqldump`:

```bash
which mysqldump
```

Если команды нет, установить MySQL client tools. Для Ubuntu/Debian:

```bash
sudo apt update
sudo apt install mysql-client
```

## Ручной запуск

```bash
python3 scripts/backup.py --output-dir /var/backups/goparty --keep 30
```

Скрипт читает параметры базы из переменных окружения или из `secrets/local_db.json`, как и само приложение:

- `DB_HOST`;
- `DB_PORT`;
- `DB_NAME`;
- `DB_USER`;
- `DB_PASSWORD`;
- `DB_SSL_CA`.

Если проект запускается из виртуального окружения, лучше использовать Python из него:

```bash
/path/to/venv/bin/python scripts/backup.py --output-dir /var/backups/goparty --keep 30
```

## Запуск по расписанию

Открыть cron:

```bash
crontab -e
```

Добавить ежедневный запуск, например в 03:15:

```cron
15 3 * * * cd /path/to/project && /path/to/venv/bin/python scripts/backup.py --output-dir /var/backups/goparty --keep 30 >> logs/backup.log 2>&1
```

Параметр `--keep 30` оставляет 30 последних архивов и удаляет более старые.

## Важное правило хранения

Архив в `/var/backups/goparty` защищает от ошибок в базе или случайного удаления файлов, но не защищает от потери самого сервера. Поэтому копии нужно регулярно уносить за пределы виртуальной машины Cloud.ru.

Минимальный вариант - скачивать архив на локальный компьютер:

```bash
scp <user>@<server-ip>:/var/backups/goparty/goparty_backup_YYYYMMDD_HHMMSS.zip .
```

Более надежный вариант - настроить выгрузку архивов во внешнее объектное хранилище или другое отдельное хранилище резервных копий.

## Восстановление

1. Остановить приложение, чтобы бот не писал новые данные во время восстановления.
2. Распаковать нужный архив.
3. Восстановить базу:

```bash
mysql --host=localhost --port=3306 --user=root --password goparty_bot < database.sql
```

4. Вернуть папку `storage/photos` из архива в корень проекта.
5. Запустить приложение обратно.

Если MySQL находится не на том же сервере, нужно указать реальные `--host`, `--port`, `--user` и имя базы.
