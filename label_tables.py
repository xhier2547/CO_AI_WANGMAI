import os
import cv2
from pathlib import Path
import shutil

RAW_DIR = Path("dataset_tables/raw")
FREE_DIR = Path("dataset_tables/free")
USED_DIR = Path("dataset_tables/used")

FREE_DIR.mkdir(parents=True, exist_ok=True)
USED_DIR.mkdir(parents=True, exist_ok=True)

images = sorted(list(RAW_DIR.glob("*.jpg")))

print(f"🖼 พบภาพทั้งหมด {len(images)} รูป")
print("กด 'f' = FREE, 'u' = USED, 'q' = quit")

for i, img_path in enumerate(images, 1):
    img = cv2.imread(str(img_path))
    cv2.imshow("Label Table (f=free, u=used, q=quit)", img)

    key = cv2.waitKey(0)

    if key == ord('f'):
        shutil.move(str(img_path), FREE_DIR / img_path.name)
        print(f"[{i}] ✅ FREE -> {img_path.name}")
    elif key == ord('u'):
        shutil.move(str(img_path), USED_DIR / img_path.name)
        print(f"[{i}] ✅ USED -> {img_path.name}")
    elif key == ord('q'):
        print("🛑 หยุดการ Label แล้ว")
        break

cv2.destroyAllWindows()
print("🎯 Labeling เสร็จสิ้น!")
