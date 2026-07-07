/**
 * LINE Messaging APIのwebhookエンドポイント
 *
 * "名前 <名前>" 形式のメッセージを受信した場合、
 * LINEユーザーIDと名前の対応をローカルのsqlite3データベースに保存する。
 *
 * Usage:
 *     node webhook.js
 */
"use strict";

const crypto = require("crypto");
const path = require("path");
const { DatabaseSync } = require("node:sqlite");
const dotenv = require("dotenv");
const express = require("express");
const ngrok = require("@ngrok/ngrok");

dotenv.config({ quiet: true });

const LINE_CHANNEL_SECRET = process.env.LINE_CHANNEL_SECRET;
const DB_PATH = path.join(__dirname, "users.db");
const NAME_PATTERN = /^名前\s+(.+)$/;
const NGROK_ACCESS_TOKEN = process.env.NGROK_ACCESS_TOKEN;

const app = express();
app.use(express.raw({ type: "*/*" }));

function initDb() {
  const conn = new DatabaseSync(DB_PATH);
  conn.exec(`
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    )
  `);
  conn.close();
}

function saveUserName(userId, name) {
  const conn = new DatabaseSync(DB_PATH);
  conn
    .prepare(
      `INSERT INTO users (user_id, name) VALUES (?, ?)
       ON CONFLICT(user_id) DO UPDATE SET name = excluded.name`
    )
    .run(userId, name);
  conn.close();
}

function verifySignature(body, signature) {
  const digest = crypto
    .createHmac("sha256", LINE_CHANNEL_SECRET)
    .update(body)
    .digest();
  const expectedSignature = digest.toString("base64");

  const expectedBuffer = Buffer.from(expectedSignature);
  const signatureBuffer = Buffer.from(String(signature));
  if (expectedBuffer.length !== signatureBuffer.length) return false;
  return crypto.timingSafeEqual(expectedBuffer, signatureBuffer);
}

app.post("/webhook", (req, res) => {
  const body = req.body;
  const xLineSignature = req.header("x-line-signature");

  console.log("Signature", xLineSignature, verifySignature(body, xLineSignature));
  // if (!xLineSignature || !verifySignature(body, xLineSignature)) {
  //   return res.status(400).json({ detail: "Invalid signature" });
  // }

  const payload = JSON.parse(body.toString("utf-8"));
  for (const event of payload.events || []) {
    if (event.type !== "message") continue;

    const message = event.message || {};
    if (message.type !== "text") continue;

    const match = NAME_PATTERN.exec(message.text || "");
    const userId = event.source && event.source.userId;
    if (match && userId) {
      saveUserName(userId, match[1].trim());
    }
  }

  res.json({ status: "ok" });
});

async function main() {
  initDb();

  const port = parseInt(process.env.PORT || "8000", 10);
  const listener = await ngrok.connect({ addr: port, authtoken: NGROK_ACCESS_TOKEN });
  console.log(`webhook URL: ${listener.url()}/webhook`);
  app.listen(port, "0.0.0.0");
}

if (require.main === module) {
  main();
}
