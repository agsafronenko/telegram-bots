import logging
from typing import List, Dict, Optional

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from news_service import NewsService
from keyboards import NewsKeyboards

def escape_markdown_v2(text: Optional[str]) -> str:
    """
    Escape special characters for Telegram Markdown V2 formatting.
    
    Args:
        text (str): Input text to escape
    
    Returns:
        str: Markdown V2 escaped text
    """
    if not text:
        return ''
    
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def format_articles(
    articles: List[Dict], 
    headline_prefix: str = '', 
    prefix_capitalized: bool = True
) -> str:
    """
    Format news articles into a Markdown V2 compatible text.
    
    Args:
        articles (List[Dict]): List of news articles
        headline_prefix (str, optional): Prefix for headline
        prefix_capitalized (bool, optional): Whether to capitalize prefix
    
    Returns:
        str: Formatted news text in Markdown V2
    """
    if not articles:
        return "No articles available."
    
    # Capitalize prefix if requested
    display_prefix = headline_prefix.capitalize() if prefix_capitalized else headline_prefix
    
    # Create headline
    news_text = f"📰 *{display_prefix}Headlines:*\n\n" if headline_prefix else "📰 *Headlines:*\n\n"
    
    for article in articles:
        title = escape_markdown_v2(article.get('title', 'Untitled'))
        description = escape_markdown_v2(article.get('description', 'No description'))
        url = article.get('url', '')
        
        # Create markdown link or plain text based on URL availability
        if url:
            news_text += f"📍 [*{title}*]({url})\n{description}\n\n"
        else:
            news_text += f"📍 *{title}*\n{description}\n\n"
    
    return news_text

class NewsHandlers:
    """Telegram bot handlers for news-related commands and interactions."""
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command and provide bot introduction.
        
        Args:
            update (Update): Incoming update from Telegram
            context (ContextTypes.DEFAULT_TYPE): Context for the update
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
    async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Fetch and display top headlines.
        
        Args:
            update (Update): Incoming update from Telegram
            context (ContextTypes.DEFAULT_TYPE): Context for the update
        """
        try:
            articles = NewsService.get_top_headlines()
            news_text = format_articles(articles)
            await update.message.reply_markdown_v2(news_text)
        except Exception as e:
            logging.error(f"Error fetching news: {e}")
            await update.message.reply_text("Sorry, couldn't fetch news right now.")
    
    @staticmethod
    async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Show category selection keyboard.
        
        Args:
            update (Update): Incoming update from Telegram
            context (ContextTypes.DEFAULT_TYPE): Context for the update
        """
        await update.message.reply_text(
            "Choose a news category:", 
            reply_markup=NewsKeyboards.get_category_keyboard()
        )
    
    @staticmethod
    async def choose_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Show country selection keyboard.
        
        Args:
            update (Update): Incoming update from Telegram
            context (ContextTypes.DEFAULT_TYPE): Context for the update
        """
        await update.message.reply_text(
            "Choose a country:", 
            reply_markup=NewsKeyboards.get_country_keyboard()
        )
    
    @classmethod
    async def _handle_news_callback(
        cls, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        fetch_method: str
    ) -> None:
        """
        Generic handler for news callbacks (category or country).
        
        Args:
            update (Update): Incoming update from Telegram
            context (ContextTypes.DEFAULT_TYPE): Context for the update
            fetch_method (str): Method to fetch news ('category' or 'country')
        """
        query = update.callback_query
        await query.answer()
        
        try:
            # Dynamically fetch headlines based on method
            articles = NewsService.get_top_headlines(**{fetch_method: query.data})
            
            # Prepare headline prefix
            headline_prefix = query.data.upper() if fetch_method == 'country' else query.data.capitalize()
            news_text = format_articles(articles, headline_prefix)
            
            await query.edit_message_text(news_text, parse_mode='MarkdownV2')
        except Exception as e:
            logging.error(f"Error processing {fetch_method} callback: {e}")
            await query.edit_message_text(f"Error fetching {fetch_method} news. This is likely due to using a free NewsAPI token (for developers) instead of a production API token.")

    
    @classmethod
    async def handle_category_callback(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle category selection callback."""
        await cls._handle_news_callback(update, context, 'category')
    
    @classmethod
    async def handle_country_callback(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle country selection callback."""
        await cls._handle_news_callback(update, context, 'country')