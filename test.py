import os
import pandas as pd
from pathlib import Path
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator
from datetime import datetime
from PIL import Image
import torch
import numpy as np
from torchvision import transforms, models
import shutil

# ---------------- CONFIG ---------------- #
BASE_DIR = Path(os.getcwd())
INPUT_FOLDER = BASE_DIR / "images"
OUTPUT_FOLDER = BASE_DIR / "outputs"
PROCESSED_FOLDER = BASE_DIR / "processed"
CSV_FILE = BASE_DIR / "usage_stats.csv"
CLASSIFIER_MODEL = BASE_DIR / "table_classifier.pt"

OUTPUT_FOLDER.mkdir(exist_ok=True)
PROCESSED_FOLDER.mkdir(exist_ok=True)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[INFO] Running on {DEVICE.upper()}")

# ---------------- LOAD YOLO MODELS ---------------- #
model_people = YOLO("yolov8x.pt").to(DEVICE)
model_table = YOLO("table.pt").to(DEVICE)
model_beanbag = YOLO("beanbag.pt").to(DEVICE)

# ---------------- LOAD TABLE CLASSIFIER ---------------- #
classifier = models.resnet18(pretrained=False)
classifier.fc = torch.nn.Linear(classifier.fc.in_features, 2)
state_dict = torch.load(CLASSIFIER_MODEL, map_location=DEVICE)
classifier.load_state_dict(state_dict)
classifier.to(DEVICE)
classifier.eval()

transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize([0.5]*3, [0.5]*3)
])

def classify_table(crop_img):
    try:
        img_t = transform(Image.fromarray(crop_img)).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            pred = classifier(img_t)
            cls = pred.argmax(dim=1).item()
        return "USED" if cls == 1 else "FREE"
    except Exception as e:
        print(f"⚠️ classify_table error: {e}")
        return "FREE"

# ---------------- HELPERS ---------------- #
def parse_timestamp_from_filename(filename: str):
    try:
        base = Path(filename).stem
        parts = base.split("_")
        if len(parts) >= 3:
            ts = parts[1] + parts[2]
            return datetime.strptime(ts, "%Y%m%d%H%M%S")
    except Exception:
        pass
    return datetime.now()

def bbox_iou(box1, box2):
    x1, y1, x2, y2 = box1
    x1b, y1b, x2b, y2b = box2
    xi1, yi1 = max(x1, x1b), max(y1, y1b)
    xi2, yi2 = min(x2, x2b), min(y2, y2b)
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    union_area = (x2 - x1)*(y2 - y1) + (x2b - x1b)*(y2b - y1b) - inter_area
    return inter_area / union_area if union_area else 0

def center_in_box(center, box):
    x, y = center
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2

def safe_crop(image, x1, y1, x2, y2):
    h, w = image.shape[:2]
    x1 = int(max(0, min(x1, w)))
    y1 = int(max(0, min(y1, h)))
    x2 = int(max(0, min(x2, w)))
    y2 = int(max(0, min(y2, h)))
    if x2 <= x1 or y2 <= y1:
        return None
    return image[y1:y2, x1:x2]

# ---------------- PROCESS IMAGE ---------------- #
def process_image(img_path: Path):
    im = Image.open(img_path).convert("RGB")
    annotator = Annotator(im)
    np_im = np.array(im)

    results_people = model_people.predict(str(img_path), device=DEVICE, verbose=False)
    results_table = model_table.predict(str(img_path), device=DEVICE, verbose=False)
    results_beanbag = model_beanbag.predict(str(img_path), device=DEVICE, verbose=False)

    people_boxes, table_boxes, beanbag_boxes = [], [], []

    # DETECT PEOPLE
    for r in results_people:
        for box, cls_id, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            if model_people.names[int(cls_id)] == "person":
                people_boxes.append(box.tolist())
                annotator.box_label(box.tolist(), f"person {conf*100:.1f}%", color=(0,255,0))

    # DETECT TABLE
    for r in results_table:
        for box, conf in zip(r.boxes.xyxy, r.boxes.conf):
            table_boxes.append(box.tolist())

    # DETECT BEANBAG
    for r in results_beanbag:
        for box, conf in zip(r.boxes.xyxy, r.boxes.conf):
            beanbag_boxes.append(box.tolist())

    # TABLE CLASSIFICATION
    tables_used = 0
    for box in table_boxes:
        x1, y1, x2, y2 = map(int, box)
        crop = safe_crop(np_im, x1, y1, x2, y2)
        if crop is None:
            continue
        state = classify_table(crop)
        color = (255,165,0) if state == "USED" else (150,150,150)
        annotator.box_label(box, f"table {state}", color=color)
        if state == "USED":
            tables_used += 1

    # BEANBAG CLASSIFICATION
    beanbags_used = 0
    for b_box in beanbag_boxes:
        used = False
        for p_box in people_boxes:
            iou = bbox_iou(b_box, p_box)
            px1, py1, px2, py2 = p_box
            center = ((px1+px2)/2, (py1+py2)/2)
            if iou > 0.2 or center_in_box(center, b_box):
                used = True
                break
        color = (255,0,0) if used else (120,120,255)
        status = "USED" if used else "FREE"
        annotator.box_label(b_box, f"beanbag {status}", color=color)
        if used:
            beanbags_used += 1

    # SUMMARY
    people_count = len(people_boxes)
    tables_total = len(table_boxes)
    beanbags_total = len(beanbag_boxes)

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
    print(f"✅ {img_path.name}: people={people_count} | tables={tables_used}/{tables_total} | beanbags={beanbags_used}/{beanbags_total}")

    # Move processed file
    target = PROCESSED_FOLDER / img_path.name
    if target.exists():
        target = target.with_name(f"{target.stem}_{datetime.now().strftime('%H%M%S')}{target.suffix}")
    shutil.copy2(img_path, target)
    img_path.unlink()

# ---------------- MAIN ---------------- #
def main():
    imgs = sorted(INPUT_FOLDER.glob("*.jpg"))
    for img in imgs:
        process_image(img)
    print("🏁 All images processed.")

if __name__ == "__main__":
    main()
