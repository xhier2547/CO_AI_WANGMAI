from __future__ import print_function
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# ---------------- CONFIG ---------------- #
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = "1VY1Y9xOQnSrO81ZaDo1RMtf2yfhds6BK"
OUTPUT_FOLDER = "images/"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def authenticate():
    """ยืนยันตัวตนด้วย OAuth"""
    creds = None
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def download_latest_file():
    """โหลดไฟล์ล่าสุดจากโฟลเดอร์"""
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    # ค้นหาไฟล์ในโฟลเดอร์
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType contains 'image/'",
        orderBy="createdTime desc",
        pageSize=1,
        fields="files(id, name, createdTime)"
    ).execute()

    items = results.get('files', [])
    if not items:
        print("⚠️ ไม่พบไฟล์ในโฟลเดอร์")
        return None

    latest_file = items[0]
    file_id = latest_file['id']
    file_name = latest_file['name']
    request = service.files().get_media(fileId=file_id)

    output_path = os.path.join(OUTPUT_FOLDER, file_name)
    with io.FileIO(output_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"⬇️ Download {file_name}: {int(status.progress() * 100)}%")

    print(f"✅ Saved: {output_path}")
    return output_path

if __name__ == '__main__':
    download_latest_file()
