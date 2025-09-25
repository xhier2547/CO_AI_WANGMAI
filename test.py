from ultralytics import YOLO
from pathlib import Path
import pandas as pd
from datetime import datetime

BASE_DIR = Path.cwd()
INPUT_FOLDER = BASE_DIR / "images"
OUTPUT_FOLDER = BASE_DIR / "outputs"
PROCESSED_FOLDER = BASE_DIR / "processed"
CSV_FILE = BASE_DIR / "usage_stats.csv"

OUTPUT_FOLDER.mkdir(exist_ok=True)
PROCESSED_FOLDER.mkdir(exist_ok=True)

# โหลดโมเดล YOLO
model = YOLO("yolov8x.pt")

def parse_timestamp_from_filename(filename: str):
    base = Path(filename).stem
    parts = base.split("_")
    if len(parts) >= 3:
        ts = parts[1] + parts[2]
        return datetime.strptime(ts, "%Y%m%d%H%M%S")
    return datetime.now()

def process_image(img_path: Path):
    results = model.predict(str(img_path), save=True, project=OUTPUT_FOLDER, name="", exist_ok=True, verbose=False)

    people = sum(1 for r in results for c in r.boxes.cls if model.names[int(c)] == "person")
    tables_used = sum(1 for r in results for c in r.boxes.cls if "table" in model.names[int(c)].lower())

    row = {
        "timestamp": parse_timestamp_from_filename(img_path.name).strftime("%Y-%m-%d %H:%M:%S"),
        "people_count": people,
        "table_used": tables_used,
        "table_total": 7,
        "filename": img_path.name
    }

    df = pd.DataFrame([row])
    df.to_csv(CSV_FILE, mode="a", header=not CSV_FILE.exists(), index=False)
    img_path.rename(PROCESSED_FOLDER / img_path.name)
    print(f"✅ {img_path.name} → People={people}, Tables={tables_used}/7")

def main():
    for img in sorted(INPUT_FOLDER.glob("*.jpg")):
        process_image(img)

if __name__ == "__main__":
    main()
