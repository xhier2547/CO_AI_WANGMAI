import subprocess, time, os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(os.getcwd())

def run_command(cmd):
    """Run command and stream logs safely with UTF-8"""
    process = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",     # ✅ ป้องกัน emoji error
        errors="replace"      # ✅ ถ้าเจอตัวแปลกจะแทนด้วย ?
    )

    for line in process.stdout:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {line.strip()}")

    process.wait()
    return process.returncode

def main():
    print(f"===== PIPELINE START {datetime.now()} =====")
    
    # 1. ดาวน์โหลดรูปจาก Google Drive
    run_command(["python", str(BASE_DIR / "download_from_drive.py")])

    # 2. ประมวลผลภาพด้วย test.py
    run_command(["python", str(BASE_DIR / "test.py")])

    print(f"===== PIPELINE END {datetime.now()} =====")

if __name__ == "__main__":
    main()
