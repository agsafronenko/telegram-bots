import logging
from typing import Dict, Any

import config
import utils
import handlers
import conversation
import game

logger = logging.getLogger(__name__)

class TriviaBot:
    """
    Core class for the Trivia Bot.
    Holds state and routes commands/callbacks to specific handlers.
    """
    def __init__(self, token: str):
        if not token:
            logger.critical("Bot token is missing. Cannot initialize.")
            raise ValueError("Telegram Bot Token is required.")
        self.token = token
        
        # --- State ---
        # Stores active games, keyed by user_id
        self.current_games: Dict[int, Dict[str, Any]] = {} 
        # Stores category ID -> category name mapping
        self.categories: Dict[int, str] = {} 
        # Stores best scores, keyed by utils.get_best_score_key()
        self.best_scores: Dict[int, Dict[str, int]] = {} 
        
        # --- Configuration ---
        self.answer_timeout = config.ANSWER_TIMEOUT
        self.best_scores_file = config.BEST_SCORES_FILE

        # --- Initialization ---
        self._load_initial_data()
        
    def _load_initial_data(self):
        """Loads categories and best scores on startup."""
        logger.info("Loading initial data...")
        self.categories = utils.fetch_trivia_categories()
        if not self.categories:
             logger.warning("Failed to fetch trivia categories on startup. Category selection may fail.")
        else:
             logger.info(f"Loaded {len(self.categories)} categories.")
             
        self.best_scores = utils.load_best_scores()
        logger.info(f"Loaded best score records for {len(self.best_scores)} users from '{self.best_scores_file}'.")

    # --- Method Wrappers for Handlers ---

    # Command Handlers
    async def help_command(self, update, context):
        await handlers.handle_help_command(update, context, self)

    async def stop_quiz_command(self, update, context):
        await handlers.handle_stop_quiz(update, context, self)

    # Conversation Handlers (need to return state for ConversationHandler)
    async def start_conversation(self, update, context):
        return await conversation.handle_start_conversation(update, context, self)

    async def select_difficulty_callback(self, update, context):
        return await conversation.handle_select_difficulty(update, context, self)

    async def select_category_callback(self, update, context):
        return await conversation.handle_select_category(update, context, self)
        
    async def cancel_conversation(self, update, context):
        return await conversation.handle_cancel_conversation(update, context)


    # Game Logic Callbacks (outside conversation)
    async def start_quiz_callback(self, update, context):
        await game.handle_start_quiz(update, context, self)

    async def answer_callback(self, update, context):
        await game.handle_answer_callback(update, context, self)

