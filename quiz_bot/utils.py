import json
import logging
import random
import html
from typing import Dict, List, Any

import requests

import config

logger = logging.getLogger(__name__)

# --- Trivia API ---

def fetch_trivia_categories() -> Dict[int, str]:
    """Fetch available trivia categories from Open Trivia API."""
    try:
        response = requests.get(config.TRIVIA_API_CATEGORY_URL,
                                timeout=config.API_REQUEST_TIMEOUT)
        response.raise_for_status() # Raise an exception for bad status codes

        data = response.json()
        categories = {
            cat['id']: html.unescape(cat['name']) 
            for cat in data.get('trivia_categories', [])
        }
        if not categories:
            logger.warning("No categories fetched from API.")
        return categories
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching categories: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding categories JSON: {e}")
    return {} # Return empty dict on error

def fetch_trivia_questions(difficulty: str, category: int, amount: int) -> List[Dict[str, Any]]:
    """Fetch and process trivia questions from Open Trivia API."""
    params = {
        'amount': amount,
        'difficulty': difficulty,
        'category': category,
        'type': 'multiple'
    }
    try:

        response = requests.get(config.TRIVIA_API_QUESTIONS_URL,
                                params=params,
                                timeout=config.API_REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        if data.get('response_code') == 0:
            processed_questions = []
            for question_data in data.get('results', []):
                # Ensure correct_answer is always included in the list before shuffling
                correct = html.unescape(question_data.get('correct_answer', ''))
                incorrect = [html.unescape(ans) for ans in question_data.get('incorrect_answers', []) if ans]
                
                # Guard against missing answers
                if not correct:
                   logger.warning(f"Question skipped due to missing correct answer: {question_data.get('question')}")
                   continue

                answers = incorrect + [correct]
                random.shuffle(answers)

                processed_questions.append({
                    'question': html.unescape(question_data.get('question', 'N/A')),
                    'answers': answers,
                    'correct_answer': correct,
                    'category': html.unescape(question_data.get('category', 'N/A')),
                    'answered': False
                })
            
            if len(processed_questions) != amount and len(processed_questions) < data.get('results', []):
                 logger.warning(f"Processed {len(processed_questions)} questions, but API returned {len(data.get('results', []))} (requested {amount}). Some might have been skipped.")
            elif len(processed_questions) < amount:
                 logger.warning(f"API returned fewer questions ({len(processed_questions)}) than requested ({amount}) for params: {params}")

            return processed_questions
        elif data.get('response_code') == 1:
            logger.warning(f"API Error (Code 1 - No Results): Could not return results for the specified query. Params: {params}")
            return []
        elif data.get('response_code') == 2:
             logger.warning(f"API Error (Code 2 - Invalid Parameter): Contains an invalid parameter. Params: {params}")
             return []
        elif data.get('response_code') == 5:
             logger.warning(f"API Error (Code 5 - Too Many Requests): Rate limit hit. Please wait before requesting more questions.")

             return []
        else:
            logger.warning(f"API returned unexpected response code: {data.get('response_code')} for params: {params}")
            return [] # Indicate potential issue

    except requests.exceptions.Timeout:
        logger.error(f"Timeout error fetching questions for params: {params}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching questions: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding questions JSON: {e}")
        return []
    except Exception as e: 
        logger.exception(f"Unexpected error processing trivia questions: {e}")
        return []

# --- Best Score Persistence ---

def load_best_scores() -> Dict[int, Dict[str, int]]:
    """
    Load user-specific best scores from the JSON file specified in config.
    Keys are user_ids (int), values are dicts mapping game keys (str) to scores (int).
    Handles conversion of user_id keys from string (JSON) to int.
    """
    scores: Dict[int, Dict[str, int]] = {}
    try:
        with open(config.BEST_SCORES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logger.warning(f"'{config.BEST_SCORES_FILE}' does not contain a dictionary. Starting fresh.")
            return {}

        for user_id_str, user_scores in data.items():
            try:
                user_id = int(user_id_str)
                if isinstance(user_scores, dict):
                    validated_user_scores: Dict[str, int] = {}
                    all_valid = True
                    for game_key, score in user_scores.items():
                        if isinstance(game_key, str) and isinstance(score, int):
                             validated_user_scores[game_key] = score
                        else:
                             logger.warning(f"Invalid entry in scores for user {user_id}: key='{game_key}' ({type(game_key)}), score='{score}' ({type(score)}). Skipping entry.")
                             all_valid = False
                    if all_valid or validated_user_scores: 
                         scores[user_id] = validated_user_scores

                else:
                    logger.warning(f"Invalid score data type for user ID '{user_id_str}': Expected dict, got {type(user_scores)}. Skipping user.")
            except ValueError:
                logger.warning(f"Invalid user ID key '{user_id_str}' found in '{config.BEST_SCORES_FILE}'. Expected integer. Skipping entry.")
        
        return scores

    except FileNotFoundError:
        logger.info(f"'{config.BEST_SCORES_FILE}' not found. Starting with empty scores.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from '{config.BEST_SCORES_FILE}': {e}. Starting fresh.")
        return {}
    except Exception as e:
        logger.exception(f"Unexpected error loading best scores from '{config.BEST_SCORES_FILE}': {e}") # Use logger.exception to include traceback
        return {}

def save_best_scores(scores: Dict[int, Dict[str, int]], filepath: str = config.BEST_SCORES_FILE):
    """
    Save user-specific best scores to the specified JSON file.
    Keys are user_ids (int), values are dicts mapping game keys (str) to scores (int).
    """
    try:

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(scores, f, indent=4, ensure_ascii=False) # Use indent for readability, ensure_ascii=False for broader character support
        logger.info(f"Successfully saved best scores for {len(scores)} users to '{filepath}'")
    except TypeError as e:
         logger.error(f"Data type error saving best scores (potential non-serializable data?): {e}")
    except IOError as e:
        logger.error(f"I/O error writing best scores to '{filepath}': {e}")
    except Exception as e:
        logger.exception(f"Unexpected error saving best scores to '{filepath}': {e}")


# --- Helpers ---

def get_best_score_key(difficulty: str, category_id: int, game_length: int) -> str:
    """Generate a unique key for best score tracking based on game parameters."""
    return f"{difficulty.lower()}|{category_id}|{game_length}"
