import os
import pandas as pd
from pathlib import Path
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator
from datetime import datetime
import torch
from PIL import Image

# ---------------- CONFIG ---------------- #
BASE_DIR = Path(os.getcwd())
INPUT_FOLDER = BASE_DIR / "images"
OUTPUT_FOLDER = BASE_DIR / "outputs"
PROCESSED_FOLDER = BASE_DIR / "processed"
CSV_FILE = BASE_DIR / "usage_stats.csv"

OUTPUT_FOLDER.mkdir(exist_ok=True)
PROCESSED_FOLDER.mkdir(exist_ok=True)

# ---------------- FIX TORCH SAFE GLOBALS ---------------- #
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

# ---------------- LOAD YOLO MODELS ---------------- #
model_people_table = YOLO("yolov8x.pt")   # detect person + table
model_beanbag = YOLO("best.pt")           # detect beanbag


# ---------------- HELPER FUNCTIONS ---------------- #
def parse_timestamp_from_filename(filename: str):
    try:
        base = Path(filename).stem
        parts = base.split("_")
        if len(parts) >= 3:
            ts = parts[1] + parts[2]  # YYYYMMDD + HHMMSS
            return datetime.strptime(ts, "%Y%m%d%H%M%S")
    except Exception:
        pass
    return datetime.now()


def process_image(img_path: Path):
    # run prediction (ไม่เซฟอัตโนมัติ)
    results_people_table = model_people_table.predict(
        source=str(img_path), save=False, verbose=False
    )
    results_beanbag = model_beanbag.predict(
        source=str(img_path), save=False, verbose=False
    )

    # counts
    people, tables_used, tables_total = 0, 0, 7
    beanbags_used, beanbags_total = 0, 8

    # โหลดภาพต้นฉบับเพื่อวาดผลรวม
    im = Image.open(img_path).convert("RGB")
    annotator = Annotator(im)

    # จาก yolov8x (person + table)
    for r in results_people_table:
        for box, cls_id in zip(r.boxes.xyxy, r.boxes.cls):
            cls_name = model_people_table.names[int(cls_id)]
            if cls_name.lower() == "person":
                people += 1
            elif "table" in cls_name.lower():
                tables_used += 1
            # วาด bounding box
            annotator.box_label(box, cls_name, color=(0, 255, 0))

    # จาก best.pt (beanbag)
    for r in results_beanbag:
        for box, cls_id in zip(r.boxes.xyxy, r.boxes.cls):
            cls_name = model_beanbag.names[int(cls_id)]
            if "beanbag" in cls_name.lower():
                beanbags_used += 1
            # วาด bounding box
            annotator.box_label(box, cls_name, color=(255, 0, 0))

    # เซฟภาพรวม
    save_path = OUTPUT_FOLDER / img_path.name
    annotator.result().save(save_path)

    # timestamp
    ts = parse_timestamp_from_filename(img_path.name)

    # append CSV
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

    # move processed file
    img_path.rename(PROCESSED_FOLDER / img_path.name)

    print(f"✅ {img_path.name}: People={people}, Tables={tables_used}/{tables_total}, Beanbags={beanbags_used}/{beanbags_total}")


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
