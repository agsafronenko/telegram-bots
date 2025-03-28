from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

class NewsKeyboards:
    @staticmethod
    def get_category_keyboard():
        """Create an inline keyboard for news categories"""
        keyboard = [
            [InlineKeyboardButton(cat, callback_data=cat.lower()) for cat in row]
            for row in Config.NEWS_CATEGORIES
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_country_keyboard():
        """Create an inline keyboard for country selection"""
        keyboard = [
            [InlineKeyboardButton(country, callback_data=country.lower()) for country in row]
            for row in Config.NEWS_COUNTRIES
        ]
        return InlineKeyboardMarkup(keyboard)