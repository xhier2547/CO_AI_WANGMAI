import sys, os
sys.path.append("/app")
sys.path.append("/opt/airflow/dags")

import subprocess, hashlib, traceback
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator  # ✅ เพิ่ม import
from airflow.models.variable import Variable

# =========================================================
# 🧱 DEFAULT CONFIG
# =========================================================
default_args = {
    "owner": "co-ai",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2025, 1, 1),
}

CSV_FILE = "/app/usage_stats.csv"
HASH_FILE = "/app/forecast/last_csv_hash.txt"

# =========================================================
# 🧩 CSV HASH CHECK
# =========================================================
def get_file_hash(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def is_csv_changed():
    current_hash = get_file_hash(CSV_FILE)
    last_hash = None
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_hash = f.read().strip()

    if current_hash != last_hash:
        print("📊 Detected CSV update → re-run forecast.")
        with open(HASH_FILE, "w") as f:
            f.write(current_hash or "")
        return True
    else:
        print("🟢 CSV not changed → skip forecast.")
        return False

# =========================================================
# 🪣 DOWNLOAD + DETECTION
# =========================================================
def run_download():
    print("[AIRFLOW] Starting: download_from_drive.py")
    try:
        from download_from_drive import download_files
        download_files()
        print("[AIRFLOW] ✅ Download complete")
    except Exception as e:
        print("[AIRFLOW] ❌ Download failed:", e)
        traceback.print_exc()
        raise e

def run_detection():
    print("[AIRFLOW] Running: test.py (YOLO detection)")
    from test import main as detect_main
    detect_main()
    print("[AIRFLOW] ✅ Detection complete")

# =========================================================
# 🧠 SMART FORECAST
# =========================================================
def run_forecast(model_name):
    if not is_csv_changed():
        print(f"[AIRFLOW] ⚙️ Skip {model_name} → no CSV change.")
        return
    print(f"[AIRFLOW] 🔮 Running Forecast: {model_name}")
    cmd = ["python", "/app/forecast/forecasting_analysis.py", "--model", model_name]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception(f"{model_name} forecast failed!")

# =========================================================
# 📈 DASHBOARD / LINE BOT PERSISTENT
# =========================================================
def ensure_dashboard_running():
    if os.system("pgrep -f 'streamlit run /app/dashboard.py' > /dev/null 2>&1") == 0:
        print("[AIRFLOW] 🟢 Dashboard already running.")
        return
    subprocess.Popen(
        ["streamlit", "run", "/app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
    )
    print("[AIRFLOW] 🚀 Dashboard launched.")

def ensure_linebot_running():
    # --- ✨ 2. ดึง API KEY จาก AIRFLOW VARIABLE ---
    # ใช้ .get(key, default_value) เพื่อไม่ให้ DAG พังถ้ายังไม่ได้ตั้งค่า
    groq_api_key = Variable.get("GROQ_API_KEY", default_var=None)
    
    if not groq_api_key:
        print("[AIRFLOW] ⚠️ WARNING: GROQ_API_KEY is not set in Airflow Variables. LLM will not work.")
        # ถ้าไม่ต้องการให้รันเลยถ้าไม่มี key ให้ raise Exception แทน
        # raise ValueError("GROQ_API_KEY is not set in Airflow Variables.")

    # --- ✨ 3. สร้าง ENVIRONMENT สำหรับ SUBPROCESS ---
    # คัดลอก environment ปัจจุบันของ Airflow มาก่อน
    bot_env = os.environ.copy()
    # เพิ่ม/อัปเดต key ของเราเข้าไป
    if groq_api_key:
        bot_env["GROQ_API_KEY"] = groq_api_key
        print("[AIRFLOW] 🔑 GROQ_API_KEY loaded successfully.")

    # --- ✨ 4. รัน SUBPROCESS พร้อมกับ ENVIRONMENT ที่กำหนด ---
    if os.system("pgrep -f 'python /app/line_bot.py' > /dev/null 2>&1") == 0:
        print("[AIRFLOW] 🟢 LINE Bot already running.")
        return
        
    # ส่ง bot_env เข้าไปใน Popen ผ่าน argument `env`
    subprocess.Popen(["python", "/app/line_bot.py"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, env=bot_env)
    subprocess.Popen(["python", "/app/setup_richmenu.py"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print("[AIRFLOW] 💬 LINE Bot launched.")

# =========================================================
# 🧩 DAG DEFINITION (อัปเดต)
# =========================================================
with DAG(
    dag_id="coworking_pipeline",
    default_args=default_args,
    description="Co-AI Pipeline: Smart Forecast ONLY", # แก้ไข description
    schedule_interval=timedelta(minutes=10),
    catchup=False,
    max_active_runs=1,
) as dag:

    start_task = DummyOperator(task_id="start")
    end_task = DummyOperator(task_id="end")

    download_task = PythonOperator(
        task_id="download_images",
        python_callable=run_download,
    )

    detect_task = PythonOperator(
        task_id="detect_objects",
        python_callable=run_detection,
    )
    
    # ✨ ใช้ DummyOperator เพื่อรวมผล forecast ก่อนจบ
    join_forecasts = DummyOperator(task_id="join_forecasts")

    # 🔗 DAG FLOW (ปรับปรุงใหม่)
    start_task >> download_task >> detect_task
    
    # รัน forecast ทั้ง 3 แบบขนานกัน
    detect_task >> [
        PythonOperator(task_id="forecast_arima", python_callable=lambda: run_forecast("ARIMA")),
        PythonOperator(task_id="forecast_sarima", python_callable=lambda: run_forecast("SARIMA")),
        PythonOperator(task_id="forecast_sarimax", python_callable=lambda: run_forecast("SARIMAX")),
    ] >> join_forecasts >> end_task
