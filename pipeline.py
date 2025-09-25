import subprocess
import time
import os
from pathlib import Path
from datetime import datetime
import sys

# ---------------- CONFIG ---------------- #
BASE_DIR = Path(os.getcwd())
DOWNLOAD_FILE = BASE_DIR / "download_from_drive.py"
TEST_FILE = BASE_DIR / "test.py"

# ---------------- RUN COMMAND ---------------- #
def run_command(cmd, cwd=BASE_DIR):
    """Run command and stream logs (UTF-8 safe)."""
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"  # ✅ ป้องกัน error encoding
    )

    for line in process.stdout:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {line}", end="")

    process.wait()
    return process.returncode

# ---------------- MAIN ---------------- #
def main():
    print(f"===== PIPELINE START {datetime.now()} =====")

    # 1) ดาวน์โหลดไฟล์ใหม่จาก Google Drive
    ret = run_command([sys.executable, str(DOWNLOAD_FILE)])
    if ret != 0:
        print("❌ download_from_drive.py failed.")
        return

    # 2) รัน YOLO ตรวจจับและบันทึกลง CSV
    ret = run_command([sys.executable, str(TEST_FILE)])
    if ret != 0:
        print("❌ test.py failed.")
        return

    print(f"===== PIPELINE END {datetime.now()} =====")

if __name__ == "__main__":
    main()
