/**
 * LINE Messaging APIで特定のユーザーにメッセージを送信する
 *
 * ユーザーは名前の部分一致検索で特定する（対応関係は`users.db`に保存されたものを使用する）。
 *
 * Usage:
 *     send_message_v2.js <name> <message>
 *     send_message_v2.js -h | --help
 *
 * Options:
 *     -h --help  ヘルプを表示する
 */
"use strict";

const path = require("path");
const { DatabaseSync } = require("node:sqlite");
const dotenv = require("dotenv");
const { docopt } = require("docopt");

const doc = `
Usage:
    send_message_v2.js <name> <message>
    send_message_v2.js -h | --help

Options:
    -h --help  ヘルプを表示する
`;

const LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push";
const DB_PATH = path.join(__dirname, "users.db");

function findUsersByName(name) {
  const conn = new DatabaseSync(DB_PATH);
  try {
    return conn
      .prepare("SELECT user_id, name FROM users WHERE name LIKE ?")
      .all(`%${name}%`);
  } finally {
    conn.close();
  }
}

async function pushMessage(accessToken, userId, message) {
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${accessToken}`,
  };
  const payload = { to: userId, messages: [{ type: "text", text: message }] };

  const response = await fetch(LINE_PUSH_URL, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  return response;
}

async function main() {
  const args = docopt(doc);
  dotenv.config({ quiet: true });

  const accessToken = process.env.LINE_CHANNEL_ACCESS_TOKEN;
  if (!accessToken) {
    console.error("エラー: .envにLINE_CHANNEL_ACCESS_TOKENを設定してください");
    process.exit(1);
  }

  const name = args["<name>"];
  const matches = findUsersByName(name);

  if (matches.length === 0) {
    console.error(`エラー: 名前「${name}」に一致するユーザーが見つかりません`);
    process.exit(1);
  }
  if (matches.length > 1) {
    const candidates = matches
      .map((m) => `${m.name}(${m.user_id})`)
      .join(", ");
    console.error(
      `エラー: 名前「${name}」に一致するユーザーが複数見つかりました: ${candidates}`
    );
    process.exit(1);
  }

  const { user_id: userId, name: matchedName } = matches[0];

  const response = await pushMessage(accessToken, userId, args["<message>"]);
  const responseText = await response.text();
  if (!response.ok) {
    console.error(
      `送信に失敗しました: ${response.status} ${response.statusText}\n${responseText}`
    );
    process.exit(1);
  }
  console.log(`送信成功: ${response.status} ${responseText}`);

  console.log(`${matchedName}さんにメッセージを送信しました。`);
}

main();
