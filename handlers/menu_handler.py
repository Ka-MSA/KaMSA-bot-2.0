from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from file_data import get_live_drive_data, find_node_by_id, find_file_globally, MAIN_FOLDER_ID
from utils import send_file_as_document

def find_parent_id_globally(tree_node, target_id, current_parent_id=MAIN_FOLDER_ID):
    """Dynamically calculates the true parent folder ID of any given node ID inside the tree."""
    if not tree_node:
        return MAIN_FOLDER_ID
    if "folders" in tree_node and target_id in tree_node["folders"]:
        return current_parent_id
    if "folders" in tree_node:
        for folder_id, sub in tree_node["folders"].items():
            found = find_parent_id_globally(sub["content"], target_id, folder_id)
            if found:
                return found
    return MAIN_FOLDER_ID

def register_menu_handler(bot):
    @bot.message_handler(commands=['menu'])
    def show_menu(message):
        try:
            tree = get_live_drive_data()
            markup = build_keyboard_for_node(tree, current_id=MAIN_FOLDER_ID, parent_id=MAIN_FOLDER_ID)
            
            bot.send_message(
                message.chat.id, 
                "📂 *Main Directory*:", 
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception:
            bot.send_message(message.chat.id, "❌ Error loading menu structure. Please try again.")

    def build_keyboard_for_node(node, current_id, parent_id):
        keyboard = InlineKeyboardMarkup()

        # 1. Loop through child subfolders safely
        if "folders" in node:
            for folder_id, folder_info in node["folders"].items():
                keyboard.add(InlineKeyboardButton(text=f"📁 {folder_info['name']}", callback_data=f"view|{folder_id}"))

        # 2. Loop through actual files safely 
        if "files" in node:
            for file_id, file_info in node["files"].items():
                keyboard.add(InlineKeyboardButton(text=f"📄 {file_info['name']}", callback_data=f"grab|{file_id}"))

        # 3. Handle Back button constraints dynamically
        if current_id != MAIN_FOLDER_ID:
            keyboard.add(InlineKeyboardButton(text="⬅️ Back", callback_data=f"back_to|{parent_id}"))
            
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data.startswith("view|"))
    def handle_subfolder_navigation(call):
        try:
            target_folder_id = call.data.split("|")[1]
            tree = get_live_drive_data()
            
            target_node = find_node_by_id(tree, target_folder_id)
            if not target_node:
                bot.answer_callback_query(call.id, "Folder context empty or missing.")
                return

            # Compute parent context dynamically directly from our local data structure
            calculated_parent = find_parent_id_globally(tree, target_folder_id)

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="📂 *Subfolder Contents*:",
                reply_markup=build_keyboard_for_node(target_node, current_id=target_folder_id, parent_id=calculated_parent),
                parse_mode="Markdown"
            )
        except Exception:
            bot.answer_callback_query(call.id, "Error opening subfolder.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_to|"))
    def handle_back_navigation(call):
        try:
            destination_folder_id = call.data.split("|")[1]
            tree = get_live_drive_data()

            target_node = find_node_by_id(tree, destination_folder_id)
            if not target_node:
                bot.answer_callback_query(call.id, "Directory layer missing.")
                return

            # Resolve the parent of the folder we are navigating back to
            calculated_parent = find_parent_id_globally(tree, destination_folder_id)

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="📂 *Directory Context*:",
                reply_markup=build_keyboard_for_node(target_node, current_id=destination_folder_id, parent_id=calculated_parent),
                parse_mode="Markdown"
            )
        except Exception:
            bot.answer_callback_query(call.id, "Error navigating backward.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("grab|"))
    def deliver_file(call):
        try:
            file_id = call.data.split("|")[1]
            tree = get_live_drive_data()
            
            filename = find_file_globally(tree, file_id)
            if filename:
                send_file_as_document(bot, call.message.chat.id, filename, file_id)
            else:
                bot.answer_callback_query(call.id, "❌ File reference missing or moved.", show_alert=True)
        except Exception:
            bot.answer_callback_query(call.id, "Error downloading file.")
