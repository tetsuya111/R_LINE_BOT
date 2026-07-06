# CodeRing_LINE_BOT

LINE Messaging APIでメッセージを一斉送信するCLIツールと、メッセージを受信するwebhookエンドポイント。

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
```

`.env`にLINEチャネルアクセストークンとチャネルシークレットを設定する。

```
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_CHANNEL_SECRET=your_channel_secret_here
```

## 使い方

### メッセージ送信（一斉送信）

```bash
python send_message.py "送信したいメッセージ"
```

```
LINE Messaging APIでメッセージを一斉送信する

Usage:
    send_message.py <message>
    send_message.py -h | --help

Options:
    -h --help  ヘルプを表示する
```

### メッセージ送信（個別送信）

```bash
python send_message_v2.py "名前" "送信したいメッセージ"
```

```
LINE Messaging APIで特定のユーザーにメッセージを送信する

ユーザーは名前の部分一致検索で特定する（対応関係は`users.db`に保存されたものを使用する）。

Usage:
    send_message_v2.py <name> <message>
    send_message_v2.py -h | --help

Options:
    -h --help  ヘルプを表示する
```

名前が部分一致で複数のユーザーにヒットした場合、または1件もヒットしなかった場合はエラーになる。

### webhookエンドポイント

```bash
python webhook.py
```

起動するとngrokでトンネルが張られ、表示されたURL（`https://xxxx.ngrok-free.app/webhook`）をLINE Developersコンソールのwebhook URLに設定する。

LINEユーザーから`名前 <名前>`形式のメッセージを受信すると、ユーザーIDと名前の対応が`users.db`（sqlite3）に保存される。

## 構成

| ファイル | 内容 |
| --- | --- |
| `send_message.py` | 一斉送信スクリプト本体 |
| `send_message_v2.py` | 個別送信スクリプト本体 |
| `webhook.py` | webhookエンドポイント本体 |
| `users.db` | ユーザーID・名前対応の保存先（sqlite3、自動生成） |
| `requirements.txt` | 依存パッケージ |
| `.env.example` | 環境変数のサンプル |
| `prompts/` | 実装時に使用したプロンプト |
| `logs/` | プロンプト実行ログ |
