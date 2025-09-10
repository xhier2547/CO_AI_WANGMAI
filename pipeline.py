import subprocess
import os
from datetime import datetime

LOG_FILE = "scheduler_log.txt"

def run_command(command):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] >>> {' '.join(command)}\n")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            f.write(line)
        process.wait()
    return process.returncode

def main():
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n===== PIPELINE START {datetime.now()} =====\n")

    run_command(["python", "download_from_drive.py"])
    run_command(["python", "test.py"])

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"===== PIPELINE END {datetime.now()} =====\n")

if __name__ == "__main__":
    main()
