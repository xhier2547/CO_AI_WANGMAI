import subprocess
import os
from datetime import datetime
from pathlib import Path

# กำหนด path หลักเป็นโฟลเดอร์ที่ pipeline.py อยู่
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "scheduler_log.txt"

def run_command(command):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] >>> {' '.join(command)}\n")
        process = subprocess.Popen(
            command,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",      # ✅ force decode เป็น UTF-8
            errors="replace"       # ✅ แทนตัวอักษรที่อ่านไม่ได้ด้วย �
        )
        for line in process.stdout:
            f.write(line)
        process.wait()
    return process.returncode


def main():
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n===== PIPELINE START {datetime.now()} =====\n")

    # ✅ เรียก script โดยอ้างอิงจาก BASE_DIR
    run_command(["python", str(BASE_DIR / "download_from_drive.py")])
    run_command(["python", str(BASE_DIR / "test.py")])

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"===== PIPELINE END {datetime.now()} =====\n")

if __name__ == "__main__":
    main()
