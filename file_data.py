import os
import json
import time
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

# In-memory storage cache registries
DRIVE_TREE = {}
_LAST_UPDATE_HOUR = -1

def sync_entire_drive_structure(folder_id):
    """Recursively walks Google Drive and returns a nested node dictionary."""
    node = {"folders": {}, "files": {}}
    
    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(
        q=query,
        orderBy='name',
        fields="files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])

    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            node["folders"][item['id']] = {
                "name": item['name'],
                "content": sync_entire_drive_structure(item['id'])
            }
        else:
            node["files"][item['id']] = {
                "name": item['name']
            }
    return node

def get_live_drive_data():
    """Returns directory structure. Syncs once at the start of every hour."""
    global DRIVE_TREE, _LAST_UPDATE_HOUR
    current_hour = time.localtime().tm_hour
    
    if DRIVE_TREE == {} or current_hour != _LAST_UPDATE_HOUR:
        try:
            DRIVE_TREE = sync_entire_drive_structure(MAIN_FOLDER_ID)
            _LAST_UPDATE_HOUR = current_hour
        except Exception:
            # Silent fallback: keep serving existing memory cache if API drops offline
            if DRIVE_TREE == {}:
                DRIVE_TREE = {"folders": {}, "files": {}}
                
    return DRIVE_TREE

def find_node_by_id(tree_node, target_id):
    """
    Deeply traverses down the tree structure to find the dictionary 
    corresponding to target_id, no matter how nested it is.
    """
    if not tree_node:
        return None
        
    # If the root node matches the target
    if target_id == MAIN_FOLDER_ID:
        return tree_node
        
    # Check if it's an immediate child subfolder
    if "folders" in tree_node and target_id in tree_node["folders"]:
        return tree_node["folders"][target_id]["content"]
        
    # Recursively look deeper down into grandchildren folders
    if "folders" in tree_node:
        for sub in tree_node["folders"].values():
            found = find_node_by_id(sub["content"], target_id)
            if found is not None:
                return found
                
    return None

def find_file_globally(tree_node, file_id):
    """Deeply searches the tree down to the leaves to find a file name by its ID."""
    if not tree_node:
        return None
        
    if "files" in tree_node and file_id in tree_node["files"]:
        return tree_node["files"][file_id]["name"]
        
    if "folders" in tree_node:
        for sub in tree_node["folders"].values():
            found = find_file_globally(sub["content"], file_id)
            if found is not None:
                return found
                
    return None
