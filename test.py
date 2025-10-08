import os
import pandas as pd
from pathlib import Path
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator
from datetime import datetime
import torch
from PIL import Image
import numpy as np
import cv2

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
model_people = YOLO("yolov8x.pt")     # detect only people
model_table = YOLO("table.pt")        # custom-trained table
model_beanbag = YOLO("beanbag.pt")    # custom-trained beanbag

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

def analyze_table_usage(image, box):
    """วิเคราะห์โต๊ะว่ามีของวางไหม (ถ้ามีของวาง >30% ของพื้นที่ = ใช้งาน)"""
    x1, y1, x2, y2 = map(int, box)
    crop = np.array(image)[y1:y2, x1:x2]
    if crop.size == 0:
        return False
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 60, 255])
    mask = cv2.inRange(hsv, lower_white, upper_white)
    white_ratio = mask.sum() / 255 / (mask.shape[0] * mask.shape[1] + 1e-6)
    return white_ratio < 0.7  # True = มีของวางเกิน 30%

def bbox_iou(box1, box2):
    """คำนวณ IoU ระหว่าง 2 กล่อง"""
    x1, y1, x2, y2 = box1
    x1b, y1b, x2b, y2b = box2
    xi1, yi1 = max(x1, x1b), max(y1, y1b)
    xi2, yi2 = min(x2, x2b), min(y2, y2b)
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (x2b - x1b) * (y2b - y1b)
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area if union_area else 0

def center_in_box(center, box):
    """ตรวจว่าจุดศูนย์กลางคนอยู่ใน beanbag ไหม"""
    x, y = center
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2

# ---------------- CORE LOGIC ---------------- #
def process_image(img_path: Path):
    im = Image.open(img_path).convert("RGB")

    # === Run All Models === #
    results_people = model_people.predict(source=str(img_path), save=False, verbose=False)
    results_table = model_table.predict(source=str(img_path), save=False, verbose=False)
    results_beanbag = model_beanbag.predict(source=str(img_path), save=False, verbose=False)

    annotator = Annotator(im)
    people_boxes, table_boxes, beanbag_boxes = [], [], []

    # ---------------- PEOPLE ---------------- #
    for r in results_people:
        for box, cls_id, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            if model_people.names[int(cls_id)].lower() == "person":
                box = box.tolist()
                conf = float(conf)
                people_boxes.append(box)
                annotator.box_label(box, f"person {conf*100:.1f}%", color=(0, 255, 0))

    # ---------------- TABLE ---------------- #
    for r in results_table:
        for box, cls_id, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            if "table" in model_table.names[int(cls_id)].lower():
                box = box.tolist()
                conf = float(conf)
                table_boxes.append((box, conf))

    # ---------------- BEANBAG ---------------- #
    for r in results_beanbag:
        for box, cls_id, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            if "beanbag" in model_beanbag.names[int(cls_id)].lower():
                box = box.tolist()
                conf = float(conf)
                beanbag_boxes.append((box, conf))

    # === TABLE LOGIC === #
    tables_total = len(table_boxes)
    tables_used = 0
    for box, conf in table_boxes:
        used = analyze_table_usage(im, box)
        color = (0, 200, 255) if used else (150, 150, 150)
        status = "USED" if used else "FREE"
        annotator.box_label(box, f"table {status} {conf*100:.1f}%", color=color)
        if used:
            tables_used += 1

    # === BEANBAG LOGIC === #
    beanbags_total = len(beanbag_boxes)
    beanbags_used = 0
    for b_box, conf in beanbag_boxes:
        used = False
        for p_box in people_boxes:
            iou = bbox_iou(b_box, p_box)
            px1, py1, px2, py2 = p_box
            person_center = ((px1 + px2) / 2, (py1 + py2) / 2)
            if iou > 0.2 or center_in_box(person_center, b_box):
                used = True
                break
        color = (255, 0, 0) if used else (120, 120, 255)
        status = "USED" if used else "FREE"
        annotator.box_label(b_box, f"beanbag {status} {conf*100:.1f}%", color=color)
        if used:
            beanbags_used += 1

    # === PEOPLE COUNT === #
    people_count = len(people_boxes)

    # === SAVE OUTPUT === #
    save_path = OUTPUT_FOLDER / img_path.name
    Image.fromarray(annotator.result()).save(save_path)

    ts = parse_timestamp_from_filename(img_path.name)
    row = {
        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "people_count": people_count,
        "table_used": tables_used,
        "table_total": tables_total,
        "beanbag_used": beanbags_used,
        "beanbag_total": beanbags_total,
        "filename": img_path.name
    }

    file_exists = CSV_FILE.exists()
    pd.DataFrame([row]).to_csv(CSV_FILE, mode="a", header=not file_exists, index=False)

    # ✅ ป้องกัน error จากไฟล์ชื่อซ้ำใน processed/
    target_path = PROCESSED_FOLDER / img_path.name
    if target_path.exists():
        new_name = f"{target_path.stem}_{datetime.now().strftime('%H%M%S')}{target_path.suffix}"
        target_path = PROCESSED_FOLDER / new_name

    img_path.rename(target_path)

    print(f"✅ {img_path.name}: 👥 {people_count} | 🪑 Table {tables_used}/{tables_total} | 🛋 Beanbag {beanbags_used}/{beanbags_total}")

# ---------------- MAIN ---------------- #
def main():
    images = sorted(INPUT_FOLDER.glob("*.jpg"))
    if not images:
        print("⚠️ No images found in input folder.")
        return
    for img in images:
        process_image(img)

if __name__ == "__main__":
    print("🚀 COAI Ultra Smart Detector Starting...")
    main()
    print("✅ All images processed successfully.")
