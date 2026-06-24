import re
from file_data import drive_service, MAIN_FOLDER_ID, build_files_by_section
import file_data as fd

def get_or_create_section_folder(section_name):
    """Finds a subfolder ID by name, or creates it if it doesn't exist."""
    query = f"'{MAIN_FOLDER_ID}' in parents and name='{section_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    
    if files:
        return files[0]['id']
        
    # Create the folder if it's missing
    folder_metadata = {
        'name': section_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [MAIN_FOLDER_ID]
    }
    new_folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    return new_folder.get('id')

def register_add_handler(bot):
    @bot.message_handler(commands=['add'])
    def handle_add(message):
        try:
            text = message.text
            # Matches: /add section /filename /drive_link
            match = re.match(r"/add (\\w+) /(.+?) /(\\S+)", text)
            if not match:
                bot.reply_to(message, "Incorrect format. Use:\n`/add section /filename /drive_link`")
                return

            section, filename, link = match.groups()

            # Extract target file ID from the link they want to save
            file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
            if not file_id_match:
                bot.reply_to(message, "Invalid Google Drive link provided.")
                return
            target_file_id = file_id_match.group(1)

            # 1. Get or create the parent section folder on your live Drive
            folder_id = get_or_create_section_folder(section)

            # 2. Create a Shortcut on your Google Drive to link this file to the folder
            shortcut_metadata = {
                'name': filename,
                'mimeType': 'application/vnd.google-apps.shortcut',
                'parents': [folder_id],
                'shortcutDetails': {
                    'targetId': target_file_id
                }
            }
            drive_service.files().create(body=shortcut_metadata).execute()

            # 3. Refresh the bot's memory instantly without restarting!
            fd.files_by_section = build_files_by_section()

            bot.reply_to(message, f"✅ Successfully added '{filename}' to section '{section}' directly on Google Drive!")

        except Exception as e:
            bot.reply_to(message, f"❌ Failed to add file to Drive: {str(e)}")