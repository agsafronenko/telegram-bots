from dotenv import load_dotenv
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext

load_dotenv()

# Define a function that handles new user joins
async def welcome(update: Update, context: CallbackContext) -> None:
    # Get the list of new users
    new_users = update.message.new_chat_members
    
    # Loop through new users and send a welcome message
    for user in new_users:
        # Send "hi" to the chat
        await update.message.reply_text(f"Hi, {user.first_name}! Welcome to the chat!")

def main():
    # Use your own bot token obtained from BotFather
    print("new_bot.py is running")
    token = os.getenv("NEWS_BOT_TOKEN")
    
    # Create an Application object
    application = Application.builder().token(token).build()

    # Set up a message handler that listens for new members joining the chat
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
