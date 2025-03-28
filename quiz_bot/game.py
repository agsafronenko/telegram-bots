import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import config
import utils
# Avoid circular import for type hinting
if TYPE_CHECKING:
    from bot_core import TriviaBot 

logger = logging.getLogger(__name__)

# --- Timeout Handling ---

async def _handle_question_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, bot: 'TriviaBot'):
    """Internal function to process a question timeout."""
    if user_id not in bot.current_games:
        logger.debug(f"Timeout triggered for user {user_id}, but game no longer exists.")
        return

    game_state = bot.current_games[user_id]
    q_index = game_state['current_question_index']
    
    # Ensure the timeout corresponds to the *current* question being displayed
    if q_index >= len(game_state['questions']) or game_state['questions'][q_index]['answered']:
         logger.debug(f"Timeout for user {user_id} on Q{q_index}, but it was already answered or out of bounds.")
         return # Question already answered or game moved on

    current_q = game_state['questions'][q_index]
    current_q['answered'] = True # Mark as answered (timed out)
    
    # Safety check before removing - should always be present if unanswered
    if q_index in game_state.get('unanswered_indices', []):
        game_state['unanswered_indices'].remove(q_index)

    logger.info(f"User {user_id} timed out on question {q_index + 1}.")

    response_text = (
        f"⏰ Time's up for question {q_index + 1}!\n"
        f"Correct Answer: {current_q['correct_answer']}\n\n"
        f"Current Score: {game_state['score']}/{game_state['game_length']}"
    )

    # Try sending message to the chat
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id:
         try:
             await context.bot.send_message(chat_id=chat_id, text=response_text)
         except Exception as e:
             logger.error(f"Error sending timeout message to chat {chat_id}: {e}")
    else:
        logger.error(f"Cannot send timeout message: No chat ID found for user {user_id}.")


    # Move to next question or end game
    await handle_send_next_question(update, context, bot)


async def _set_question_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, bot: 'TriviaBot'):
    """Coroutine that waits and triggers the timeout handler."""
    await asyncio.sleep(bot.answer_timeout)
    
    # Check if game still exists *before* calling the handler
    if user_id in bot.current_games:
        await _handle_question_timeout(update, context, user_id, bot)
    else:
        logger.debug(f"Timeout sleep finished for user {user_id}, but game ended before execution.")


# --- Game Flow ---

async def handle_start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, bot: 'TriviaBot') -> None:
    """Starts the actual quiz after configuration (callback query starting with 'length_')."""
    query = update.callback_query
    if not query or not query.data or not query.message or not query.from_user:
         logger.warning("handle_start_quiz called without valid query.")
         return
    
    await query.answer()

    user_id = query.from_user.id
    
    # --- Prevent starting multiple games ---
    if user_id in bot.current_games:
        logger.warning(f"User {user_id} tried to start a new quiz while one is active.")
        await query.edit_message_text("You already have a quiz in progress! Use /stop_quiz first if you want to start over.")
        return
        
    # --- Get parameters from context and callback ---
    difficulty = context.user_data.get('difficulty')
    category = context.user_data.get('category')
    
    try:
        game_length_str = query.data.split('_')[1]
        game_length = int(game_length_str)
    except (IndexError, ValueError):
        logger.error(f"Invalid game length callback data: {query.data}")
        await query.edit_message_text("Invalid game length selected. Please /start_quiz again.")
        return

    if not difficulty or category is None:
        logger.error(f"Missing difficulty or category for user {user_id} when starting quiz.")
        await query.edit_message_text("Something went wrong with setup (missing difficulty or category). Please /start_quiz again.")
        return

    logger.info(f"Starting quiz for user {user_id}: Diff={difficulty}, Cat={category}, Len={game_length}")
    
    # --- Fetch Questions ---
    await query.edit_message_text("Starting quiz... Fetching questions...")
    
    questions = utils.fetch_trivia_questions(difficulty, category, game_length)

    if not questions or len(questions) < game_length:
        logger.warning(f"Could not fetch enough ({len(questions)}/{game_length}) questions for user {user_id}.")
        await query.edit_message_text(
            "😕 Sorry, couldn't fetch enough questions for this combination.\n"
            "Maybe try a different category, difficulty, or length?\n"
            "Use /start_quiz to try again."
        )
        # Clean partial setup data
        context.user_data.clear() 
        return

    # --- Initialize Game State ---
    bot.current_games[user_id] = {
        'difficulty': difficulty,
        'category': category,
        'category_name': bot.categories.get(category, "Unknown"), # Store name for end message
        'game_length': game_length,
        'questions': questions,
        'current_question_index': 0, # Start at the first question
        'unanswered_indices': list(range(game_length)), # List of indices yet to be asked/answered
        'score': 0,
        'timeout_task': None,
        'last_message_id': None 
    }

    logger.info(f"Game state initialized for user {user_id}. Starting first question.")
    
    # --- Send First Question ---
    await handle_send_next_question(update, context, bot)
    
    # Clean up setup data from user_data after successful start
    context.user_data.clear() 


async def handle_send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE, bot: 'TriviaBot') -> None:
    """Sends the next available question or ends the game if none are left."""
    user_id = update.effective_user.id if update.effective_user else None
    
    # Use query if available (indicates it follows a button press)
    query = update.callback_query
    chat_id = query.message.chat.id if query and query.message else update.effective_chat.id
    
    if not user_id or user_id not in bot.current_games:
        # This might happen if a timeout triggers after /stop_quiz
        logger.debug(f"handle_send_next_question called for user {user_id}, but no active game found.")
        # Optionally send a message if chat_id is known
        # if chat_id: await context.bot.send_message(chat_id, "No active game found.")
        return

    game_state = bot.current_games[user_id]

    # --- Check if Game Ended ---
    if not game_state['unanswered_indices']:
        logger.info(f"No more unanswered questions for user {user_id}. Ending game.")
        await handle_end_game(update, context, bot)
        return

    # --- Get Next Question ---
    # Always take the first index from the remaining list
    next_q_index = game_state['unanswered_indices'][0] 
    game_state['current_question_index'] = next_q_index # Update current index track
    current_q = game_state['questions'][next_q_index]

    # --- Create Keyboard ---
    keyboard = []
    # Create buttons in a 2-column layout if possible
    answers = current_q['answers']
    row = []
    for i, answer in enumerate(answers):
         # Callback data: "ans_{question_index}_{answer_index}"
        row.append(InlineKeyboardButton(answer, callback_data=f"ans_{next_q_index}_{i}"))
        if len(row) == (1 if len(answers) <= 2 else 2): # Single button per row if only 1 or 2 answers total
            keyboard.append(row)
            row = []
    if row: # Add remaining button if odd number > 2
        keyboard.append(row)
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Display index starts from 1
    question_number = game_state['game_length'] - len(game_state['unanswered_indices']) + 1 

    question_text = (
        f"❓ Question {question_number}/{game_state['game_length']}\n"
        f"Category: {current_q['category']}\n\n"
        f"{current_q['question']}"
    )

    # --- Send/Edit Message ---
    try:
        sent_message = await context.bot.send_message(
            chat_id=chat_id,
            text=question_text,
            reply_markup=reply_markup
        )
        game_state['last_message_id'] = sent_message.message_id
        logger.debug(f"Sent question {next_q_index + 1} to user {user_id}")

    except Exception as e:
        logger.error(f"Failed to send question {next_q_index + 1} to user {user_id}: {e}")
        del bot.current_games[user_id] 
        await context.bot.send_message(chat_id, "An error occurred sending the question. Quiz aborted.")
        return

    # --- Set Timeout for the New Question ---
    # Cancel previous timeout task if it exists and hasn't finished
    if game_state.get('timeout_task') and not game_state['timeout_task'].done():
        game_state['timeout_task'].cancel()
        logger.debug(f"Previous timeout task cancelled for user {user_id}.")

    game_state['timeout_task'] = asyncio.create_task(
        _set_question_timeout(update, context, user_id, bot)
    )
    logger.debug(f"Timeout task created for user {user_id}, Q{next_q_index + 1}.")


async def handle_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, bot: 'TriviaBot') -> None:
    """Handles a user's answer selection (callback query starting with 'ans_')."""
    query = update.callback_query
    if not query or not query.data or not query.message or not query.from_user:
         logger.warning("handle_answer_callback received invalid query.")
         return

    await query.answer()

    user_id = query.from_user.id

    if user_id not in bot.current_games:
        logger.warning(f"User {user_id} answered, but no active game found.")


    game_state = bot.current_games[user_id]

    # --- Cancel Timeout ---
    if game_state.get('timeout_task') and not game_state['timeout_task'].done():
        game_state['timeout_task'].cancel()
        logger.debug(f"Timeout task cancelled due to answer from user {user_id}.")

    # --- Parse Callback Data ---
    try:
        _, question_index_str, answer_index_str = query.data.split('_')
        question_index = int(question_index_str)
        answer_index = int(answer_index_str)
    except (ValueError, IndexError):
        logger.error(f"Invalid answer callback data format: {query.data}")
        return

    # --- Validate Answer Attempt ---
    # Check if the answered question is the *current* one expected
    if question_index != game_state.get('current_question_index'):
         logger.warning(f"User {user_id} answered Q{question_index+1}, but current is {game_state.get('current_question_index', 'N/A')+1}. Ignoring.")
         return # Ignore answer for old/future question

    # Check if already answered (e.g., double-click)
    if question_index >= len(game_state['questions']) or game_state['questions'][question_index]['answered']:
        logger.debug(f"User {user_id} tried to answer Q{question_index+1} which is already answered.")
        await query.answer("Already answered!")
        return

    # --- Process Answer ---
    current_q = game_state['questions'][question_index]
    selected_answer = current_q['answers'][answer_index]
    is_correct = (selected_answer == current_q['correct_answer'])

    current_q['answered'] = True # Mark as answered
    
    # Remove from unanswered list - safety check
    if question_index in game_state.get('unanswered_indices', []):
        game_state['unanswered_indices'].remove(question_index)
    else:
         logger.warning(f"Index {question_index} was not in unanswered list for user {user_id} when answering.")


    result_icon = "✅" if is_correct else "❌"
    if is_correct:
        game_state['score'] += 1
        result_text = "Correct!"
        logger.info(f"User {user_id} answered Q{question_index + 1} correctly.")
    else:
        result_text = f"Wrong! Correct was: {current_q['correct_answer']}"
        logger.info(f"User {user_id} answered Q{question_index + 1} incorrectly.")

    # --- Provide Feedback ---
    feedback_text = (
        f"{result_icon} {result_text}\n"
        f"Score: {game_state['score']}/{game_state['game_length']}"
    )
    
    # Edit the question message to show the result and disable the keyboard
    try:
        await query.edit_message_text(
            f"{query.message.text}\n\n---\n{feedback_text}", # Append result to original question text
            reply_markup=None # Remove keyboard
        )
    except Exception as e:
         # If editing fails (e.g., message too old), send a new message
         logger.warning(f"Failed to edit message for answer feedback (user {user_id}): {e}. Sending new message.")
         try:
             await query.message.reply_text(feedback_text)
         except Exception as e2:
             logger.error(f"Failed to send new message for answer feedback (user {user_id}): {e2}")
             
    # --- Move to Next Question ---
    # Add a small delay before sending the next question
    await asyncio.sleep(1.5) 
    await handle_send_next_question(update, context, bot)


async def handle_end_game(update: Update, context: ContextTypes.DEFAULT_TYPE, bot: 'TriviaBot') -> None:
    """Ends the game, calculates final score, updates best score, and removes game state."""
    user_id = update.effective_user.id if update.effective_user else None
    query = update.callback_query
    chat_id = query.message.chat.id if query and query.message else update.effective_chat.id

    if not user_id or user_id not in bot.current_games:
        logger.warning(f"handle_end_game called for user {user_id} but no game found.")
        if chat_id: await context.bot.send_message(chat_id, "Couldn't find a game to end.")
        return

    game_state = bot.current_games[user_id]
    logger.info(f"Ending game for user {user_id}. Final Score: {game_state['score']}/{game_state['game_length']}")

    # --- Best Score Logic ---
    # --- Best Score Logic (USER-SPECIFIC) ---
    current_score = game_state['score']
    game_key = utils.get_best_score_key(
        game_state['difficulty'], game_state['category'], game_state['game_length']
    )

    # Get the dictionary of scores for *this specific user*
    # If the user isn't in best_scores yet, default to an empty dictionary
    user_best_scores = bot.best_scores.get(user_id, {})

    # Get the previous best score for *this user* and *this game configuration*
    # If no previous score exists for this config, default to 0
    previous_best_score = user_best_scores.get(game_key, 0)





    # best_score_key = utils.get_best_score_key(
    #     game_state['difficulty'], game_state['category'], game_state['game_length']
    # )
    # previous_best_score = bot.best_scores.get(best_score_key, 0)
    # current_score = game_state['score']
    
    congratulations = ""
    new_best = False
    if current_score > previous_best_score:
        # Ensure the user's entry exists in the main dictionary
        if user_id not in bot.best_scores:
            bot.best_scores[user_id] = {}
        # Update the score for this user and game configuration
        bot.best_scores[user_id][game_key] = current_score
        new_best = True
        # Pass the entire best_scores dictionary (now potentially updated) to save
        utils.save_best_scores(bot.best_scores, bot.best_scores_file)
        congratulations = f"🎉 New Personal Best for this setup ({current_score} points)! 🎉\n"
        logger.info(f"User {user_id} achieved new best score for key '{game_key}': {current_score}")

    # Determine the score to display (either the new best or the existing one)
    # Safely get the potentially updated score
    best_score_display = bot.best_scores.get(user_id, {}).get(game_key, 0)

    # --- Send Final Message ---
    final_text = (
        f"🏁 Quiz Finished! 🏁\n\n"
        f"{congratulations}"
        f"Your final score: {current_score}/{game_state['game_length']}\n"
        f"Your best score for this setup: {best_score_display}\n\n"
        f"Difficulty: {game_state['difficulty'].capitalize()}\n"
        f"Category: {game_state['category_name']}\n\n"
        "Use /start_quiz to play again!"
    )

    try:
        # Send as a new message
        await context.bot.send_message(chat_id=chat_id, text=final_text)
    except Exception as e:
        logger.error(f"Failed to send final score message to user {user_id}: {e}")

    # --- Clean Up ---
    # Cancel timeout task just in case it's still pending somehow
    if game_state.get('timeout_task') and not game_state['timeout_task'].done():
        game_state['timeout_task'].cancel()
    
    del bot.current_games[user_id] # Remove game state from memory
    logger.info(f"Game state cleaned up for user {user_id}.")

