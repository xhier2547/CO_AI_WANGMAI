import subprocess, sys, os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(os.getcwd())

def run_command(cmd):
    process = subprocess.Popen(
        cmd,
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
    return process.returncode

def main():
    print(f"===== PIPELINE START {datetime.now()} =====")

    # 1) โหลดภาพใหม่จาก Google Drive
    run_command([sys.executable, str(BASE_DIR / "download_from_drive.py")])

    # 2) รัน detection (test.py)
    ret = run_command([sys.executable, str(BASE_DIR / "test.py")])
    if ret != 0:
        print("❌ test.py failed.")
    else:
        print("✅ test.py finished.")

    print(f"===== PIPELINE END {datetime.now()} =====")

if __name__ == "__main__":
    main()