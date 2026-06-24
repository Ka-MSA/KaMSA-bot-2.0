import telebot
from config import BOT_TOKEN
from handlers.start_handler import register_start_handler
from handlers.list_handler import register_list_handler
from handlers.menu_handler import register_menu_handler
from handlers.add_handler import register_add_handler

bot = telebot.TeleBot(BOT_TOKEN)

# Register only your necessary structural handlers
register_start_handler(bot)
register_list_handler(bot)
register_menu_handler(bot)
register_add_handler(bot)

if __name__ == "__main__":
    bot.remove_webhook()
    print("🚀 Running streamlined bot via Infinity Polling...")
    bot.infinity_polling(skip_pending=True)