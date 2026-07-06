"""LINE Messaging APIでメッセージを一斉送信する

Usage:
    send_message.py <message>
    send_message.py -h | --help

Options:
    -h --help  ヘルプを表示する
"""
import os
import sys

import requests
from docopt import docopt
from dotenv import load_dotenv

LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"


def broadcast_message(access_token: str, message: str) -> None:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {"messages": [{"type": "text", "text": message}]}

    response = requests.post(LINE_BROADCAST_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response


def main() -> None:
    args = docopt(__doc__)
    load_dotenv()

    access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not access_token:
        print("エラー: .envにLINE_CHANNEL_ACCESS_TOKENを設定してください", file=sys.stderr)
        sys.exit(1)

    try:
        response=broadcast_message(access_token, args["<message>"])
        print(f"送信成功: {response.status_code} {response.text}")
    except requests.exceptions.HTTPError as e:
        print(f"送信に失敗しました: {e}\n{e.response.text}", file=sys.stderr)
        sys.exit(1)

    print("メッセージを送信しました。")


if __name__ == "__main__":
    main()
