import os
import random
import html
import logging
import json
from typing import Dict, List, Any
import asyncio

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
DIFFICULTY_SELECTION, CATEGORY_SELECTION = range(2)

class TriviaBot:
    def __init__(self, token: str):
        self.token = token
        self.current_games: Dict[int, Dict[str, Any]] = {}
        self.categories = self.fetch_trivia_categories()
        self.best_scores_file = 'best_scores.json'
        self.best_scores = self.load_best_scores()
        self.ANSWER_TIMEOUT = 15  # 15 seconds to answer

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Provide help information about the bot and its commands.
        """
        help_text = (
            "🤖 Advanced Trivia Quiz Bot Help 🧠\n\n"
            "Available Commands:\n"
            "/start_quiz - Start a new trivia quiz\n"
            "   - Choose difficulty level\n"
            "   - Select a category\n"
            "   - Pick number of questions\n\n"
            "/stop_quiz - End the current quiz\n"
            "/help - Show this help message\n\n"
            "Quiz Rules:\n"
            "• You have 15 seconds to answer each question\n"
            "• Select the correct answer to earn points\n"
            "• The bot tracks your best scores per difficulty and category\n\n"
            "Enjoy testing your knowledge! 🏆"
        )
        await update.message.reply_text(help_text)

    async def stop_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Stop the current quiz for the user.
        """
        user_id = update.effective_user.id
        
        if user_id in self.current_games:
            # Cancel any pending timeout task
            game_state = self.current_games[user_id]
            if game_state['timeout_task']:
                game_state['timeout_task'].cancel()
            
            # Remove the game state
            del self.current_games[user_id]
            
            await update.message.reply_text(
                "❌ Quiz stopped. Your progress has been reset.\n"
                "Start a new quiz with /start_quiz"
            )
        else:
            await update.message.reply_text(
                "No active quiz to stop. Start a new quiz with /start_quiz"
            )

    def load_best_scores(self) -> Dict[str, int]:
        """Load best scores from a JSON file."""
        try:
            with open(self.best_scores_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_best_scores(self):
        """Save best scores to a JSON file."""
        try:
            with open(self.best_scores_file, 'w') as f:
                json.dump(self.best_scores, f)
        except Exception as e:
            logger.error(f"Error saving best scores: {e}")

    def get_best_score_key(self, game_state: Dict[str, Any]) -> str:
        """Generate a unique key for best score tracking."""
        return f"{game_state['difficulty']}_{game_state['category']}_{game_state['game_length']}"

    def fetch_trivia_categories(self) -> Dict[int, str]:
        """Fetch available trivia categories from Open Trivia API."""
        url = "https://opentdb.com/api_category.php"
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                categories = {
                    cat['id']: cat['name'] 
                    for cat in response.json()['trivia_categories']
                }
                return categories
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
        return {}

    def fetch_trivia_questions(self, difficulty: str, category: int, amount: int) -> List[Dict[str, Any]]:
        """
        Fetch multiple trivia questions from Open Trivia API.
        
        Args:
            difficulty (str): Question difficulty level
            category (int): Trivia category ID
            amount (int): Number of questions to fetch
        
        Returns:
            List[Dict[str, Any]]: List of parsed question data
        """
        url = f"https://opentdb.com/api.php?amount={amount}&difficulty={difficulty}&category={category}&type=multiple"
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response code
                if data['response_code'] == 0:
                    processed_questions = []
                    for question in data['results']:
                        # Combine correct and incorrect answers
                        answers = question['incorrect_answers'] + [question['correct_answer']]
                        random.shuffle(answers)
                        
                        processed_questions.append({
                            'question': html.unescape(question['question']),
                            'answers': [html.unescape(ans) for ans in answers],
                            'correct_answer': html.unescape(question['correct_answer']),
                            'category': html.unescape(question['category']),
                            'answered': False
                        })
                    
                    return processed_questions
                
                logger.warning(f"API response code: {data['response_code']}")
        
        except Exception as e:
            logger.error(f"Error fetching questions: {e}")
        
        return []

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

        # Send message
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

        # Fetch and generate questions immediately
        difficulty = context.user_data['difficulty']
        
        # Game length selection options
        questions_amounts = [10, 25, 50]

        # Game length selection keyboard
        keyboard = [
            [
                InlineKeyboardButton(f"{amount} Questions", 
                                     callback_data=f"length_{amount}_{amount}")
                for amount in questions_amounts
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Selected Category: {category_name}\n\n"
            "Choose Quiz Length:"
        )
        await query.message.reply_text(
            "Select Number of Questions:", 
            reply_markup=reply_markup
        )

        return ConversationHandler.END

    async def start_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the quiz based on user selections."""
        query = update.callback_query
        await query.answer()

        # Parse callback data
        callback_parts = query.data.split('_')
        game_length = int(callback_parts[1])
        amount_from_callback = int(callback_parts[2])
        print("game length from callback", game_length)
        print("amount from callback", amount_from_callback)

        # Fetch questions for the selected game length
        user_id = query.from_user.id
        difficulty = context.user_data['difficulty']
        category = context.user_data['category']
        
        # Fetch questions for the specific game length
        questions = self.fetch_trivia_questions(difficulty, category, game_length)

        print("length of questions", len(questions))
        # Check if we got enough questions
        if len(questions) < game_length:
            await query.message.reply_text(
                "Sorry, couldn't fetch enough questions. Please try a different category or difficulty."
            )
            return ConversationHandler.END

        # Initialize game state
        self.current_games[user_id] = {
            'difficulty': difficulty,
            'category': category,
            'game_length': game_length,
            'questions': questions,
            'current_question_index': 0,
            'unanswered_questions': list(range(game_length)),
            'score': 0,
            'timeout_task': None
        }

        # Get the first question
        current_q = questions[0]

        # Create inline keyboard with answer options
        keyboard = [
            [InlineKeyboardButton(
                answer, 
                callback_data=f"0_{i}"
            ) for i, answer in enumerate(current_q['answers'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Edit the previous message with the first question
        await query.edit_message_text(
            f"Question 1/{game_length}\n"
            f"Category: {current_q['category']}\n\n"
            f"{current_q['question']}",
            reply_markup=reply_markup
        )

        # Set up timeout
        self.current_games[user_id]['timeout_task'] = asyncio.create_task(
            self.set_timeout(update, context, user_id)
        )

        return ConversationHandler.END

    async def handle_question_timeout(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Handle question timeout."""
        if user_id not in self.current_games:
            return

        game_state = self.current_games[user_id]
        current_q = game_state['questions'][game_state['current_question_index']]

        # Mark question as answered (even though it's a timeout)
        current_q['answered'] = True

        # Remove the current question index from unanswered questions
        if game_state['current_question_index'] in game_state['unanswered_questions']:
            game_state['unanswered_questions'].remove(game_state['current_question_index'])

        response_text = (
            f"⏰ Time's up! You didn't answer in time.\n"
            f"The correct answer was: {current_q['correct_answer']}\n"
            f"Current Score: {game_state['score']}/{game_state['current_question_index'] + 1}"
        )

        await update.callback_query.message.chat.send_message(response_text)

        # Move to next question
        game_state['current_question_index'] += 1

        # Send next question or end game
        await self.send_next_question(update, context)

    async def send_next_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send the next trivia question as a new message."""
        # Correctly extract user ID from either update or callback query
        if update.callback_query:
            user_id = update.callback_query.from_user.id
            current_message = update.callback_query.message
        else:
            user_id = update.effective_user.id
            current_message = update.message

        # Check if game exists for this user
        if user_id not in self.current_games:
            await current_message.reply_text("No active game. Start a new quiz with /start")
            return

        game_state = self.current_games[user_id]

        # Find next unanswered question
        if not game_state['unanswered_questions']:
            await self.end_game(update, context)
            return

        # Set current question index to the next unanswered question
        game_state['current_question_index'] = game_state['unanswered_questions'][0]
        current_q = game_state['questions'][game_state['current_question_index']]

        # Create inline keyboard with answer options
        keyboard = [
            [InlineKeyboardButton(
                answer, 
                callback_data=f"{game_state['current_question_index']}_{i}", 
                callback_game=True if current_q['answered'] else None
            ) for i, answer in enumerate(current_q['answers'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send a new message with the question
        await current_message.chat.send_message(
            f"Question {game_state['current_question_index'] + 1}/{game_state['game_length']}\n"
            f"Category: {current_q['category']}\n\n"
            f"{current_q['question']}",
            reply_markup=reply_markup
        )

        # Set up timeout
        game_state['timeout_task'] = asyncio.create_task(
            self.set_timeout(update, context, user_id)
        )

    async def set_timeout(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Set a timeout for answering the question."""
        await asyncio.sleep(self.ANSWER_TIMEOUT)
        
        # Check if game still exists
        if user_id in self.current_games:
            await self.handle_question_timeout(update, context, user_id)

    async def answer_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle answer selection."""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        
        # Check if game exists for this user
        if user_id not in self.current_games:
            logger.warning(f"User {user_id} tried to answer a question without an active game or changed answer before fetching data from server")

        # Cancel timeout task if it exists
        game_state = self.current_games[user_id]
        if game_state['timeout_task']:
            game_state['timeout_task'].cancel()

        # Parse callback data to get question index and answer index
        callback_data = query.data.split('_')
        question_index = int(callback_data[0])
        answer_index = int(callback_data[1])

        # Get current question details
        current_q = game_state['questions'][question_index]
        
        # Prevent answering already answered questions
        if current_q['answered']:
            await query.answer("This question has already been answered!")
            return

        selected_answer = current_q['answers'][answer_index]
        
        # Check if answer is correct
        if selected_answer == current_q['correct_answer']:
            # Increment user score
            game_state['score'] += 1
            
            response_text = (
                f"✅ Correct! The answer is: {current_q['correct_answer']}\n"
                f"Current Score: {game_state['score']}/{question_index + 1}"
            )
        else:
            response_text = (
                f"❌ Wrong! The correct answer is: {current_q['correct_answer']}\n"
                f"Current Score: {game_state['score']}/{question_index + 1}"
            )

        # Mark question as answered
        current_q['answered'] = True

        # Remove the current question from unanswered questions
        if question_index in game_state['unanswered_questions']:
            game_state['unanswered_questions'].remove(question_index)

        # Send a new message as a reply to the original message
        await query.message.chat.send_message(response_text)

        # Move to next question
        await self.send_next_question(update, context)

    async def end_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """End the game and show final score."""
        # Correctly extract user ID
        if update.callback_query:
            user_id = update.callback_query.from_user.id
        else:
            user_id = update.effective_user.id

        game_state = self.current_games[user_id]

        # Determine best score for this configuration
        best_score_key = self.get_best_score_key(game_state)
        previous_best_score = self.best_scores.get(best_score_key, 0)
        
        # Update best score if current score is higher
        congratulations = ""
        if game_state['score'] > previous_best_score:
            self.best_scores[best_score_key] = game_state['score']
            self.save_best_scores()
            congratulations = "🎉 New Personal Best! 🎉\n"

        # Determine the appropriate way to send the message
        message_method = (update.callback_query.message.reply_text 
                          if update.callback_query 
                          else update.message.reply_text)

        await message_method(
            f"🏁 Game Over!\n"
            f"{congratulations}"
            f"Final Score: {game_state['score']}/{game_state['game_length']}\n"
            f"Best Score: {self.best_scores.get(best_score_key, game_state['score'])}\n"
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
            entry_points=[CommandHandler("start_quiz", self.start)],
            states={
                DIFFICULTY_SELECTION: [
                    CallbackQueryHandler(self.select_difficulty, pattern=r'^difficulty_')
                ],
                CATEGORY_SELECTION: [
                    CallbackQueryHandler(self.select_category, pattern=r'^category_')
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )

        # Add conversation handler, answer callback, help, and stop quiz handlers
        application.add_handler(conv_handler)
        application.add_handler(CallbackQueryHandler(self.start_quiz, pattern=r'^length_'))
        application.add_handler(CallbackQueryHandler(self.answer_callback))

        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("stop_quiz", self.stop_quiz))

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