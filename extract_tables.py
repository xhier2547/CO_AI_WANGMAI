from ultralytics import YOLO
from pathlib import Path
from PIL import Image
import os

# CONFIG
MODEL_PATH = "table.pt"
INPUT_FOLDER = Path("images")
OUTPUT_FOLDER = Path("dataset_tables/raw")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# LOAD YOLO
model = YOLO(MODEL_PATH)

def extract_tables():
    images = sorted(INPUT_FOLDER.glob("*.jpg"))
    for img_path in images:
        results = model.predict(source=str(img_path), save=False, verbose=False)
        for r in results:
            for i, box in enumerate(r.boxes.xyxy):
                x1, y1, x2, y2 = map(int, box.tolist())
                im = Image.open(img_path).convert("RGB")
                crop = im.crop((x1, y1, x2, y2))
                save_path = OUTPUT_FOLDER / f"{img_path.stem}_table{i}.jpg"
                crop.save(save_path)
        print(f"✅ Extracted tables from {img_path.name}")

if __name__ == "__main__":
    extract_tables()
    print("🎯 Table extraction completed. Label the crops into 'free/' and 'used/' folders next.")
