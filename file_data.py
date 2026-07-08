import os
import json
import requests
import io
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT')
if not service_account_json:
    raise ValueError("GOOGLE_SERVICE_ACCOUNT is not set in environment variables.")

creds_dict = json.loads(service_account_json)
creds = service_account.Credentials.from_service_account_info(creds_dict)

# Global authenticated Drive API client instance
drive_service = build('drive', 'v3', credentials=creds)

MAIN_FOLDER_ID = '1-5ocbVU17S13rUgbaxi5kEWOXjAJWTsf'

def get_items_in_folder(folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(
        q=query,
        orderBy='name',
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get('files', [])

def build_tree_recursive(folder_id, folder_name):
    """
    Builds a structured tree profile where each folder node explicitly knows 
    its files, its child folders, its parent connection, and any embedded descriptive text notes.
    """
    node = {
        'name': folder_name,
        'id': folder_id,
        'subfolders': {},  # folder_id -> folder_name
        'files': {},       # filename -> {id, name, mimeType}
        'folder_note': None # Raw text string read from any .txt files inside
    }
    
    items = get_items_in_folder(folder_id)
    
    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            node['subfolders'][item['id']] = item['name']
        elif item['name'].lower().endswith('.txt'):
            try:
                url = f"https://drive.google.com/uc?export=download&id={item['id']}"
                response = requests.get(url)
                if response.status_code == 200:
                    node['folder_note'] = response.text.strip()
            except Exception as e:
                print(f"⚠️ Failed to read text file note {item['name']}: {e}")
        else:
            node['files'][item['name']] = {
                'id': item['id'],
                'name': item['name'],
                'mimeType': item.get('mimeType', '')
            }
            
    return node

def build_entire_drive_map():
    """Crawls all layers and stores them indexed flat by folder_id for O(1) lookups."""
    flat_registry = {}
    
    def cache_worker(folder_id, folder_name, parent_id=None):
        node = build_tree_recursive(folder_id, folder_name)
        node['parent_id'] = parent_id
        flat_registry[folder_id] = node
        
        for subfolder_id, subfolder_name in node['subfolders'].items():
            cache_worker(subfolder_id, subfolder_name, parent_id=folder_id)
            
    print("📂 Building deep hierarchical file explorer tree from Google Drive...")
    cache_worker(MAIN_FOLDER_ID, "Main Menu")
    return flat_registry

# --- Static Memory Storage Boot ---
_drive_tree_registry = build_entire_drive_map()

# --- Dynamic Short Key Button Compression Map ---
_short_id_map = {}
for index, real_id in enumerate(_drive_tree_registry.keys()):
    short_key = f"f{index}"
    _short_id_map[short_key] = real_id

def get_short_id(real_id):
    """Finds the short compressed key for a real Google Drive ID."""
    for short_key, rid in _short_id_map.items():
        if rid == real_id:
            return short_key
    return real_id

def get_real_id_from_short(short_key):
    """Translates a short key back to the true massive Google Drive ID."""
    return _short_id_map.get(short_key, short_key)

def get_folder_node(folder_id):
    """Instantly fetches a specific directory layer from RAM."""
    real_id = get_real_id_from_short(folder_id)
    return _drive_tree_registry.get(real_id)

def get_root_folder_id():
    return MAIN_FOLDER_ID

def find_file_node_global(filename):
    """Scans cache to find a full file dictionary node matching the requested name string."""
    for node in _drive_tree_registry.values():
        if filename in node['files']:
            return node['files'][filename]
    return None
