import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage


# ---------------- CONFIG ---------------- #
CHANNEL_ACCESS_TOKEN = "RgdlVa2/M981fASPei1fz+p8VxMMltZDC3MyZKrfqiHo59UsZye5LmSJx2v7wc8+DT4VxlnVL9RSOlpTQRtFDfj8IIt6jgBLyjj/E/EuepWi3ymkVRg44h72q3NcTGje3vTDHKzPuWYNnrd8OVx1JAdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "fe71e2480dfcac451b531659e5336652"           # << ใส่จาก LINE Developers

CSV_FILE = "usage_stats.csv"

app = Flask(__name__)
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ================= HELPER ================= #
def get_latest_status():
    """อ่านข้อมูลล่าสุดจาก usage_stats.csv"""
    if not os.path.exists(CSV_FILE):
        return "⚠️ ไม่มีข้อมูลในระบบ", None

    df = pd.read_csv(CSV_FILE)
    if df.empty:
        return "⚠️ ไฟล์ CSV ว่างเปล่า", None

    latest = df.iloc[-1]  # แถวล่าสุด
    ts = latest["timestamp"]
    people = int(latest["people_count"])
    tables = int(latest["table_used"])
    table_total = int(latest["table_total"])

    text = f"📅 เวลา: {ts}\n👥 คน: {people}\n🪑 โต๊ะ: {tables}/{table_total}"

    return text, df


def generate_graph(df):
    """สร้างกราฟคนในห้อง 6 ชั่วโมงล่าสุด"""
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    except Exception:
        return None

    # เลือกข้อมูล 6 ชั่วโมงล่าสุด
    cutoff = datetime.now() - timedelta(hours=6)
    df_recent = df[df["timestamp"] >= cutoff]

    if df_recent.empty:
        return None

    # วาดกราฟ
    plt.figure(figsize=(6, 3))
    plt.plot(df_recent["timestamp"], df_recent["people_count"], marker="o", label="People")
    plt.plot(df_recent["timestamp"], df_recent["table_used"], marker="s", label="Tables Used")
    plt.xlabel("Time")
    plt.ylabel("Count")
    plt.title("Co-working Space (last 6h)")
    plt.legend()
    plt.xticks(rotation=30)
    plt.tight_layout()

    img_path = "latest_graph.png"
    plt.savefig(img_path)
    plt.close()

    return img_path


# ================= ROUTES ================= #
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


# ================= EVENT HANDLER ================= #
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    if user_text == "เช็คห้อง CO":
        reply_text, df = get_latest_status()

        if df is not None:
            graph_path = generate_graph(df)
            if graph_path:
                # ส่งข้อความ + รูปกราฟ
                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        TextSendMessage(text=reply_text),
                        ImageSendMessage(
                            original_content_url=f"https://{os.getenv('NGROK_URL')}/static/{graph_path}",
                            preview_image_url=f"https://{os.getenv('NGROK_URL')}/static/{graph_path}"
                        )
                    ]
                )
                return

        # ถ้าไม่มีกราฟ → ส่งข้อความอย่างเดียว
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

    else:
        # กรณีข้อความอื่น
        reply_text = f"คุณพิมพ์ว่า: {user_text}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))


# ================= MAIN ================= #
if __name__ == "__main__":
    # ให้ Flask เสิร์ฟไฟล์ static (รูปกราฟ)
    static_dir = os.path.join(os.getcwd(), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.static_folder = static_dir
    app.run(port=5000, debug=True)