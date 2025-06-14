import os
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import os
from datetime import datetime

app = Flask(__name__)
load_dotenv()

# 用你自己的 Token/Secret
line_bot_api = LineBotApi("CHANNEL_SECRET")
handler = WebhookHandler("CHANNEL_ACCESS_TOKEN")
DATA_FILE = "record.json"

# 初始化紀錄檔案
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()
    data = load_data()

    if text == "start":
        now = datetime.now().isoformat()
        data[user_id] = {"start": now}
        save_data(data)
        reply = f"🟢 開始時間已紀錄：{now}"

    elif text == "end":
        if user_id in data and "start" in data[user_id]:
            start_time = datetime.fromisoformat(data[user_id]["start"])
            end_time = datetime.now()
            duration = end_time - start_time
            minutes = round(duration.total_seconds() / 60, 2)

            reply = (
                f"🔴 結束時間：{end_time.isoformat()}\n"
                f"⏱ 總共花費時間：{minutes} 分鐘"
            )
            del data[user_id]
            save_data(data)
        else:
            reply = "⚠️ 尚未開始計時，請先輸入 start。"

    else:
        reply = "請輸入 `start` 開始，或 `end` 結束計時。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


if __name__ == "__main__":
    app.run()
