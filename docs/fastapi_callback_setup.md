# FastAPI Callback API Setup

## Что изменилось

- Точка входа для VK Callback API: `app.py`
- Callback endpoint: `POST /vk/callback`
- Healthcheck endpoint: `GET /health`
- Общая обработка событий вынесена в `event_processing.py`

## Секреты

Нужны дополнительные секреты:

- `secrets/vk_callback_secret.txt`
- `secrets/vk_callback_confirmation_token.txt`

Либо можно передать их через env:

- `VK_CALLBACK_SECRET`
- `VK_CALLBACK_CONFIRMATION_TOKEN`

Опционально:

- `APP_HOST`
- `APP_PORT`

## Локальный запуск

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

Проверка:

```bash
curl http://127.0.0.1:8000/health
```

## Systemd service

Пример `/etc/systemd/system/goparty.service`:

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

## Nginx

Пример reverse proxy:

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

Дальше нужно выпустить HTTPS-сертификат, например через Let's Encrypt.

## VK Callback API

В настройках сообщества VK:

1. Включить Callback API.
2. Указать URL:
   `https://your-domain.example/vk/callback`
3. Указать `secret`, совпадающий с `VK_CALLBACK_SECRET`.
4. Подтвердить сервер через `confirmation` token.
5. Включить события:
   - `message_new`
   - `message_event`
