import logging
from typing import TYPE_CHECKING

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

import config

# Avoid circular import for type hinting
if TYPE_CHECKING:
    from bot_core import TriviaBot 

logger = logging.getLogger(__name__)

async def handle_start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE, bot: 'TriviaBot') -> int:
    """Starts the quiz configuration conversation (/start_quiz command)."""
    if update.message:
        await update.message.reply_text(
            "Welcome to the Advanced Trivia Quiz Bot! 🧠\n\n"
            "Let's configure your quiz. First, choose a difficulty:"
        )

    # Difficulty selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("Easy", callback_data="difficulty_easy"),
            InlineKeyboardButton("Medium", callback_data="difficulty_medium"),
            InlineKeyboardButton("Hard", callback_data="difficulty_hard")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("Select Difficulty:", reply_markup=reply_markup)
    else:
        logger.warning("handle_start_conversation called without a message.")
        # Try sending to chat_id from context if available, otherwise log error
        chat_id = context.chat_data.get('chat_id') if context.chat_data else None
        if chat_id:
             await context.bot.send_message(chat_id, "Select Difficulty:", reply_markup=reply_markup)
        else:
             logger.error("Cannot send difficulty selection - no message and no chat_id.")


    return config.DIFFICULTY_SELECTION # Next state

async def handle_select_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE, bot: 'TriviaBot') -> int:
    """Handles difficulty selection (callback query starting with 'difficulty_')."""
    query = update.callback_query
    if not query or not query.data or not query.message:
         logger.warning("handle_select_difficulty called without valid query.")
         return ConversationHandler.END

    await query.answer()

    difficulty = query.data.split('_')[1]
    context.user_data['difficulty'] = difficulty # Store selection in user_data

    logger.info(f"User {query.from_user.id} selected difficulty: {difficulty}")

    # Create category selection keyboard
    keyboard = []
    current_row = []
    sorted_categories = sorted(bot.categories.items(), key=lambda item: item[1]) # Sort alphabetically

    for category_id, category_name in sorted_categories:
        button = InlineKeyboardButton(category_name, callback_data=f"category_{category_id}")
        current_row.append(button)
        
        if len(current_row) == 2: # Max 2 buttons per row
            keyboard.append(current_row)
            current_row = []
    
    if current_row: # Add any remaining button(s)
        keyboard.append(current_row)

    if not keyboard:
         await query.edit_message_text("Could not load categories. Please try /start_quiz again later.")
         logger.error("Category list is empty when trying to display.")
         return ConversationHandler.END

    await query.edit_message_text(
        f"Difficulty: {difficulty.capitalize()}\n\nNow, select a Trivia Category:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return config.CATEGORY_SELECTION # Next state

async def handle_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE, bot: 'TriviaBot') -> int:
    """Handles category selection (callback query starting with 'category_')."""
    query = update.callback_query
    if not query or not query.data or not query.message:
         logger.warning("handle_select_category called without valid query.")
         return ConversationHandler.END

    await query.answer()

    category_id_str = query.data.split('_')[1]
    try:
        category_id = int(category_id_str)
        category_name = bot.categories.get(category_id, "Unknown Category")
        context.user_data['category'] = category_id # Store selection
        logger.info(f"User {query.from_user.id} selected category ID: {category_id} ({category_name})")

    except (ValueError, IndexError):
         logger.error(f"Invalid category callback data received: {query.data}")
         await query.edit_message_text("Invalid category selection. Please try /start_quiz again.")
         return ConversationHandler.END

    # Game length selection keyboard using values from config
    keyboard = [
        [
            InlineKeyboardButton(f"{amount} Qs", callback_data=f"length_{amount}")
            for amount in config.DEFAULT_GAME_LENGTHS
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    difficulty = context.user_data.get('difficulty', 'N/A')
    await query.edit_message_text(
        f"Difficulty: {difficulty.capitalize()}\n"
        f"Category: {category_name}\n\n"
        "Finally, choose the quiz length:",
        reply_markup=reply_markup
    )

    return ConversationHandler.END

async def handle_cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the quiz setup conversation."""
    if update.message:
        await update.message.reply_text("Quiz setup cancelled. Use /start_quiz to try again.")
    logger.info(f"User {update.effective_user.id} cancelled conversation.")
    # Clean up user_data if necessary
    context.user_data.clear()
    return ConversationHandler.END
