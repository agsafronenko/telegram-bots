import os
import logging
from datetime import date

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext
)

from config import (
    REPUTATION_WORDS, 
    DAILY_TOP_10_TIME,
    REPUTATION_GAIN,
    MAX_DAILY_REPUTATION_GAIN
)
from database import ReputationDatabase
from utils import adjust_time, generate_leaderboard_message

# Load environment variables at the start of the main script
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ReputationBot:
    def __init__(self):
        # Get bot token from environment variable
        self.bot_token = os.getenv("BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("No BOT_TOKEN found in environment variables")
        
        self.db = ReputationDatabase()
        self.user_daily_reputation = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command and add chat to active chats"""
        self.db.add_active_chat(update.effective_chat.id)
        
        await update.message.reply_text(
            "Welcome to the Reputation Bot! "
            "Say thanks to people, and earn reputation. "
            "Use /ranks to see top users and /myrank to check your rank."
        )

    async def handle_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle message replies with reputation words"""
        message = update.message
        original_message = message.reply_to_message
        reply_user = message.from_user
        
        # Validate original message and user
        if not original_message or not original_message.from_user:
            return
        
        original_user = original_message.from_user

        # Prevent self-reputation
        if reply_user.id == original_user.id:
            return

        # Check message text for reputation words
        if message.text:
            reply_text = message.text.lower()
            if any(word in reply_text for word in REPUTATION_WORDS):
                today = date.today()
                user_key = (original_user.id, today)
                current_reputation_today = self.user_daily_reputation.get(user_key, 0)

                if current_reputation_today < MAX_DAILY_REPUTATION_GAIN:
                    # Update reputation in database
                    self.db.update_reputation(
                        original_user.id, 
                        original_user.first_name, 
                        original_user.username, 
                        REPUTATION_GAIN
                    )

                    # Track daily reputation
                    self.user_daily_reputation[user_key] = current_reputation_today + REPUTATION_GAIN

                    # Send confirmation message
                    await message.reply_text(
                        f"👍 {original_user.first_name or original_user.username}'s reputation increased by {REPUTATION_GAIN} point(s)!"
                    )

    async def show_rank(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show top 10 users all-time"""
        self.db.add_active_chat(update.effective_chat.id)
        
        top_users = self.db.get_top_users()
        rank_message = generate_leaderboard_message(top_users)
        
        await update.message.reply_text(rank_message, parse_mode='Markdown')

    async def show_my_rank(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's own rank"""
        self.db.add_active_chat(update.effective_chat.id)
        
        user = update.effective_user
        rank_info = self.db.get_user_rank(user.id)
        
        if rank_info:
            rank, reputation = rank_info
            await update.message.reply_text(
                f"🏅 Your Rank: {rank}\n"
                f"💯 Your Reputation: {reputation} points"
            )
        else:
            await update.message.reply_text("You haven't earned any reputation yet!")

    async def daily_top_announcement(self, context: CallbackContext):
        """Send daily top 10 announcement to all active chats"""
        top_users = self.db.get_top_users()
        rank_message = generate_leaderboard_message(top_users, is_daily=True)

        target_chats = self.db.get_active_chats()
        for chat_id in target_chats:
            try:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=rank_message, 
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send daily top 10 message to chat {chat_id}: {e}")

    def run(self):
        """Configure and start the bot"""
        app = Application.builder().token(self.bot_token).build()

        # Command handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler([
            "rank", "ranks", "ranking", "rankings", 
            "rnk", "rak", "rnak", "rangs", 
            "leaderboard", "top", "scoreboard"
        ], self.show_rank))

        app.add_handler(CommandHandler(["myrank", "myranks"], self.show_my_rank))

        # Message handler for replies with reputation words
        app.add_handler(MessageHandler(
            filters.REPLY & filters.TEXT & ~filters.COMMAND,
            self.handle_reply
        ))

        # Schedule daily top 10 announcement if time is set
        if DAILY_TOP_10_TIME:
            try:
                scheduled_time = adjust_time(DAILY_TOP_10_TIME)
                job_queue = app.job_queue
                job_queue.run_daily(self.daily_top_announcement, scheduled_time)
            except ValueError:
                logger.error("Invalid time format for daily top 10 announcement")   

        # Start the bot
        app.run_polling()

def main():
    """Entry point for the bot"""
    try:
        bot = ReputationBot()
        bot.run()
    finally:
        # Ensure database connection is closed when bot stops
        bot.db.close()
if __name__ == '__main__':
    main()