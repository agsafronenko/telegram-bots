import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    Defaults,
)

import config
from bot_core import TriviaBot 

logger = logging.getLogger(__name__)

def main() -> None:
    """Sets up the bot application and runs it."""
    
    # --- Basic Setup ---
    if not config.TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN not configured in config.py or .env. Exiting.")
        return
        
    logger.info("Initializing Trivia Bot...")
    bot_instance = TriviaBot(token=config.TELEGRAM_BOT_TOKEN)
    
    # --- Create Application ---
    application = ApplicationBuilder().token(bot_instance.token).build()

    # --- Conversation Handler for Quiz Setup ---
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start_quiz", bot_instance.start_conversation)],
        states={
            config.DIFFICULTY_SELECTION: [
                CallbackQueryHandler(bot_instance.select_difficulty_callback, pattern=r'^difficulty_')
            ],
            config.CATEGORY_SELECTION: [
                CallbackQueryHandler(bot_instance.select_category_callback, pattern=r'^category_')
            ]
        },
        fallbacks=[
             CommandHandler("cancel", bot_instance.cancel_conversation),
        ],
    )

    # --- Register Handlers ---
    application.add_handler(conv_handler)

    # Callback handler for selecting game length (triggers quiz start)
    application.add_handler(CallbackQueryHandler(bot_instance.start_quiz_callback, pattern=r'^length_'))
    
    # Callback handler for answering questions
    application.add_handler(CallbackQueryHandler(bot_instance.answer_callback, pattern=r'^ans_'))

    # Command handlers
    application.add_handler(CommandHandler(["help", "start"], bot_instance.help_command))
    application.add_handler(CommandHandler("stop_quiz", bot_instance.stop_quiz_command))


    # --- Start the Bot ---
    logger.info("Starting bot polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot polling stopped.")


if __name__ == '__main__':
    main()
