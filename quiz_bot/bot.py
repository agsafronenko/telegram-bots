import os
import random
import html
import asyncio
import logging
from typing import Dict, List, Any

import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    ConversationHandler
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
DIFFICULTY_SELECTION, CATEGORY_SELECTION, GAME_LENGTH_SELECTION = range(3)

class TriviaBot:
    def __init__(self, token: str):
        self.token = token
        self.current_games: Dict[int, Dict[str, Any]] = {}
        self.categories = self.fetch_trivia_categories()

    def fetch_trivia_categories(self) -> Dict[int, str]:
        """Fetch available trivia categories from Open Trivia API."""
        url = "https://opentdb.com/api_category.php"
        response = requests.get(url)
        
        if response.status_code == 200:
            categories = {
                cat['id']: cat['name'] 
                for cat in response.json()['trivia_categories']
            }
            return categories
        return {}

    def fetch_trivia_question(self, difficulty: str, category: int) -> Dict[str, Any]:
        """Fetch a trivia question from Open Trivia API."""
        url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}&category={category}&type=multiple"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data['response_code'] == 0:
                question = data['results'][0]
                
                # Combine correct and incorrect answers
                answers = question['incorrect_answers'] + [question['correct_answer']]
                random.shuffle(answers)
                
                return {
                    'question': html.unescape(question['question']),
                    'answers': [html.unescape(ans) for ans in answers],
                    'correct_answer': html.unescape(question['correct_answer']),
                    'category': html.unescape(question['category'])
                }
        return None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the quiz configuration process."""
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
        await update.message.reply_text("Select Difficulty:", reply_markup=reply_markup)

        return DIFFICULTY_SELECTION

    async def select_difficulty(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle difficulty selection."""
        query = update.callback_query
        await query.answer()

        # Extract difficulty
        difficulty = query.data.split('_')[1]
        context.user_data['difficulty'] = difficulty

        # Create category selection keyboard
        keyboard = []
        current_row = []
        for category_id, category_name in self.categories.items():
            button = InlineKeyboardButton(category_name, callback_data=f"category_{category_id}")
            current_row.append(button)
            
            # Create a new row every 2 buttons
            if len(current_row) == 2:
                keyboard.append(current_row)
                current_row = []
        
        # Add any remaining buttons
        if current_row:
            keyboard.append(current_row)

        await query.edit_message_text("Select a Trivia Category:")
        await query.message.reply_text("Choose a Category:", reply_markup=InlineKeyboardMarkup(keyboard))

        return CATEGORY_SELECTION

    async def select_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category selection."""
        query = update.callback_query
        await query.answer()

        # Extract category
        category_id = int(query.data.split('_')[1])
        context.user_data['category'] = category_id
        category_name = self.categories.get(category_id, "Unknown Category")

        # Game length selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("10 Questions", callback_data="length_10"),
                InlineKeyboardButton("25 Questions", callback_data="length_25"),
                InlineKeyboardButton("50 Questions", callback_data="length_50")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Selected Category: {category_name}\n\n"
            "Choose Quiz Length:"
        )
        await query.message.reply_text("Select Number of Questions:", reply_markup=reply_markup)

        return GAME_LENGTH_SELECTION

    async def start_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the quiz based on user selections."""
        query = update.callback_query
        await query.answer()

        # Extract game length
        game_length = int(query.data.split('_')[1])
        context.user_data['game_length'] = game_length

        # Initialize game state
        user_id = query.from_user.id
        self.current_games[user_id] = {
            'difficulty': context.user_data['difficulty'],
            'category': context.user_data['category'],
            'game_length': game_length,
            'current_question': 0,
            'score': 0
        }

        # Send first question
        await self.send_next_question(update, context)

        return ConversationHandler.END

    async def send_next_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send the next trivia question."""
        # Correctly extract user ID from either update or callback query
        if update.callback_query:
            user_id = update.callback_query.from_user.id
        else:
            user_id = update.effective_user.id

        # Check if game exists for this user
        if user_id not in self.current_games:
            if update.callback_query:
                await update.callback_query.message.reply_text("No active game. Start a new quiz with /start")
            else:
                await update.message.reply_text("No active game. Start a new quiz with /start")
            return

        game_state = self.current_games[user_id]

        # Check if game is complete
        if game_state['current_question'] >= game_state['game_length']:
            await self.end_game(update, context)
            return

        # Fetch a new question
        question_data = None
        attempts = 0
        while not question_data and attempts < 3:
            question_data = self.fetch_trivia_question(
                game_state['difficulty'], 
                game_state['category']
            )
            attempts += 1
            
            if not question_data:
                # Wait a bit before retrying
                await asyncio.sleep(1)

        # If still no question after multiple attempts
        if not question_data:
            # Try a different category or difficulty
            alternative_categories = list(self.categories.keys())
            alternative_difficulties = ['easy', 'medium', 'hard']
            
            for alt_category in alternative_categories:
                for alt_difficulty in alternative_difficulties:
                    question_data = self.fetch_trivia_question(
                        alt_difficulty, 
                        alt_category
                    )
                    if question_data:
                        break
                if question_data:
                    break

        # Final check for question data
        if not question_data:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    "Sorry, unable to fetch a question after multiple attempts. "
                    "Please try starting a new quiz."
                )
            elif update.message:
                await update.message.reply_text(
                    "Sorry, unable to fetch a question after multiple attempts. "
                    "Please try starting a new quiz."
                )
            
            # End the current game
            await self.end_game(update, context)
            return

        # Create inline keyboard with answer options
        keyboard = [
            [InlineKeyboardButton(answer, callback_data=str(i)) 
            for i, answer in enumerate(question_data['answers'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send question
        game_state['current_question'] += 1
        game_state['current_question_data'] = question_data

        # Determine the appropriate way to send the message
        if update.callback_query:
            message = await update.callback_query.message.reply_text(
                f"Question {game_state['current_question']}/{game_state['game_length']}\n"
                f"Category: {question_data['category']}\n\n"
                f"{question_data['question']}",
                reply_markup=reply_markup
            )
        elif update.message:
            message = await update.message.reply_text(
                f"Question {game_state['current_question']}/{game_state['game_length']}\n"
                f"Category: {question_data['category']}\n\n"
                f"{question_data['question']}",
                reply_markup=reply_markup
            )

    async def answer_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle answer selection."""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        
        # Check if game exists for this user
        if user_id not in self.current_games:
            await query.message.reply_text("No active game. Start a new quiz with /start")
            return

        # Get current game state and question details
        game_state = self.current_games[user_id]
        current_q = game_state['current_question_data']
        selected_answer = current_q['answers'][int(query.data)]
        
        # Check if answer is correct
        if selected_answer == current_q['correct_answer']:
            # Increment user score
            game_state['score'] += 1
            
            response_text = (
                f"✅ Correct! The answer is: {current_q['correct_answer']}\n"
                f"Current Score: {game_state['score']}/{game_state['current_question']}"
            )
        else:
            response_text = (
                f"❌ Wrong! The correct answer is: {current_q['correct_answer']}\n"
                f"Current Score: {game_state['score']}/{game_state['current_question']}"
            )

        # Edit the original message with result
        await query.edit_message_text(response_text)

        # Send next question or end game
        await self.send_next_question(update, context)

    async def end_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """End the game and show final score."""
        user_id = update.effective_user.id
        game_state = self.current_games[user_id]

        await update.message.reply_text(
            f"🏁 Game Over!\n"
            f"Final Score: {game_state['score']}/{game_state['game_length']}\n"
            f"Difficulty: {game_state['difficulty'].capitalize()}\n"
            f"Category: {self.categories.get(game_state['category'], 'Unknown')}"
        )

        # Remove the game state
        del self.current_games[user_id]

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        await update.message.reply_text("Quiz setup cancelled.")
        return ConversationHandler.END

    def run(self):
        """Run the Telegram bot."""
        # Create the Application and pass it your bot's token
        application = Application.builder().token(self.token).build()

        # Create conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                DIFFICULTY_SELECTION: [
                    CallbackQueryHandler(self.select_difficulty, pattern=r'^difficulty_')
                ],
                CATEGORY_SELECTION: [
                    CallbackQueryHandler(self.select_category, pattern=r'^category_')
                ],
                GAME_LENGTH_SELECTION: [
                    CallbackQueryHandler(self.start_quiz, pattern=r'^length_')
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )

        # Add conversation handler and answer callback
        application.add_handler(conv_handler)
        application.add_handler(CallbackQueryHandler(self.answer_callback))

        # Start the bot
        print("Bot is running... Press Ctrl+C to stop.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    # Get bot token from environment variable
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file")
        return

    bot = TriviaBot(TOKEN)
    bot.run()

if __name__ == '__main__':
    main()