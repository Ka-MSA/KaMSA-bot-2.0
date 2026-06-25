from file_data import get_live_files_by_section
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .utils import send_file_as_document  # Look in the current folder

def register_menu_handler(bot):
    
    # --- 1. MESSAGE HANDLERS (The Commands) ---
    
    @bot.message_handler(commands=['menu'])
    def show_menu(message):
        bot.send_message(
            message.chat.id, 
            "Choose a section:", 
            reply_markup=build_section_keyboard()
        )

    @bot.message_handler(commands=['list'])
    def list_files(message):
        keyboard = InlineKeyboardMarkup()
        live_data = get_live_files_by_section()

        # Flat structural loop over your nested categories
        for section, files in live_data.items():
            for name in files:
                keyboard.add(InlineKeyboardButton(text=name, callback_data=f"get|{name}"))

        bot.send_message(message.chat.id, "Available files (click to get):", reply_markup=keyboard)


    # --- 2. KEYBOARD BUILDERS (UI Layouts) ---
    
    def build_section_keyboard():
        keyboard = InlineKeyboardMarkup()
        live_data = get_live_files_by_section()
        
        for section in live_data:
            keyboard.add(InlineKeyboardButton(text=section, callback_data=f"section|{section}"))
        return keyboard

    def build_files_keyboard(section_name):
        keyboard = InlineKeyboardMarkup()
        live_data = get_live_files_by_section()
        
        # Guard clause in case a background cache refresh updates folders live
        if section_name in live_data:
            for filename in live_data[section_name]:
                keyboard.add(InlineKeyboardButton(text=filename, callback_data=f"get|{filename}"))
                
        keyboard.add(InlineKeyboardButton(text="⬅ Back to Sections", callback_data="back"))
        return keyboard


    # --- 3. CALLBACK QUERY HANDLERS (Button Clicks) ---
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("section|"))
    def handle_section(call):
        section_name = call.data.split("|", 1)[1]
        live_data = get_live_files_by_section()
        
        if section_name not in live_data:
            bot.answer_callback_query(call.id, "Section not found.")
            return
            
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Files in *{section_name}*:",
            reply_markup=build_files_keyboard(section_name),
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data == "back")
    def handle_back(call):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Choose a section:",
            reply_markup=build_section_keyboard()
        )

    # Catches file requests originating from BOTH the structured /menu and flat /list views!
    @bot.callback_query_handler(func=lambda call: call.data.startswith("get|"))
    def send_file(call):
        filename = call.data.split("|", 1)[1]
        live_data = get_live_files_by_section()
        
        for section in live_data.values():
            if filename in section:
                file_info = section[filename]
                file_target = file_info['id'] if isinstance(file_info, dict) else file_info

                # Forward file stream to user via utils context
                send_file_as_document(bot, call.message.chat.id, filename, file_target)
                return
                
        bot.send_message(call.message.chat.id, "File not found.")
