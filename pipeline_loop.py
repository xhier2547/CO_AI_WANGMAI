import subprocess, time, os
from datetime import datetime
from pathlib import Path

INTERVAL = 600  # 10 นาที (600 วินาที)

BASE_DIR = Path(os.getcwd())
PIPELINE_FILE = BASE_DIR / "pipeline.py"

def run_pipeline_once():
    """รัน pipeline ครั้งเดียวและ log ออกมา"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Running pipeline...")

    process = subprocess.Popen(
        ["python", str(PIPELINE_FILE)],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    for line in process.stdout:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {line}", end="")

    process.wait()

    if process.returncode == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Pipeline finished.\n")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Pipeline failed.\n")

if __name__ == "__main__":
    while True:
        run_pipeline_once()

        print(f"⏳ Waiting {INTERVAL//60} minutes until next run...\n")
        for remaining in range(INTERVAL, 0, -1):
            mins, secs = divmod(remaining, 60)
            print(f"   Next run in: {mins:02d}:{secs:02d}", end="\r")
            time.sleep(1)
        print()
