import logging
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import ContextTypes

# Avoid circular import for type hinting
if TYPE_CHECKING:
    from bot_core import TriviaBot 

logger = logging.getLogger(__name__)

async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, bot: 'TriviaBot') -> None:
    """
    Provide help information about the bot and its commands.
    Invoked by the /help command.
    """

    help_text = (
        "🤖 Advanced Trivia Quiz Bot Help 🧠\n\n"
        "Available Commands:\n"
        "/start_quiz - Begin setting up a new trivia quiz\n"
        "   - Choose difficulty level\n"
        "   - Select a category\n"
        "   - Pick number of questions\n\n"
        "/stop_quiz - Immediately end your current quiz\n"
        "/help - Show this help message\n\n"
        "Quiz Rules:\n"
        f"• You have {bot.answer_timeout} seconds to answer each question\n"
        "• Select the correct answer by tapping the buttons\n"
        "• The bot tracks your personal best score for each combination of "
        "difficulty, category, and length\n\n"
        "Enjoy testing your knowledge! 🏆"
    )
    if update.message:
        await update.message.reply_text(help_text)
    else:
         logger.warning("handle_help_command called without a message.")

async def handle_stop_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, bot: 'TriviaBot') -> None:
    """
    Stop the current quiz for the user.
    Invoked by the /stop_quiz command.
    """
    user_id = update.effective_user.id if update.effective_user else None
    
    if user_id and user_id in bot.current_games:
        game_state = bot.current_games[user_id]
        
        # Cancel any pending timeout task for this game
        if game_state.get('timeout_task'):
            game_state['timeout_task'].cancel()
            logger.info(f"Timeout task cancelled for user {user_id} via /stop_quiz.")
        
        # Remove the game state
        del bot.current_games[user_id]
        logger.info(f"Quiz stopped and game state removed for user {user_id}.")
        
        reply_message = ("❌ Quiz stopped. Your progress for this session is lost.\n"
                         "Start a new quiz with /start_quiz when you're ready!")
    else:
        reply_message = "🤷 No active quiz found for you to stop. Start one with /start_quiz"

    if update.message:
        await update.message.reply_text(reply_message)
    else:
        logger.warning("handle_stop_quiz called without a message.")
