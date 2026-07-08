from file_data import (
    get_folder_node, 
    get_root_folder_id, 
    get_short_id, 
    get_real_id_from_short,
    get_file_token,
    find_file_node_by_token
)
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .utils import send_file_as_document

def register_menu_handler(bot):
    
    @bot.message_handler(commands=['menu'])
    def show_menu(message):
        root_id = get_root_folder_id()
        bot.send_message(
            message.chat.id, 
            "📂 *Main Menu*:", 
            reply_markup=build_explorer_keyboard(root_id),
            parse_mode="Markdown"
        )

    def build_explorer_keyboard(folder_id):
        keyboard = InlineKeyboardMarkup()
        node = get_folder_node(folder_id)
        
        if not node:
            return keyboard

        # Layer 1: Subfolders
        for sub_id, sub_name in sorted(node['subfolders'].items(), key=lambda x: x[1]):
            short_sub_id = get_short_id(sub_id)
            keyboard.add(InlineKeyboardButton(text=f"📁 {sub_name}", callback_data=f"browse|{short_sub_id}"))
            
        # Layer 2: Files (Now completely tokenized and compressed! 📄)
        for file_name in sorted(node['files'].keys()):
            file_token = get_file_token(file_name)
            if file_token:
                keyboard.add(InlineKeyboardButton(text=f"📄 {file_name}", callback_data=f"get|{file_token}"))
            
        # Layer 3: Back Button
        if folder_id != get_root_folder_id():
            parent_id = node.get('parent_id') or get_root_folder_id()
            short_parent_id = get_short_id(parent_id)
            keyboard.add(InlineKeyboardButton(text="⬅️ Back", callback_data=f"browse|{short_parent_id}"))
            
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data.startswith("browse|"))
    def handle_browsing(call):
        short_key = call.data.split("|", 1)[1]
        target_folder_id = get_real_id_from_short(short_key)
        node = get_folder_node(target_folder_id)
        
        if not node:
            bot.answer_callback_query(call.id, "Directory layer missing.")
            return
            
        display_text = f"📂 Current Folder: *{node['name']}*\n\n"
        if node.get('folder_note'):
            display_text += f"{node['folder_note']}\n\n"
            
        display_text += "Choose an option below:"
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=display_text,
                reply_markup=build_explorer_keyboard(target_folder_id),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"⚠️ Telegram layout edit error: {e}")
            bot.answer_callback_query(call.id, "Could not update window.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("get|"))
    def send_file(call):
        file_token = call.data.split("|", 1)[1]
        # Look up using the unique token ID instead of relying on the raw name string
        file_node = find_file_node_by_token(file_token)
        
        if file_node:
            filename = file_node['name']
            bot.answer_callback_query(call.id, "⏳ Fetching original file...")
            send_file_as_document(bot, call.message.chat.id, filename, file_node)
        else:
            bot.send_message(call.message.chat.id, "❌ File could not be retrieved from map.")
