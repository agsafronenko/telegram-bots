# Telegram News Bot

## Overview

This is a Telegram bot that provides customizable news headlines from various categories and countries using the NewsAPI. Users can easily retrieve top news, filter by category, and select news from different countries through an interactive interface.

## Key Features

- Fetch top headlines from NewsAPI
- Select news by category (by default: General, Business, Technology, Science, Sports, Entertainment)
- Choose news from multiple countries (by default: US, UK, Canada, India, Australia, Japan)
- User-friendly inline keyboard for category and country selection
- Markdown V2 formatted news display
- Configurable news retrieval settings

## Prerequisites

- Python 3.8+
- Telegram account
- Telegram Bot Token
- NewsAPI Token

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/agsafronenko/telegram-news-bot.git
cd news_bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Getting Tokens

### Telegram Bot Token

1. Open Telegram and search for the `BotFather`
2. Start a chat and send `/newbot`
3. Follow the prompts to name your bot
4. BotFather will provide you with a token

### NewsAPI Token

1. Visit [NewsAPI](https://newsapi.org/)
2. Sign up
3. Navigate to your account dashboard
4. Copy your API key

## Configuration

1. Create a `.env` file in the project root
2. Add your tokens:

```
NEWS_BOT_TOKEN=your_telegram_bot_token_here
NEWSAPI_TOKEN=your_newsapi_token_here
LOG_LEVEL=INFO  # Optional: Adjust logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

## Customizing News Settings

Edit `config.py` to modify:

- `NEWS_CATEGORIES`: Add or change news categories
- `NEWS_COUNTRIES`: Update list of countries
- `MAX_ARTICLES`: Adjust number of articles retrieved
- `DEFAULT_COUNTRY`: Set default country for news

### Example Customization

```python
NEWS_CATEGORIES = [
    ['Technology', 'Science'],
    ['Health', 'Environment']
]

NEWS_COUNTRIES = [
    ['US', 'CA', 'GB'],
    ['AU', 'NZ', 'SG']
]
```

## Running the Bot

Run this command from the project's root directory:

```bash
python3 -m main
```

## Bot Commands

- `/start`: Show welcome message and available commands
- `/news`: Fetch top headlines
- `/category`: Select news category
- `/country`: Choose news country

## Deployment Considerations

- Use a server or cloud platform for 24/7 operation

## Security Notes

- Keep bot and API tokens secret
- Use environment variables
- Be mindful of NewsAPI usage limits
