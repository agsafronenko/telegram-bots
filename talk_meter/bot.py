import asyncio
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters
)

from config import (
    DATABASE_PATH, 
    SPAM_THRESHOLD,
    PERIODS
)
from database import DatabaseManager
from leaderboard import LeaderboardManager
from notifications import NotificationManager

load_dotenv()

class LeaderboardBot:
    def __init__(self):
        # Initialize database
        self.db_manager = DatabaseManager(DATABASE_PATH)
        
        # Initialize leaderboard manager
        self.leaderboard_manager = LeaderboardManager(self.db_manager)
        
        # Create bot application
        TELEGRAM_BOT_TOKEN = os.getenv("TALK_METER")
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Message tracking
        self.user_message_track = {}

    def setup_handlers(self):
        """Set up command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("rank", self.rank_command))
        self.application.add_handler(CommandHandler("mystats", self.mystats_command))
        
        # Period-specific rank commands
        for period, period_name in PERIODS.items():
            if period != 'alltime':
                method_name = f"{period}rank_command"
                handler = CommandHandler(f"{period}rank", getattr(self, method_name))
                self.application.add_handler(handler)
        
        # Notification commands
        self.application.add_handler(CommandHandler("notifyme", self.notifyme_command))
        self.application.add_handler(CommandHandler("stopnotify", self.stopnotify_command))
        
        # Message handler with spam protection
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Initialize notification manager
        self.notification_manager = NotificationManager(
            self.application.bot, 
            self.db_manager
        )

    async def start_command(self, update: Update, context):
        """Handle /start command."""
        await update.message.reply_text(
            "Welcome to the Leaderboard Bot! 🏆\n"
            "Track your messaging stats and compete with others.\n\n"
            "📢 *Important:* To receive leaderboard notifications, you must start a private chat with this bot first. "
            "Bots *cannot* message users unless they have interacted with them first.\n\n"
            "🔹 *Available Commands:*\n"
            "/rank - All-time ranking\n"
            "/dayrank - Today's ranking\n"
            "/weekrank - Weekly ranking\n"
            "/monthrank - Monthly ranking\n"
            "/mystats - Your personal stats\n"
            "/notifyme - Get leaderboard updates\n"
            "/stopnotify - Stop leaderboard notifications\n\n"
        )

    async def handle_message(self, update: Update, context):
        """Handle incoming messages with spam protection."""
        user = update.effective_user
        current_time = datetime.now()
        
        # Initialize or update user tracking
        if user.id not in self.user_message_track:
            self.user_message_track[user.id] = []
        
        # Remove old messages from tracking
        self.user_message_track[user.id] = [
            msg_time for msg_time in self.user_message_track[user.id]
            if (current_time - msg_time).total_seconds() <= SPAM_THRESHOLD['time_window']
        ]
        
        # Check spam
        if len(self.user_message_track[user.id]) >= SPAM_THRESHOLD['messages']:
            return  # Ignore spam
        
        # Track message
        self.user_message_track[user.id].append(current_time)
        
        # Process message for leaderboard and milestones
        milestones = self.leaderboard_manager.process_message(
            user.id, 
            user.username or user.first_name
        )

        # Announce milestones
        if milestones:

            for milestone in milestones:
                text = (f"🎉 Congratulations! [{user.first_name or user.username}](tg://user?id={user.id}) "
                        f"has reached {milestone} messages!")   
                await update.message.reply_text(text=text,parse_mode='Markdown')


    async def rank_command(self, update: Update, context):
        """Show all-time leaderboard."""
        message = self.leaderboard_manager.get_leaderboard_message(
            'all-time', 
            update.effective_user.id
        )
        await update.message.reply_text(text=message, parse_mode='Markdown')

    async def dayrank_command(self, update: Update, context):
        """Show daily leaderboard."""
        message = self.leaderboard_manager.get_leaderboard_message(
            'day', 
            update.effective_user.id
        )
        await update.message.reply_text(text=message, parse_mode='Markdown')

    async def weekrank_command(self, update: Update, context):
        """Show weekly leaderboard."""
        message = self.leaderboard_manager.get_leaderboard_message(
            'week', 
            update.effective_user.id
        )
        await update.message.reply_text(text=message, parse_mode='Markdown')

    async def monthrank_command(self, update: Update, context):
        """Show monthly leaderboard."""
        message = self.leaderboard_manager.get_leaderboard_message(
            'month', 
            update.effective_user.id
        )
        await update.message.reply_text(text=message, parse_mode='Markdown')

    async def mystats_command(self, update: Update, context):
        """Show user's personal stats."""
        message = self.leaderboard_manager.get_user_stats(update.effective_user.id)
        await update.message.reply_text(message)

    async def notifyme_command(self, update: Update, context):
        """Enable leaderboard notifications."""
        print("notifyme_command turned on")
        self.db_manager.toggle_notifications(update.effective_user.id, True)
        await update.message.reply_text("You will now receive leaderboard update notifications.")

    async def stopnotify_command(self, update: Update, context):
        """Disable leaderboard notifications."""
        self.db_manager.toggle_notifications(update.effective_user.id, False)
        await update.message.reply_text("You will no longer receive leaderboard update notifications.")

    async def start_periodic_checks(self):
        """Perform a leaderboard check."""
        for period in PERIODS:
            if period != 'alltime':
                await self.notification_manager.check_leaderboard_changes(period)

    def run(self):
        """Run the bot."""
        self.setup_handlers()
        
        # Run periodic checks
        self.application.job_queue.run_repeating(
            lambda context: asyncio.create_task(self.start_periodic_checks()), 
            interval=3600, 
            first=0
        )
        
        # Start the Bot
        self.application.run_polling(drop_pending_updates=True)

def main():
    bot = LeaderboardBot()
    bot.run()

if __name__ == '__main__':
    main()
