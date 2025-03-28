import json
import logging
import random
import html
from typing import Dict, List, Any

import requests

import config

logger = logging.getLogger(__name__)

def fetch_trivia_categories() -> Dict[int, str]:
    """Fetch available trivia categories from Open Trivia API."""
    try:
        response = requests.get(config.TRIVIA_API_CATEGORY_URL, 
                                timeout=config.API_REQUEST_TIMEOUT)
        response.raise_for_status() # Raise an exception for bad status codes
        
        data = response.json()
        categories = {
            cat['id']: cat['name']
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
                answers = question_data.get('incorrect_answers', []) + \
                          [question_data.get('correct_answer', '')]
                random.shuffle(answers)
                
                processed_questions.append({
                    'question': html.unescape(question_data.get('question', 'N/A')),
                    'answers': [html.unescape(ans) for ans in answers if ans],
                    'correct_answer': html.unescape(question_data.get('correct_answer', '')),
                    'category': html.unescape(question_data.get('category', 'N/A')),
                    'answered': False 
                })
            return processed_questions
        else:
            logger.warning(f"API response code not 0: {data.get('response_code')}")
            return [] # Indicate potential issue fetching specific questions

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching questions: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding questions JSON: {e}")
    return [] # Return empty list on error

def load_best_scores() -> Dict[str, int]:
    """Load best scores from the JSON file specified in config."""
    try:
        with open(config.BEST_SCORES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info(f"'{config.BEST_SCORES_FILE}' not found. Starting with empty scores.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding '{config.BEST_SCORES_FILE}': {e}. Starting fresh.")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading best scores: {e}")
        return {}

def save_best_scores(scores: Dict[str, int]):
    """Save best scores to the JSON file specified in config."""
    try:
        with open(config.BEST_SCORES_FILE, 'w') as f:
            json.dump(scores, f, indent=4) # Use indent for readability
    except IOError as e:
        logger.error(f"Error writing best scores to '{config.BEST_SCORES_FILE}': {e}")
    except Exception as e:
        logger.error(f"Unexpected error saving best scores: {e}")

def get_best_score_key(difficulty: str, category_id: int, game_length: int) -> str:
    """Generate a unique key for best score tracking based on game parameters."""
    return f"{difficulty}|{category_id}|{game_length}"
