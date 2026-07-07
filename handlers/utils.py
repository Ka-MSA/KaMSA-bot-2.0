import io
from file_data import drive_service  # Reuse your authenticated Drive client
from googleapiclient.http import MediaIoBaseDownload

def send_file_as_document(bot, chat_id, filename, file_node):
    """
    Downloads file content directly via Google Drive API media streams into memory
    and uploads it natively to Telegram. Integrates type checking and handles fallback links.
    """
    status_msg = bot.send_message(chat_id, f"⏳ Fetching '{filename}' from Drive...")
    file_id = file_node['id']
    mime_type = file_node.get('mimeType', '')
    
    try:
        # 1. Determine download type based on Google Drive MIME Type
        if mime_type == 'application/vnd.google-apps.presentation':
            # Handle native Google Slides templates by exporting them cleanly to PPTX format
            request = drive_service.files().export_media(
                fileId=file_id, 
                mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'
            )
            if not filename.lower().endswith('.pptx') and not filename.lower().endswith('.ppt'):
                filename = f"{filename}.pptx"
        else:
            # Handle standard raw uploaded binary files (.ppt, .pptx, .pdf, .docx, etc.)
            request = drive_service.files().get_media(fileId=file_id)

        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        bot.edit_message_text("📥 Streaming content from cloud memory...", chat_id, status_msg.message_id)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        bot.edit_message_text("📤 Uploading document to Telegram...", chat_id, status_msg.message_id)
        
        file_buffer.seek(0)
        bot.send_document(
            chat_id=chat_id,
            document=file_buffer,
            visible_file_name=filename  # Dynamically maintains the authentic format type extension
        )
        bot.delete_message(chat_id, status_msg.message_id)
        
    except Exception as e:
        print(f"⚠️ Authenticated download stream failed: {e}")
        # --- THE LIVE RUNTIME FAIL-SAFE ---
        fallback_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=f"❌ Direct stream failed. Download manually here:\n🔗 [{filename}]({fallback_url})",
            parse_mode="Markdown"
        )
