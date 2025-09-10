from ultralytics import YOLO
import cv2
import json
import csv
import os
import shutil
from datetime import datetime

# ---------------- CONFIG ---------------- #
MODEL_PATH = "yolov8s.pt"
INPUT_FOLDER = "images/"
OUTPUT_FOLDER = "outputs/"
PROCESSED_FOLDER = "processed/"
COCO_JSON = "tables.json"
CSV_FILE = "usage_stats.csv"

CONF_THRESHOLD = 0.3
IOU_THRESHOLD = 0.2

# โหลด YOLOv8
model = YOLO(MODEL_PATH)
CLASS_NAMES = model.names

# โหลด bounding box โต๊ะจาก JSON
with open(COCO_JSON, "r", encoding="utf-8") as f:
    coco = json.load(f)

TABLES = []
for ann in coco["annotations"]:
    if ann["category_id"] == 1:  # 1 = table
        x, y, w, h = ann["bbox"]
        TABLES.append({
            "id": ann["id"],
            "x1": int(x),
            "y1": int(y),
            "x2": int(x + w),
            "y2": int(y + h)
        })

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# ---------------- HELPER ---------------- #
def iou(boxA, boxB):
    xA, yA = max(boxA[0], boxB[0]), max(boxA[1], boxB[1])
    xB, yB = min(boxA[2], boxB[2]), min(boxA[3], boxB[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    if inter == 0:
        return 0.0
    areaA = (boxA[2]-boxA[0]) * (boxA[3]-boxA[1])
    areaB = (boxB[2]-boxB[0]) * (boxB[3]-boxB[1])
    return inter / float(areaA + areaB - inter)

def process_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"⚠️ ไม่พบไฟล์ภาพ: {image_path}")
        return None

    results = model.predict(source=image_path, conf=CONF_THRESHOLD, verbose=False)

    # ---------------- DETECT PEOPLE ---------------- #
    people_boxes = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            if CLASS_NAMES[cls_id] == "person":
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                people_boxes.append((x1, y1, x2, y2))
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img, "person", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # ---------------- CHECK TABLE USAGE ---------------- #
    table_used = 0
    for table in TABLES:
        tbox = (table["x1"], table["y1"], table["x2"], table["y2"])
        used = any(iou(tbox, p) > IOU_THRESHOLD for p in people_boxes)
        color = (0, 0, 255) if used else (255, 0, 0)
        label = f"Table {table['id']} {'USED' if used else 'FREE'}"
        cv2.rectangle(img, (tbox[0], tbox[1]), (tbox[2], tbox[3]), color, 2)
        cv2.putText(img, label, (tbox[0], tbox[1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if used:
            table_used += 1

    # ---------------- SAVE RESULT ---------------- #
    people_count = len(people_boxes)
    table_total = len(TABLES)
    beanbag_used, beanbag_total = 0, 0

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = os.path.basename(image_path)
    output_img_path = os.path.join(OUTPUT_FOLDER, f"detect_{filename}")
    cv2.imwrite(output_img_path, img)

    # ✅ cast int ทุกค่า ก่อนเขียน CSV
    return [
        timestamp,
        int(people_count),
        int(table_used),
        int(table_total),
        int(beanbag_used),
        int(beanbag_total),
        output_img_path
    ]

# ---------------- MAIN ---------------- #
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "people_count", "table_used", "table_total",
            "beanbag_used", "beanbag_total", "output_image"
        ])

image_files = [os.path.join(INPUT_FOLDER, f) for f in os.listdir(INPUT_FOLDER)
               if f.lower().endswith((".jpg", ".jpeg", ".png"))]

if image_files:
    latest_file = max(image_files, key=os.path.getmtime)
    row = process_image(latest_file)
    if row:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        print(f"✅ Processed latest file: {os.path.basename(latest_file)} "
              f"People={row[1]}, Tables={row[2]}/{row[3]}")

        # ย้ายไฟล์ไป processed/
        dest_path = os.path.join(PROCESSED_FOLDER, os.path.basename(latest_file))
        shutil.move(latest_file, dest_path)
        print(f"📦 Moved {os.path.basename(latest_file)} → processed/")
else:
    print("⚠️ ไม่พบไฟล์ใน images/")
