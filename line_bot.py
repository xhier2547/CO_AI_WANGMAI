import os
import pandas as pd
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage


# ---------------- CONFIG ---------------- #
CHANNEL_ACCESS_TOKEN = "RgdlVa2/M981fASPei1fz+p8VxMMltZDC3MyZKrfqiHo59UsZye5LmSJx2v7wc8+DT4VxlnVL9RSOlpTQRtFDfj8IIt6jgBLyjj/E/EuepWi3ymkVRg44h72q3NcTGje3vTDHKzPuWYNnrd8OVx1JAdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "fe71e2480dfcac451b531659e5336652"           # << ใส่จาก LINE Developers

CSV_FILE = "usage_stats.csv"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

app = Flask(__name__)

# ---------------- FUNCTION ---------------- #
def get_latest_status():
    if not os.path.exists(CSV_FILE):
        return "⚠️ ยังไม่มีข้อมูลในระบบ"

    df = pd.read_csv(CSV_FILE)
    if df.empty:
        return "⚠️ ยังไม่มีข้อมูลในระบบ"

    latest = df.iloc[-1]
    ts = latest["timestamp"]
    people = int(latest["people_count"])
    tables = f"{int(latest['table_used'])}/{int(latest['table_total'])}"

    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏠 ห้อง Co-AI \n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 จำนวนคน : {people}\n"
        f"🪑 การใช้โต๊ะ : {tables}\n"
        f"⏰ เวลา     : {ts}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    return text

# ---------------- ROUTES ---------------- #
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ---------------- HANDLER ---------------- #
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    if user_text in ["เช็คห้อง CO", "เช็คห้อง", "check room", "co"]:
        reply_text = get_latest_status()
    else:
        reply_text = f"คุณพิมพ์ว่า: {user_text}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)