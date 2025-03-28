import re
from telegram import Update
from telegram.ext import ContextTypes
from news_service import NewsService
from keyboards import NewsKeyboards

def escape_markdown_v2(text):
    """
    Escape special characters for Markdown V2 formatting
    
    :param text: Input text to escape
    :return: Markdown V2 escaped text
    """
    if not text:
        return ''
    
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

class NewsHandlers:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command and provide bot introduction
        """
        welcome_text = (
            "Welcome to the News Bot\\! 📰\n\n"
            "Available commands:\n"
            "/news \\- Get top headlines\n"
            "/category \\- Choose news category\n"
            "/country \\- Select news country"
        )
        await update.message.reply_markdown_v2(welcome_text)
    
    @staticmethod
    async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Fetch and display top headlines with links
        """
        articles = NewsService.get_top_headlines()
        
        if not articles:
            await update.message.reply_text("Sorry, couldn't fetch news right now.")
            return
        
        news_text = "🌐 *Top Headlines:*\n\n"
        for article in articles:
            # Safely handle potential missing fields
            title = escape_markdown_v2(article.get('title', 'Untitled'))
            description = escape_markdown_v2(article.get('description', 'No description'))
            url = article.get('url', '')
            
            # Create a markdown link with the title if URL exists
            if url:
                news_text += f"📍 [*{title}*]({url})\n{description}\n\n"
            else:
                news_text += f"📍 *{title}*\n{description}\n\n"
        
        await update.message.reply_markdown_v2(news_text)
    
    @staticmethod
    async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show category selection keyboard
        """
        await update.message.reply_text(
            "Choose a news category:", 
            reply_markup=NewsKeyboards.get_category_keyboard()
        )
    
    @staticmethod
    async def choose_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show country selection keyboard
        """
        await update.message.reply_text(
            "Choose a country:", 
            reply_markup=NewsKeyboards.get_country_keyboard()
        )
    
    @staticmethod
    async def handle_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle category selection callback with article links
        """
        query = update.callback_query
        await query.answer()
        
        category = query.data
        articles = NewsService.get_top_headlines(category=category)
        
        news_text = f"📰 *Top {escape_markdown_v2(category.capitalize())} Headlines:*\n\n"
        for article in articles:
            # Safely handle potential missing fields
            title = escape_markdown_v2(article.get('title', 'Untitled'))
            description = escape_markdown_v2(article.get('description', 'No description'))
            url = article.get('url', '')
            
            # Create a markdown link with the title if URL exists
            if url:
                news_text += f"📍 [*{title}*]({url})\n{description}\n\n"
            else:
                news_text += f"📍 *{title}*\n{description}\n\n"
        
        await query.edit_message_text(news_text, parse_mode='MarkdownV2')
    
    @staticmethod
    async def handle_country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle country selection callback with article links
        """
        query = update.callback_query
        await query.answer()
        
        country = query.data
        articles = NewsService.get_top_headlines(country=country)
        
        news_text = f"📰 *Top {escape_markdown_v2(country.upper())} Headlines:*\n\n"
        for article in articles:
            # Safely handle potential missing fields
            title = escape_markdown_v2(article.get('title', 'Untitled'))
            description = escape_markdown_v2(article.get('description', 'No description'))
            url = article.get('url', '')
            
            # Create a markdown link with the title if URL exists
            if url:
                news_text += f"📍 [*{title}*]({url})\n{description}\n\n"
            else:
                news_text += f"📍 *{title}*\n{description}\n\n"
        
        
        await query.edit_message_text(news_text, parse_mode='MarkdownV2')