"""LINE Messaging APIのwebhookエンドポイント

"名前 <名前>" 形式のメッセージを受信した場合、
LINEユーザーIDと名前の対応をローカルのsqlite3データベースに保存する。

Usage:
    python webhook.py
"""
import base64
import hashlib
import hmac
import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DB_PATH = Path(__file__).parent / "users.db"
NAME_PATTERN = re.compile(r"^名前\s+(.+)$")
NGROK_ACCESS_TOKEN = os.getenv("NGROK_ACCESS_TOKEN")

app = FastAPI()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )


def save_user_name(user_id: str, name: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, name) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET name = excluded.name
            """,
            (user_id, name),
        )


def verify_signature(body: bytes, signature: str) -> bool:
    digest = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected_signature, signature)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.post("/webhook")
async def webhook(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()

    print("Signature",x_line_signature,verify_signature(body,x_line_signature))
    #if not x_line_signature or not verify_signature(body, x_line_signature):
    #    raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    for event in payload.get("events", []):
        if event.get("type") != "message":
            continue

        message = event.get("message", {})
        if message.get("type") != "text":
            continue

        match = NAME_PATTERN.match(message.get("text", ""))
        user_id = event.get("source", {}).get("userId")
        if match and user_id:
            save_user_name(user_id, match.group(1).strip())

    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from pyngrok import ngrok

    port = int(os.getenv("PORT", "8000"))
    ngrok.set_auth_token(NGROK_ACCESS_TOKEN)
    public_url = ngrok.connect(port, "http")
    print(f"webhook URL: {public_url}/webhook")
    uvicorn.run(app, host="0.0.0.0", port=port)
