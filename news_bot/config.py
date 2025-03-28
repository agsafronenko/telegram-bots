import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv('NEWS_BOT_TOKEN')
    
    # News API Configuration
    NEWS_API_TOKEN = os.getenv('NEWSAPI_TOKEN')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # News API Default Settings
    DEFAULT_COUNTRY = 'us'
    DEFAULT_CATEGORY = 'general'
    MAX_ARTICLES = 5
    
    # Configurable Categories and Countries
    NEWS_CATEGORIES = [
        ['General', 'Business'],
        ['Technology', 'Science'],
        ['Sports', 'Entertainment']
    ]
    
    NEWS_COUNTRIES = [
        ['US', 'GB', 'CA'],
        ['IN', 'AU', 'JP']
    ]