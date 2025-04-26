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
import matplotlib.pyplot as plt

# Ensure pytesseract is configured correctly
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)

# ---------- Configuration ----------
SERVICE_ACCOUNT_FILE = 'acoustic-atom-456322-b4-ff317ed933d2.json'
SCOPES               = ['https://www.googleapis.com/auth/drive']
FOLDER_ID            = '1cTzfg8extLH7V3hiXgFXgmVvUkCz4jkc'
DOWNLOAD_DIR         = 'downloaded_images'
PROCESSED_DIR        = 'processed_images'
DB_PATH              = 'thermal_img.db'

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
    files = {}
    page_token = None
    query = f"'{folder_id}' in parents and trashed = false"
    while True:
        resp = service.files().list(
            q=query, spaces='drive',
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token
        ).execute()
        for f in resp.get('files', []):
            files[f['name']] = f['id']
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return files

def download_file(service, file_id, destination_path):
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
    remote_files  = list_files_in_folder(drive_service, FOLDER_ID)

    # Connect to SQLite
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure url_original & url_clean columns exist
    cursor.execute("PRAGMA table_info(environment_logs)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'url_original' not in cols:
        cursor.execute("ALTER TABLE environment_logs ADD COLUMN url_original TEXT")
    if 'url_clean' not in cols:
        cursor.execute("ALTER TABLE environment_logs ADD COLUMN url_clean TEXT")
    conn.commit()

    for name, file_id in remote_files.items():
        # skip cleaned or non-images
        if 'clean' in name.lower() or not name.lower().endswith(('.jpg','.jpeg','.png')):
            continue

        base       = os.path.splitext(name)[0]
        dl_path    = os.path.join(DOWNLOAD_DIR, name)
        clean_name = f"{base}_clean.jpg"
        cl_path    = os.path.join(PROCESSED_DIR, clean_name)

        # Download original if needed
        if not os.path.exists(dl_path):
            download_file(drive_service, file_id, dl_path)

        # skip if cleaned already exists remotely
        if clean_name in remote_files:
            continue

        # OCR step
        ocr = run_ocr_on_coords(dl_path, OCR_REGIONS)
        print(f"OCR for {name}: {ocr}")

        # manual override if confidence < 80
        if ocr['min_conf'] < 80 or ocr['max_conf'] < 80:
            img = Image.open(dl_path)
            plt.ion()
            plt.figure(figsize=(8,6))
            plt.imshow(img)
            plt.axis('off')
            plt.show()

            print(f"\n⚠️ Low OCR confidence for {name}.")
            if ocr['min_conf'] < 80 and ocr['max_conf'] < 80:
                ocr['min'] = input("Enter MIN temperature: ")
                ocr['max'] = input("Enter MAX temperature: ")
            elif ocr['min_conf'] < 80:
                ocr['min'] = input("Enter MIN temperature: ")
            else:
                ocr['max'] = input("Enter MAX temperature: ")

            plt.close()

        # smoothing step
        changed = smooth_pixels(
            dl_path, cl_path,
            tolerance=WHITE_TOLERANCE,
            neighbor_count=NEIGHBOR_COUNT,
            white_boxes=WHITE_BOXES,
            green_box=GREEN_BOX,
            smooth_bar=SMOOTH_TEMPERATURE_BAR,
            bar_box=TEMPERATURE_BAR_BOX
        )
        print(f"Pixels changed: {changed}")

        # upload cleaned image
        media = MediaFileUpload(cl_path, mimetype='image/jpeg')
        meta  = {'name': clean_name, 'parents': [FOLDER_ID]}
        up    = drive_service.files().create(
            body=meta, media_body=media, fields='id'
        ).execute()

        url_original = f"https://drive.google.com/uc?id={file_id}"
        url_clean    = f"https://drive.google.com/uc?id={up['id']}"

        # ----- manual metadata prompts -----
        location_id      = input("Enter location_id (e.g. ch_1_2): ").strip()
        outside_temp     = float(input("Enter outside temperature (°F): "))
        time_taken_hours = int(input("Enter hour of day (0–23): "))
        windows_opened   = input("Window opened? (Y/N): ").strip().upper()
        while windows_opened not in ('Y','N'):
            windows_opened = input("Please enter Y or N: ").strip().upper()

        # check for duplicates
        cursor.execute(
            "SELECT 1 FROM environment_logs WHERE url_original=? AND url_clean=?",
            (url_original, url_clean)
        )
        if cursor.fetchone():
            print("Already logged; skipping.")
            continue

        # final insert: 8 placeholders for 8 values
        cursor.execute(
            """
            INSERT INTO environment_logs
              (location_id,
               outside_temp,
               min_temp,
               max_temp,
               time_taken_hours,
               windows_opened,
               date,
               url_original,
               url_clean)
            VALUES (?, ?, ?, ?, ?, ?, date('now'), ?, ?)
            """,
            (
                location_id,
                outside_temp,
                float(ocr['min']),
                float(ocr['max']),
                time_taken_hours,
                windows_opened,
                url_original,
                url_clean
            )
        )
        conn.commit()
        print(f"Logged {name} → {clean_name}")

    conn.close()
    print("Processing complete.")
