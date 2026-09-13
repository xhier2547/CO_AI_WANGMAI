# =========================================================
#           ไฟล์: line_bot.py
#         ฉบับปรับปรุงและแก้ไข (ล่าสุด)
# =========================================================

import os
import sys
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import locale # ✨ NEW: เพิ่มการ import locale

# --- ✨ NEW: ตั้งค่า Locale ให้รองรับภาษาไทย ---
# บรรทัดนี้จะบอกให้ Python รู้จักการจัดการวันที่และเวลาที่เป็นภาษาไทย
# เพื่อป้องกัน 'locale' codec can't encode error บน Windows
try:
    locale.setlocale(locale.LC_ALL, 'th_TH.UTF-8')
except locale.Error:
    print("Warning: 'th_TH.UTF-8' locale not supported. Using default system locale.")

# --- ส่วนเชื่อมต่อ LLM ---
try:
    from groq import Groq
except ImportError:
    print("Warning: 'groq' library not found. LLM features will be disabled.")
    print("Please install it using: pip install groq")
    Groq = None

sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------- CONFIG ---------------- #
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN", "")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# --- Path ของไฟล์ข้อมูล (ปรับเป็น Relative Path) ---
HISTORICAL_FILE = "usage_stats.csv"
FORECAST_FILE = "outputs_forecast/forecast_results_extended.csv"

# --- เริ่มการเชื่อมต่อ Services ---
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
app = Flask(__name__)

# --- เริ่มการเชื่อมต่อ LLM Client ---
llm_client = None
if Groq and GROQ_API_KEY and GROQ_API_KEY != "YOUR_GROQ_API_KEY":
    try:
        llm_client = Groq(api_key=GROQ_API_KEY)
        print("🤖 LLM client (Groq) initialized successfully.")
    except Exception as e:
        print(f"❌ Error initializing Groq client: {e}")
else:
    print("⚠️ LLM client is not configured. GROQ_API_KEY is missing or 'groq' library is not installed.")


# --- ข้อมูลสำหรับฟีเจอร์แนะนำวัน ---
THAI_DAY_MAP_ENG_TO_THAI = {
    "Monday": "วันจันทร์", "Tuesday": "วันอังคาร", "Wednesday": "วันพุธ",
    "Thursday": "วันพฤหัสบดี", "Friday": "วันศุกร์", "Saturday": "วันเสาร์", "Sunday": "วันอาทิตย์"
}
THAI_DAY_KEYWORDS_MAP = {}
for eng, thai in THAI_DAY_MAP_ENG_TO_THAI.items():
    THAI_DAY_KEYWORDS_MAP[thai] = eng
    THAI_DAY_KEYWORDS_MAP[thai.replace("วัน", "")] = eng

# ---------------- FUNCTIONS (ไม่มีการเปลี่ยนแปลง) ---------------- #

def get_latest_status():
    if not os.path.exists(HISTORICAL_FILE):
        return "⚠️ ขออภัยครับ ยังไม่มีข้อมูลสถานะปัจจุบันในระบบ"
    try:
        df = pd.read_csv(HISTORICAL_FILE)
        if df.empty: return "⚠️ ยังไม่มีข้อมูลสถานะปัจจุบันในระบบ"
        latest = df.iloc[-1]
        ts = pd.to_datetime(latest["timestamp"]).strftime('%Y-%m-%d %H:%M')
        people = int(latest["people_count"])
        tables = f"{int(latest.get('table_used', 0))}/{int(latest.get('table_total', 10))}"
        beanbags = f"{int(latest.get('beanbag_used', 0))}/{int(latest.get('beanbag_total', 5))}"
        return (
            f"📊 สถานะล่าสุด ห้อง Co-AI ({ts}) 📊\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 จำนวนคน: {people}\n"
            f"🪑 การใช้โต๊ะ: {tables}\n"
            f"🛋️ การใช้ Beanbag: {beanbags}"
        )
    except Exception as e:
        print(f"❌ Error in get_latest_status: {e}")
        return "เกิดข้อผิดพลาดในการอ่านข้อมูลสถานะล่าสุดครับ"

def get_forecast_info(query=None):
    if not os.path.exists(FORECAST_FILE):
        return "⚠️ ขออภัยครับ ยังไม่มีข้อมูลพยากรณ์ในระบบ"
    try:
        df = pd.read_csv(FORECAST_FILE, parse_dates=["timestamp"])
        model_to_show = next((col for col in ["SARIMAX", "SARIMA", "ARIMA"] if col in df.columns), None)
        if not model_to_show: return "⚠️ ไม่พบข้อมูลโมเดลพยากรณ์"

        if not query:
            now = datetime.now()
            future_df = df[df['timestamp'] >= now].copy()
            if future_df.empty: return "ไม่พบข้อมูลพยากรณ์สำหรับอนาคต"
            future_df.dropna(subset=[model_to_show], inplace=True)
            if future_df.empty: return "ข้อมูลพยากรณ์สำหรับอนาคตไม่สมบูรณ์"
            peak_time_row = future_df.loc[future_df[model_to_show].idxmax()]
            peak_time = peak_time_row['timestamp'].strftime('%d/%m %H:%M น.')
            peak_people = int(float(peak_time_row[model_to_show]))
            return (
                f"🔮 พยากรณ์ภาพรวม (โดย {model_to_show}) 🔮\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"ช่วงเวลาที่คาดว่าคนจะ *เยอะที่สุด* คือประมาณ *{peak_time}*\n"
                f"โดยคาดว่าจะมีประมาณ *{peak_people}* คนครับ"
            )
        else:
            hour = int(query)
            if not (0 <= hour <= 23): raise ValueError
            now = datetime.now()
            target_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if target_time < now: target_time += timedelta(days=1)
            closest_row = df.iloc[(df['timestamp'] - target_time).abs().argsort()[0]]
            pred_time = closest_row['timestamp'].strftime('%d/%m %H:%M')
            pred_people = int(float(closest_row[model_to_show]))
            return (
                f"🔮 ผลพยากรณ์สำหรับเวลาใกล้เคียง (โดย {model_to_show}) 🔮\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ เวลา: *{pred_time}*\n"
                f"👤 คาดว่าจะมีคนประมาณ: *{pred_people}* คนครับ"
            )
    except ValueError:
        return "โปรดระบุเวลาเป็นตัวเลข 0-23 นะครับ เช่น 'พยากรณ์ 14'"
    except Exception as e:
        print(f"❌ Error in get_forecast_info: {e}")
        return "เกิดข้อผิดพลาดในการอ่านข้อมูลพยากรณ์ครับ"

def get_best_time_for_day(day_keyword):
    if not os.path.exists(FORECAST_FILE):
        return "⚠️ ขออภัยครับ ยังไม่มีข้อมูลพยากรณ์ในระบบ"
    try:
        day_in_english = THAI_DAY_KEYWORDS_MAP.get(day_keyword)
        if not day_in_english: return f"ขออภัยครับ ไม่รู้จัก '{day_keyword}'"

        df = pd.read_csv(FORECAST_FILE, parse_dates=["timestamp"])
        model_to_show = next((col for col in ["SARIMAX", "SARIMA", "ARIMA"] if col in df.columns), None)
        if not model_to_show: return "⚠️ ไม่พบข้อมูลโมเดลพยากรณ์"

        day_df = df[df['timestamp'].dt.day_name() == day_in_english].copy()
        day_df.dropna(subset=[model_to_show], inplace=True)
        if day_df.empty: return f"ขออภัยครับ ไม่มีข้อมูลพยากรณ์สำหรับ{day_keyword}"

        min_time_row = day_df.loc[day_df[model_to_show].idxmin()]
        best_time = min_time_row['timestamp'].strftime('%H:%M น.')
        min_people = int(float(min_time_row[model_to_show]))
        return (
            f"💡 {day_keyword}น่าเข้าใช้งานที่สุดเวลาประมาณ *{best_time}* ครับ\n"
            f"คาดว่าจะมีคนประมาณ *{min_people}* คน (น้อยที่สุด)"
        )
    except Exception as e:
        print(f"❌ Error in get_best_time_for_day: {e}")
        return "เกิดข้อผิดพลาดในการให้คำแนะนำครับ"

def get_recommended_day():
    if not os.path.exists(FORECAST_FILE):
        return "⚠️ ขออภัยครับ ยังไม่มีข้อมูลพยากรณ์ในระบบ"
    try:
        df = pd.read_csv(FORECAST_FILE, parse_dates=["timestamp"])
        model_to_show = next((col for col in ["SARIMAX", "SARIMA", "ARIMA"] if col in df.columns), None)
        if not model_to_show: return "⚠️ ไม่พบข้อมูลโมเดลพยากรณ์"
        df['day_of_week'] = df['timestamp'].dt.day_name()
        avg_by_day = df.groupby('day_of_week')[model_to_show].mean()
        if avg_by_day.empty:
             return "ขออภัยครับ ข้อมูลพยากรณ์ไม่เพียงพอที่จะให้คำแนะนำ"
        best_day_english = avg_by_day.idxmin()
        best_day_thai = THAI_DAY_MAP_ENG_TO_THAI.get(best_day_english, best_day_english)
        return (
            f"💡 วันที่แนะนำที่สุด (โดย {model_to_show}) 💡\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"จากข้อมูลพยากรณ์ทั้งหมด วันที่คนน้อยที่สุดโดยเฉลี่ยคือ **{best_day_thai}** ครับ"
        )
    except Exception as e:
        print(f"❌ Error in get_recommended_day: {e}")
        return "เกิดข้อผิดพลาดในการคำนวณเพื่อหาคำแนะนำครับ"

def ask_llm(user_prompt):
    if not llm_client:
        return (
            "สวัสดีครับ 👋 ลองใช้คำสั่งเหล่านี้ดูนะครับ:\n\n"
            "✅ `เช็คห้อง`\n"
            "🔮 `พยากรณ์`\n"
            "🕒 `พยากรณ์ 19`\n"
            "💡 `พยากรณ์วันจันทร์`\n"
            "⭐ `วันไหนดี`"
        )
    system_prompt = (
        "You are 'น้อง Co-AI', an assistant for a co-working space 'Co-AI WANGMAI'. "
        "Answer in Thai concisely and politely."
    )
    try:
        chat_completion = llm_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="llama-3.1-8b-instant", temperature=0.7
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Error calling LLM API: {e}")
        return "ขออภัยครับ เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI ผู้ช่วยครับ"

# ---------------- ROUTES (ไม่มีการเปลี่ยนแปลง) ---------------- #
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# ---------------- HANDLER (ไม่มีการเปลี่ยนแปลง) ---------------- #
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()
    user_text_lower = user_text.lower()
    reply_text = ""
    print(f"✅ Received: '{user_text}'")
    try:
        matched_day = next((day for day in THAI_DAY_KEYWORDS_MAP.keys() if day in user_text), None)
        if user_text_lower.startswith(('เช็คห้อง', 'สถานะ', 'status')) or user_text_lower == "co":
            reply_text = get_latest_status()
        elif any(keyword in user_text_lower for keyword in ['วันไหนดี', 'วันไหนว่าง', 'วันไหนน่าใช้', 'แนะนำวัน']):
            reply_text = get_recommended_day()
        elif user_text_lower.startswith(('พยากรณ์', 'forecast')) and matched_day:
            reply_text = get_best_time_for_day(matched_day)
        elif user_text_lower.startswith(('พยากรณ์', 'forecast')):
            time_query = "".join(re.findall(r'\d+', user_text))
            reply_text = get_forecast_info(time_query if time_query else None)
        elif matched_day:
            reply_text = get_best_time_for_day(matched_day)
        else:
            reply_text = ask_llm(user_text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        print(f"✔️ Replied successfully.")
    except Exception as e:
        print(f"❌❌ CRITICAL ERROR: {e}")
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ขออภัยค่ะ เกิดข้อผิดพลาดภายในระบบ"))
        except Exception as api_error:
            print(f"❌❌ FAILED TO SEND ERROR MSG: {api_error}")

# ---------------- MAIN (ไม่มีการเปลี่ยนแปลง) ---------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("--- Checking for required files ---")
    if os.path.exists(HISTORICAL_FILE): print(f"   - ✅ Found '{HISTORICAL_FILE}'")
    else: print(f"   - ⚠️  WARNING: '{HISTORICAL_FILE}' not found.")
    if os.path.exists(FORECAST_FILE): print(f"   - ✅ Found '{FORECAST_FILE}'")
    else: print(f"   - ⚠️  WARNING: '{FORECAST_FILE}' not found.")
    print("---------------------------------")
    print(f"🚀 Starting Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)