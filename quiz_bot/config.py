import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Telegram Bot Token ---
# Get your Bot Token from BotFather
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# --- Logging Configuration ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Game Settings ---
# Time in seconds allowed to answer each question
ANSWER_TIMEOUT = 30

# Default number of questions options for the user to choose from
DEFAULT_GAME_LENGTHS = [10, 25, 50]

# --- API Settings ---
# Open Trivia Database API URLs
TRIVIA_API_CATEGORY_URL = "https://opentdb.com/api_category.php"
TRIVIA_API_QUESTIONS_URL = "https://opentdb.com/api.php"
# Timeout in seconds for API requests
API_REQUEST_TIMEOUT = 10

# --- Data Persistence ---
# File to store best scores
BEST_SCORES_FILE = 'best_scores.json'

# --- Conversation States ---
# Used by ConversationHandler
DIFFICULTY_SELECTION, CATEGORY_SELECTION = range(2)


# --- Validation ---
if not TELEGRAM_BOT_TOKEN:
    logging.error("FATAL ERROR: TELEGRAM_BOT_TOKEN not found in environment variables.")

