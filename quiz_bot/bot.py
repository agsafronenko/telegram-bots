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
    ContextTypes
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TriviaBot:
    def __init__(self, token: str):
        self.token = token
        self.current_questions: Dict[int, Dict[str, Any]] = {}
        self.user_scores: Dict[int, int] = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        await update.message.reply_text(
            "Welcome to the Trivia Quiz Bot! 🧠\n\n"
            "Available commands:\n"
            "/start - Begin the bot\n"
            "/quiz - Start a new quiz\n"
            "/score - Check your current score\n"
            "/help - Show help information"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Provide help information."""
        await update.message.reply_text(
            "How to play:\n"
            "• Use /quiz to start a new quiz\n"
            "• Answer questions by clicking the buttons\n"
            "• Each correct answer gives you 1 point\n"
            "• Use /score to check your total points\n"
            "• Enjoy learning and testing your knowledge!"
        )

    def fetch_trivia_question(self, difficulty: str = 'medium') -> Dict[str, Any]:
        """Fetch a trivia question from Open Trivia API."""
        url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}&type=multiple"
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

    async def quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start a new quiz question."""
        # Fetch a trivia question
        question_data = self.fetch_trivia_question()
        
        if not question_data:
            await update.message.reply_text("Sorry, couldn't fetch a question. Please try again.")
            return

        # Create inline keyboard with answer options
        keyboard = [
            [InlineKeyboardButton(answer, callback_data=str(i)) 
             for i, answer in enumerate(question_data['answers'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send question
        message = await update.message.reply_text(
            f"Category: {question_data['category']}\n\n"
            f"{question_data['question']}",
            reply_markup=reply_markup
        )

        # Store current question for the user
        self.current_questions[update.effective_user.id] = {
            'question': question_data,
            'message_id': message.message_id
        }

    async def answer_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle answer selection."""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        
        # Check if question exists for this user
        if user_id not in self.current_questions:
            await query.edit_message_text("No active question. Start a new quiz with /quiz")
            return

        # Get current question details
        current_q = self.current_questions[user_id]['question']
        selected_answer = current_q['answers'][int(query.data)]
        
        # Check if answer is correct
        if selected_answer == current_q['correct_answer']:
            # Increment user score
            self.user_scores[user_id] = self.user_scores.get(user_id, 0) + 1
            
            response_text = (
                f"✅ Correct! The answer is: {current_q['correct_answer']}\n"
                f"Your current score: {self.user_scores[user_id]} points"
            )
        else:
            response_text = (
                f"❌ Wrong! The correct answer is: {current_q['correct_answer']}\n"
                f"Your current score: {self.user_scores.get(user_id, 0)} points"
            )

        # Remove the current question
        del self.current_questions[user_id]

        # Edit the original message
        await query.edit_message_text(response_text)

    async def show_score(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display user's current score."""
        user_id = update.effective_user.id
        score = self.user_scores.get(user_id, 0)
        await update.message.reply_text(f"Your current score: {score} points 🏆")

    def run(self):
        """Run the Telegram bot."""
        # Create the Application and pass it your bot's token
        application = Application.builder().token(self.token).build()

        # Register handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("quiz", self.quiz))
        application.add_handler(CommandHandler("score", self.show_score))
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
