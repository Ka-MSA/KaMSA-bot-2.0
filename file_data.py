import os
import json
import requests
import io
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Force load the .env file variables into memory first!
load_dotenv()

# 2. Extract and load credentials safely
service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT')
if not service_account_json:
    raise ValueError("GOOGLE_SERVICE_ACCOUNT is not set in environment variables.")

creds_dict = json.loads(service_account_json)
creds = service_account.Credentials.from_service_account_info(creds_dict)

# Initialize Drive API
drive_service = build('drive', 'v3', credentials=creds)

# Your main folder ID
MAIN_FOLDER_ID = '1-5ocbVU17S13rUgbaxi5kEWOXjAJWTsf'

def get_items_in_folder(folder_id):
    """Fetches both files and subfolders in a single API call to reduce latency."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(
        q=query,
        orderBy='name',
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get('files', [])

def crawl_folder_recursive(folder_id, current_path=""):
    """
    Recursively travels through all layers of folders, flattening the structure
    into section keys based on their folder path.
    """
    local_files_map = {}
    items = get_items_in_folder(folder_id)
    
    subfolders = [i for i in items if i['mimeType'] == 'application/vnd.google-apps.folder']
    files = [i for i in items if i['mimeType'] != 'application/vnd.google-apps.folder']
    
    if files:
        files_dict = {}
        for file in files:
            file_id = file['id']
            file_name = file['name']
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            files_dict[file_name] = {
                'id': file_id,
                'name': file_name,
                'url': download_url
            }
        section_key = current_path if current_path else "Main Folder Files"
        local_files_map[section_key] = dict(sorted(files_dict.items()))
        
    for folder in subfolders:
        next_path = f"{current_path}/{folder['name']}" if current_path else folder['name']
        child_maps = crawl_folder_recursive(folder['id'], next_path)
        local_files_map.update(child_maps)
        
    return local_files_map

def build_files_by_section():
    """Triggers our recursive engine starting from your main root folder."""
    print("📂 Building static multi-layer directory map from Google Drive...")
    raw_structure = crawl_folder_recursive(MAIN_FOLDER_ID)
    return dict(sorted(raw_structure.items()))


# --- STATIC BOOT ALLOCATION ---
# This executes EXACTLY ONCE when the container boots. 
# Zero background loops, zero CPU overhead during runtime.
_global_directory_cache = build_files_by_section()

def get_live_files_by_section():
    """Returns the pre-compiled static dictionary instantly from RAM."""
    return _global_directory_cache


def download_file(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    return io.BytesIO(response.content)
