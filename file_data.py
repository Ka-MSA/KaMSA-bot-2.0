import os
import json
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

def get_subfolders(folder_id):
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(
        q=query,
        orderBy='name',
        fields="files(id, name)"
    ).execute()
    return results.get('files', [])

def get_files_in_folder(folder_id):
    query = f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(
        q=query,
        orderBy='name',
        fields="files(id, name)"
    ).execute()
    return results.get('files', [])

def build_files_by_section():
    files_by_section = {}
    subfolders = get_subfolders(MAIN_FOLDER_ID)

    for folder in subfolders:
        section_name = folder['name']
        files = get_files_in_folder(folder['id'])
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

        files_by_section[section_name] = dict(sorted(files_dict.items()))

    return dict(sorted(files_by_section.items()))

# Exported dictionary
files_by_section = build_files_by_section()

def download_file(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    return io.BytesIO(response.content)
