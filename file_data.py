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
    node = {
        'name': folder_name,
        'id': folder_id,
        'subfolders': {},  # folder_id -> folder_name
        'files': {},       # filename -> {id, name, mimeType}
        'folder_note': None
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

# --- Unified Token Storage Map ---
_short_id_map = {}   # short_token -> real_id or filename
_file_lookup_map = {} # short_token -> file_node_dict

token_index = 0

# Generate safe tokens for all items inside RAM
for folder_real_id, node in _drive_tree_registry.items():
    # Tokenize folders
    folder_token = f"d{token_index}"
    _short_id_map[folder_token] = folder_real_id
    token_index += 1
    
    # Tokenize individual files securely
    for filename, file_node in node['files'].items():
        file_token = f"x{token_index}"
        _short_id_map[file_token] = filename
        _file_lookup_map[file_token] = file_node
        token_index += 1

def get_short_id(real_id):
    """Finds token for a folder ID."""
    for token, rid in _short_id_map.items():
        if rid == real_id and token.startswith('d'):
            return token
    return real_id

def get_file_token(filename):
    """Finds token for a filename."""
    for token, fname in _short_id_map.items():
        if fname == filename and token.startswith('x'):
            return token
    return None

def get_real_id_from_short(short_key):
    return _short_id_map.get(short_key, short_key)

def get_folder_node(folder_id):
    real_id = get_real_id_from_short(folder_id)
    return _drive_tree_registry.get(real_id)

def get_root_folder_id():
    return MAIN_FOLDER_ID

def find_file_node_by_token(token):
    """Instantly delivers file metadata dictionary matching its unique token key."""
    return _file_lookup_map.get(token)
