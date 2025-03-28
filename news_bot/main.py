import logging
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler
)
from config import Config
from handlers import NewsHandlers

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, Config.LOG_LEVEL)
    )

def main():
    """Initialize and run the Telegram bot"""
    # Setup logging
    setup_logging()
    
    # Create the Application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler('start', NewsHandlers.start))
    application.add_handler(CommandHandler('news', NewsHandlers.get_news))
    application.add_handler(CommandHandler('category', NewsHandlers.choose_category))
    application.add_handler(CommandHandler('country', NewsHandlers.choose_country))
    
    # Register callback query handlers
    application.add_handler(CallbackQueryHandler(NewsHandlers.handle_category_callback, pattern='^(general|business|technology|science|sports|entertainment)$'))
    application.add_handler(CallbackQueryHandler(NewsHandlers.handle_country_callback, pattern='^(us|gb|ca|in|au|jp)$'))
    
    # Start the bot
    print("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()