from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from file_data import get_live_drive_data, find_node_by_id, find_file_globally, MAIN_FOLDER_ID
from .utils import send_file_as_document

def register_menu_handler(bot):
    @bot.message_handler(commands=['menu'])
    def show_menu(message):
        tree = get_live_drive_data()
        bot.send_message(
            message.chat.id, 
            "📂 *Main Directory*:", 
            reply_markup=build_keyboard_for_node(tree, current_id=MAIN_FOLDER_ID, parent_id=MAIN_FOLDER_ID),
            parse_mode="Markdown"
        )

    def build_keyboard_for_node(node, current_id, parent_id):
        keyboard = InlineKeyboardMarkup()

        # 1. Output child subfolders
        for folder_id, folder_info in node["folders"].items():
            keyboard.add(InlineKeyboardButton(text=f"📁 {folder_info['name']}", callback_data=f"view|{folder_id}|{current_id}"))

        # 2. Output files inside this layer
        for file_id, file_info in node["files"].items():
            keyboard.add(InlineKeyboardButton(text=f"📄 {file_info['name']}", callback_data=f"grab|{file_id}"))

        # 3. Dynamic Back Navigation 
        if current_id != MAIN_FOLDER_ID:
            keyboard.add(InlineKeyboardButton(text="⬅️ Back", callback_data=f"back_to|{parent_id}"))
            
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data.startswith("view|"))
    def handle_subfolder_navigation(call):
        _, target_folder_id, current_parent_id = call.data.split("|")
        tree = get_live_drive_data()
        
        target_node = find_node_by_id(tree, target_folder_id)
        if not target_node:
            bot.answer_callback_query(call.id, "Folder not found.")
            return

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📂 *Subfolder Contents*:",
            reply_markup=build_keyboard_for_node(target_node, current_id=target_folder_id, parent_id=current_parent_id),
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_to|"))
    def handle_back_navigation(call):
        _, destination_folder_id = call.data.split("|")
        tree = get_live_drive_data()

        target_node = find_node_by_id(tree, destination_folder_id)
        if not target_node:
            bot.answer_callback_query(call.id, "Directory not found.")
            return

        # Fallback tracking resolution to determine previous layer configuration safely
        prev_parent_id = MAIN_FOLDER_ID
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📂 *Directory Context*:",
            reply_markup=build_keyboard_for_node(target_node, current_id=destination_folder_id, parent_id=prev_parent_id),
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("grab|"))
    def deliver_file(call):
        file_id = call.data.split("|")[1]
        tree = get_live_drive_data()
        
        filename = find_file_globally(tree, file_id)
        if filename:
            send_file_as_document(bot, call.message.chat.id, filename, file_id)
        else:
            bot.answer_callback_query(call.id, "❌ File reference not found.", show_alert=True)
