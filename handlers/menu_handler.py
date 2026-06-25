from file_data import get_folder_node, get_root_folder_id, find_file_by_name_global
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .utils import send_file_as_document

def register_menu_handler(bot):
    
    # --- 1. COMMAND TRIGGER ---
    @bot.message_handler(commands=['menu'])
    def show_menu(message):
        root_id = get_root_folder_id()
        bot.send_message(
            message.chat.id, 
            "📂 *Main Menu*:", 
            reply_markup=build_explorer_keyboard(root_id),
            parse_mode="Markdown"
        )

    # --- 2. THE WINDOW BUILDER ENGINE ---
    def build_explorer_keyboard(folder_id):
        keyboard = InlineKeyboardMarkup()
        node = get_folder_node(folder_id)
        
        if not node:
            return keyboard

        # Layer 1: Render subfolders at this current level (Prefix emoji 📁)
        for sub_id, sub_name in sorted(node['subfolders'].items(), key=lambda x: x[1]):
            keyboard.add(InlineKeyboardButton(text=f"📁 {sub_name}", callback_data=f"browse|{sub_id}"))
            
        # Layer 2: Render files side-by-side at this same level (Prefix emoji 📄)
        for file_name in sorted(node['files'].keys()):
            keyboard.add(InlineKeyboardButton(text=f"📄 {file_name}", callback_data=f"get|{file_name}"))
            
        # Layer 3: Contextual Back Button
        if folder_id != get_root_folder_id():
            parent_id = node.get('parent_id') or get_root_folder_id()
            keyboard.add(InlineKeyboardButton(text="⬅️ Back", callback_data=f"browse|{parent_id}"))
            
        return keyboard

    # --- 3. DYNAMIC EXPLORER INTERACTION LISTENER ---
   @bot.callback_query_handler(func=lambda call: call.data.startswith("browse|"))
    def handle_browsing(call):
        target_folder_id = call.data.split("|", 1)[1]
        node = get_folder_node(target_folder_id)
        
        if not node:
            bot.answer_callback_query(call.id, "Directory layer missing.")
            return
            
        # Base header format
        display_text = f"📂 Current Folder: *{node['name']}*\n\n"
        
        # DYNAMIC INJECTION: If a team member uploaded a .txt note into this folder, 
        # its content will display here natively to the user!
        if node.get('folder_note'):
            display_text += f"{node['folder_note']}\n\n"
            
        display_text += "Choose an option below:"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=display_text,
            reply_markup=build_explorer_keyboard(target_folder_id),
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("get|"))
    def send_file(call):
        filename = call.data.split("|", 1)[1]
        file_target_id = find_file_by_name_global(filename)
        
        if file_target_id:
            bot.answer_callback_query(call.id, "⏳ Fetching file stream...")
            send_file_as_document(bot, call.message.chat.id, filename, file_target_id)
        else:
            bot.send_message(call.message.chat.id, "❌ File could not be retrieved from map.")
