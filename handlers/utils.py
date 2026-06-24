import io
from file_data import drive_service  # Reuse your authenticated Drive client
from googleapiclient.http import MediaIoBaseDownload

def send_file_as_document(bot, chat_id, filename, file_id_or_url):
    """
    Downloads file content directly via Google Drive API media streams into memory
    and uploads it natively to Telegram. Bypasses the 20MB URL download ceiling.
    """
    status_msg = bot.send_message(chat_id, f"⏳ Fetching '{filename}' from Drive...")
    
    try:
        # Extract file ID if a full URL was passed, otherwise use it directly
        file_id = file_id_or_url
        if "id=" in file_id_or_url:
            file_id = file_id_or_url.split("id=")[1].split("&")[0]
        elif "/d/" in file_id_or_url:
            file_id = file_id_or_url.split("/d/")[1].split("/")[0]

        # Request raw file media via Drive API
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
            visible_file_name=f"{filename}.pdf"
        )
        bot.delete_message(chat_id, status_msg.message_id)
        
    except Exception as e:
        # Fallback if Drive API media download fails
        fallback_url = f"https://drive.google.com/uc?export=download&id={file_id}" if "http" not in file_id_or_url else file_id_or_url
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=f"❌ Direct stream failed. Download manually here:\n{fallback_url}"
        )