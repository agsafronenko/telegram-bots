from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class NewsKeyboards:
    @staticmethod
    def get_category_keyboard():
        """
        Create an inline keyboard for news categories
        """
        categories = [
            ['General', 'Business'],
            ['Technology', 'Science'],
            ['Sports', 'Entertainment']
        ]
        
        keyboard = [
            [InlineKeyboardButton(cat, callback_data=cat.lower()) for cat in row]
            for row in categories
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_country_keyboard():
        """
        Create an inline keyboard for country selection
        """
        countries = [
            ['US', 'GB', 'CA'],
            ['IN', 'AU', 'JP']
        ]
        
        keyboard = [
            [InlineKeyboardButton(country, callback_data=country.lower()) for country in row]
            for row in countries
        ]
        
        return InlineKeyboardMarkup(keyboard)
