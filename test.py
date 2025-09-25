import os
import pandas as pd
from pathlib import Path
from ultralytics import YOLO
from datetime import datetime
import torch
from PIL import Image

# ---------------- CONFIG ---------------- #
BASE_DIR = Path(os.getcwd())
INPUT_FOLDER = BASE_DIR / "images"
OUTPUT_FOLDER = BASE_DIR / "outputs"
PROCESSED_FOLDER = BASE_DIR / "processed"
CSV_FILE = BASE_DIR / "usage_stats.csv"
TABLES_FILE = BASE_DIR / "tables.json"

OUTPUT_FOLDER.mkdir(exist_ok=True)
PROCESSED_FOLDER.mkdir(exist_ok=True)

# ---------------- FIX TORCH SAFE GLOBALS ---------------- #
# ✅ allowlist classes/modules ที่ YOLO ใช้
torch.serialization.add_safe_globals([
    torch.nn.Sequential,
    torch.nn.Conv2d,
    torch.nn.BatchNorm2d,
    torch.nn.ReLU,
    torch.nn.SiLU,
    torch.nn.modules.container.Sequential,
])

try:
    from ultralytics.nn.modules import Conv
    torch.serialization.add_safe_globals([Conv])
except ImportError:
    pass

# ---------------- LOAD YOLO MODEL ---------------- #
model = YOLO("yolov8x.pt")

# ---------------- HELPER FUNCTIONS ---------------- #
def parse_timestamp_from_filename(filename: str):
    try:
        # ตัวอย่าง IMG_20250911_164346.jpg
        base = Path(filename).stem
        parts = base.split("_")
        if len(parts) >= 3:
            ts = parts[1] + parts[2]  # YYYYMMDD + HHMMSS
            return datetime.strptime(ts, "%Y%m%d%H%M%S")
    except Exception:
        pass
    return datetime.now()

def process_image(img_path: Path):
    results = model.predict(
        source=str(img_path),
        save=True,
        project=OUTPUT_FOLDER,
        name="",
        exist_ok=True,
        verbose=False
    )

    # ดึงผลลัพธ์จาก YOLO
    people = 0
    tables_used = 0
    tables_total = 7   # สมมุติว่ามีโต๊ะทั้งหมด 7
    beanbags_used = 0
    beanbags_total = 0

    for r in results:
        for c in r.boxes.cls:
            cls_name = model.names[int(c)]
            if cls_name.lower() == "person":
                people += 1
            elif "table" in cls_name.lower():
                tables_used += 1
            elif "beanbag" in cls_name.lower():
                beanbags_used += 1

    # ใช้ timestamp จากชื่อไฟล์
    ts = parse_timestamp_from_filename(img_path.name)

    # append ลง CSV
    row = {
        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "people_count": people,
        "table_used": tables_used,
        "table_total": tables_total,
        "beanbag_used": beanbags_used,
        "beanbag_total": beanbags_total,
        "filename": img_path.name
    }

    file_exists = CSV_FILE.exists()
    df = pd.DataFrame([row])
    df.to_csv(CSV_FILE, mode="a", header=not file_exists, index=False)

    # ย้ายไฟล์เข้า processed
    img_path.rename(PROCESSED_FOLDER / img_path.name)

    print(f"✅ Processed {img_path.name}: People={people}, Tables={tables_used}/{tables_total}")

# ---------------- MAIN ---------------- #
def main():
    images = sorted(INPUT_FOLDER.glob("*.jpg"))
    if not images:
        print("⚠️ No images found in input folder.")
        return
    for img in images:
        process_image(img)

if __name__ == "__main__":
    main()
