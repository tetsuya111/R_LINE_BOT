"""LINE Messaging APIで特定のユーザーにメッセージを送信する

ユーザーは名前の部分一致検索で特定する（対応関係は`users.db`に保存されたものを使用する）。

Usage:
    send_message_v2.py <name> <message>
    send_message_v2.py -h | --help

Options:
    -h --help  ヘルプを表示する
"""
import os
import sqlite3
import sys
from pathlib import Path

import requests
from docopt import docopt
from dotenv import load_dotenv

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
DB_PATH = Path(__file__).parent / "users.db"


def find_users_by_name(name: str) -> list[tuple[str, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT user_id, name FROM users WHERE name LIKE ?",
            (f"%{name}%",),
        ).fetchall()


def push_message(access_token: str, user_id: str, message: str) -> requests.Response:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {"to": user_id, "messages": [{"type": "text", "text": message}]}

    response = requests.post(LINE_PUSH_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response


def main() -> None:
    args = docopt(__doc__)
    load_dotenv()

    access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not access_token:
        print("エラー: .envにLINE_CHANNEL_ACCESS_TOKENを設定してください", file=sys.stderr)
        sys.exit(1)

    name = args["<name>"]
    matches = find_users_by_name(name)

    if not matches:
        print(f"エラー: 名前「{name}」に一致するユーザーが見つかりません", file=sys.stderr)
        sys.exit(1)
    if len(matches) > 1:
        candidates = ", ".join(f"{n}({uid})" for uid, n in matches)
        print(f"エラー: 名前「{name}」に一致するユーザーが複数見つかりました: {candidates}", file=sys.stderr)
        sys.exit(1)

    user_id, matched_name = matches[0]

    try:
        response = push_message(access_token, user_id, args["<message>"])
        print(f"送信成功: {response.status_code} {response.text}")
    except requests.exceptions.HTTPError as e:
        print(f"送信に失敗しました: {e}\n{e.response.text}", file=sys.stderr)
        sys.exit(1)

    print(f"{matched_name}さんにメッセージを送信しました。")


if __name__ == "__main__":
    main()
