from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from config import APP_HOST, APP_PORT, VK_CALLBACK_CONFIRMATION_TOKEN, VK_CALLBACK_SECRET
from event_processing import enqueue_callback_payload, start_callback_worker, stop_callback_worker
from logger import bot_logger, log_action


app = FastAPI(title="GoParty VK Bot", version="1.0.0")


@app.get("/health", response_class=PlainTextResponse)
async def healthcheck():
    return "ok"


@app.post("/vk/callback", response_class=PlainTextResponse)
async def vk_callback(request: Request):
    payload = await request.json()
    event_type = str(payload.get("type") or "")
    secret = str(payload.get("secret") or "")

    if VK_CALLBACK_SECRET and secret != VK_CALLBACK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid callback secret")

    if event_type == "confirmation":
        if not VK_CALLBACK_CONFIRMATION_TOKEN:
            raise HTTPException(status_code=500, detail="Missing confirmation token")
        return VK_CALLBACK_CONFIRMATION_TOKEN

    if event_type in {"message_new", "message_event"}:
        if not enqueue_callback_payload(payload):
            raise HTTPException(status_code=503, detail="Callback queue is full")
        return "ok"

    log_action("callback_ignored", event_type=event_type)
    return "ok"


@app.on_event("startup")
async def on_startup():
    start_callback_worker()
    bot_logger.info("FastAPI callback app started on %s:%s", APP_HOST, APP_PORT)


@app.on_event("shutdown")
async def on_shutdown():
    stop_callback_worker()
