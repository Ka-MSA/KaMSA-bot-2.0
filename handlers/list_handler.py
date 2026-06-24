from file_data import files_by_section
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def register_list_handler(bot):
    @bot.message_handler(commands=['list'])
    def list_files(message):
        keyboard = InlineKeyboardMarkup()

        for section, files in files_by_section.items():
            for name in files:
                # Clicks here generate "get|filename", caught cleanly by menu_handler!
                keyboard.add(InlineKeyboardButton(text=name, callback_data=f"get|{name}"))

        bot.send_message(message.chat.id, "Available files (click to get):", reply_markup=keyboard)