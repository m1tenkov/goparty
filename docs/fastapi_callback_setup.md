# FastAPI Callback API Setup

## Что используется сейчас

- Точка входа для VK Callback API: `app.py`
- Основной callback endpoint: `POST /vk/callback`
- Endpoint для проверки доступности: `GET /health`
- Проверка callback secret и confirmation token выполняется на уровне FastAPI
- Разбор событий `message_new` и `message_event` вынесен в `event_processing.py`

## Какие события обрабатываются

Бот принимает два рабочих типа событий:

- `message_new` - обычные входящие сообщения пользователя
- `message_event` - callback-события от inline-кнопок

Событие `confirmation` обрабатывается отдельно и возвращает `VK_CALLBACK_CONFIRMATION_TOKEN`.

Остальные типы событий логируются как `callback_ignored` и подтверждаются ответом `ok`.

## Секреты и переменные окружения

Обязательные параметры:

- `VK_BOT_TOKEN`
- `VK_CALLBACK_SECRET`
- `VK_CALLBACK_CONFIRMATION_TOKEN`

Их можно передавать через env или хранить в файлах:

- `secrets/token.txt`
- `secrets/vk_callback_secret.txt`
- `secrets/vk_callback_confirmation_token.txt`

Дополнительно используются:

- `APP_HOST`
- `APP_PORT`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_SSL_CA`
- `ENABLE_LIKE_NOTIFICATIONS`

## Локальный запуск

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

Проверка доступности:

```bash
curl http://127.0.0.1:8000/health
```

## Что происходит при callback-запросе

1. FastAPI принимает JSON от VK.
2. Проверяется поле `secret`, если задан `VK_CALLBACK_SECRET`.
3. Для `confirmation` возвращается confirmation token.
4. Для `message_new` и `message_event` создается объект события и вызывается прикладной обработчик.
5. Ошибки внутри логики не роняют endpoint: они логируются в `event_processing.py`.
6. VK получает ответ `ok`.

## Рекомендуемая схема развертывания

- `nginx` принимает HTTPS-трафик извне
- `uvicorn` с FastAPI слушает локальный порт
- VK обращается к публичному URL вида `https://<domain>/vk/callback`

Пример `systemd` unit:

```ini
[Unit]
Description=GoParty VK Bot Callback API
After=network.target mysql.service

[Service]
User=ubuntu
WorkingDirectory=/opt/goparty
Environment="APP_HOST=127.0.0.1"
Environment="APP_PORT=8000"
ExecStart=/opt/goparty/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Применение:

```bash
sudo systemctl daemon-reload
sudo systemctl enable goparty.service
sudo systemctl start goparty.service
sudo systemctl status goparty.service
```

## Пример reverse proxy для nginx

```nginx
server {
    server_name your-domain.example;

    location /vk/callback {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

После этого нужно выпустить HTTPS-сертификат, например через Let's Encrypt.

## Настройка VK Callback API

В настройках сообщества VK:

1. Включить Callback API.
2. Указать URL `https://your-domain.example/vk/callback`.
3. Указать secret, совпадающий с `VK_CALLBACK_SECRET`.
4. Подтвердить сервер через confirmation token.
5. Включить события:
   - `message_new`
   - `message_event`

## Что важно после последних доработок

- Inline-кнопки используются не только для выбора игр при регистрации, но и для выбора обязательных игр в фильтрах поиска.
- Прикладная логика теперь активно опирается на runtime-состояние пользователя и данные из `user_sessions`.
- Без корректно настроенного callback-маршрута не будут работать сценарии выбора игр и фильтров, потому что они завязаны на `message_event`.
