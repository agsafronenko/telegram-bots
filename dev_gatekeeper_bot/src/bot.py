import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.handlers.commands import start, help_command
from src.handlers.verification import (
    on_new_chat_member, 
    check_answer
)
from src.handlers.message_tracking import track_messages

def create_bot_application():
    """Create and configure the Telegram bot application."""
    # Enable logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
        level=logging.INFO
    )

    # Retrieve bot token from environment
    telegram_token = os.getenv("DEV_GATEKEEPER_BOT")
    
    # Create the Application
    application = Application.builder().token(telegram_token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Handle new chat members
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_chat_member))
    
    # Handle answers from users being verified
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))
    
    # Track all user messages
    application.add_handler(MessageHandler(filters.ALL, track_messages), group=1)

    return application
