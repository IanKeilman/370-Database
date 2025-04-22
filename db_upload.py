import os
import io
import sqlite3
from PIL import Image
import pytesseract
import cleaning_funcs as utils
from cleaning_funcs import (
    run_ocr_on_coords, smooth_pixels,
    OCR_REGIONS, WHITE_TOLERANCE, NEIGHBOR_COUNT,
    WHITE_BOXES, GREEN_BOX,
    SMOOTH_TEMPERATURE_BAR, TEMPERATURE_BAR_BOX
)
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Ensure pytesseract is configured correctly
pytesseract.pytesseract.tesseract_cmd = \
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# ---------- Configuration ----------
SERVICE_ACCOUNT_FILE = \
    'C:/Users/ianmk/CODING/random/acoustic-atom-456322-b4-2bd2a736169d.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = '1cTzfg8extLH7V3hiXgFXgmVvUkCz4jkc'
DOWNLOAD_DIR = 'downloaded_images'
PROCESSED_DIR = 'processed_images'
DB_PATH = 'thermal_img.db'

# Ensure local directories exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ---------- Google Drive Authentication ----------
def authenticate_drive():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

# ---------- Drive Utilities ----------
def list_files_in_folder(service, folder_id):
    """
    Returns dict mapping filenames to file IDs for all non-trashed files in the folder.
    """
    files = {}
    page_token = None
    query = f"'{folder_id}' in parents and trashed = false"
    while True:
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token
        ).execute()
        for f in response.get('files', []):
            files[f['name']] = f['id']
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    return files


def download_file(service, file_id, destination_path):
    """Download a file from Drive to a local path."""
    request = service.files().get_media(fileId=file_id)
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    with io.FileIO(destination_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {os.path.basename(destination_path)}: {int(status.progress() * 100)}%")

# ---------- Main Processing ----------
if __name__ == '__main__':
    drive_service = authenticate_drive()
    remote_files = list_files_in_folder(drive_service, FOLDER_ID)

    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for name, file_id in remote_files.items():
        # Skip files already processed (cleaned) or non-image
        if 'clean' in name.lower():
            print(f"Skipping cleaned file: {name}")
            continue
        if not name.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        base, ext = os.path.splitext(name)
        download_path = os.path.join(DOWNLOAD_DIR, name)
        cleaned_name = f"{base}_clean{ext}"
        cleaned_path = os.path.join(PROCESSED_DIR, cleaned_name)

        # 1) Download if not already present
        if os.path.exists(download_path):
            print(f"Already downloaded: {name}")
        else:
            print(f"Downloading: {name}")
            download_file(drive_service, file_id, download_path)

        # 2) Skip upload if cleaned file exists in Drive
        if cleaned_name in remote_files:
            print(f"Cleaned image exists remotely: {cleaned_name}")
            continue

        # 3) OCR
        ocr = run_ocr_on_coords(download_path)
        print(f"OCR for {name}: {ocr}")

        # 4) Manual input if low confidence
        if ocr['min_conf'] < 80 or ocr['max_conf'] < 80:
            print(f"Low OCR confidence for {name}. Please input manually.")
            Image.open(download_path).show()
            ocr['min'] = input('Enter MIN temperature: ')
            ocr['max'] = input('Enter MAX temperature: ')

        # 5) Image smoothing
        changed = smooth_pixels(
            download_path, cleaned_path,
            tolerance=WHITE_TOLERANCE,
            neighbor_count=NEIGHBOR_COUNT,
            white_boxes=WHITE_BOXES,
            green_box=GREEN_BOX,
            smooth_bar=SMOOTH_TEMPERATURE_BAR,
            bar_box=TEMPERATURE_BAR_BOX,
        )
        print(f"Pixels changed: {changed}")

        # 6) Upload cleaned image
        print(f"Uploading cleaned image: {cleaned_name}")
        file_metadata = {'name': cleaned_name, 'parents': [FOLDER_ID]}
        media = MediaFileUpload(cleaned_path, mimetype='image/jpeg')
        uploaded = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        uploaded_url = f"https://drive.google.com/uc?id={uploaded['id']}"

        # 7) Log to database if not already present
        cursor.execute(
            "SELECT COUNT(*) FROM environment_logs WHERE url = ?", (uploaded_url,)
        )
        if cursor.fetchone()[0] > 0:
            print(f"Record for {cleaned_name} already exists in database. Skipping logging.")
        else:
            cursor.execute(
                """
                INSERT INTO environment_logs (
                    location_id, min_temp, max_temp, date, url
                )
                VALUES (?, ?, ?, date('now'), ?)
                """,
                (
                    'UNKNOWN',  # Replace with actual location_id if known
                    ocr['min'],
                    ocr['max'],
                    uploaded_url
                )
            )
            conn.commit()
            print(f"Logged {cleaned_name} to database.")

    conn.close()
    print("Processing complete.")