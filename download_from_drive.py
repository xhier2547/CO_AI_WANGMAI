from __future__ import print_function
import os, io, sys, pickle
from pathlib import Path
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from PIL import Image

import os, tempfile
# 👇 เพิ่ม 3 บรรทัดนี้
os.environ["TMPDIR"] = "/app"
tempfile.gettempdir = lambda: "/app"
print("[INIT] Temp directory fixed to /app for Docker compatibility.")

# ---------------- CONFIG ---------------- #
BASE_DIR = Path(os.getcwd())
IMAGE_DIR = BASE_DIR / "images"
PROCESSED_DIR = BASE_DIR / "processed"
CREDENTIALS_FILE = Path("/app/credentials.json")
TOKEN_FILE = Path("/app/token.pkl")


# Google Drive Folder ID
FOLDER_ID = "1VY1Y9xOQnSrO81ZaDo1RMtf2yfhds6BK"

IMAGE_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# แก้ encoding ป้องกัน emoji error บน Windows หรือ stdout ปกติ
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass




SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# ---------------- AUTH ---------------- #
def authenticate():
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return creds

# ---------------- FIX ORIENTATION ---------------- #
def ensure_horizontal(image_path: Path):
    """หมุนรูปให้เป็นแนวนอนเสมอ"""
    try:
        img = Image.open(image_path)
        w, h = img.size
        if h > w:  # ถ้าแนวตั้ง → หมุน 90 องศา
            img = img.rotate(-90, expand=True)
        # กันรูปกลับหัว (rotate 180) กรณี orientation ผิด
        if img.size[0] < img.size[1]:
            img = img.rotate(180, expand=True)

        img.save(image_path)
        print(f"↩Rotated {image_path.name} to horizontal")
    except Exception as e:
        print(f"⚠️ Could not rotate {image_path.name}: {e}")

# ---------------- DOWNLOAD ---------------- #
def download_files():
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)

    all_files = []
    page_token = None

    while True:
        response = service.files().list(
            q=f"'{FOLDER_ID}' in parents and mimeType contains 'image/'",
            orderBy="createdTime desc",
            fields="nextPageToken, files(id, name, createdTime)",
            pageSize=1000,
            pageToken=page_token
        ).execute()

        all_files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    if not all_files:
        print("⚠️ No files found in Google Drive folder.")
        return

    print(f"📂 Found {len(all_files)} images in Google Drive folder")

    for file in all_files:
        file_id = file["id"]
        file_name = file["name"]

        # ถ้ามีใน images/ หรือ processed/ → ข้าม
        if (IMAGE_DIR / file_name).exists() or (PROCESSED_DIR / file_name).exists():
            print(f"⏭️ Skip existing file: {file_name}")
            continue

        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(IMAGE_DIR / file_name, "wb")
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"⬇️ Download {file_name}: {int(status.progress() * 100)}%")
        print(f"✅ Saved: {file_name}")

        # หมุนภาพให้เป็นแนวนอน
        ensure_horizontal(IMAGE_DIR / file_name)

    print("🎉 All new files downloaded.")

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    print(f"===== DOWNLOAD START {datetime.now()} =====")
    download_files()
    print(f"===== DOWNLOAD END {datetime.now()} =====")
