# Telegram Karma Bot

## Overview

This Telegram bot implements a gamification ranking system through a karma/reputation points mechanism. Users earn points when others thank them for help, creating an incentive for community contribution.

## Key Features

- Karma point system for helpful users
- Track user rankings
- Daily leaderboard announcements
- Points awarded for common "thank" words and appreciation emojis
- Flexible configuration of karma settings

## How It Works

- Users gain karma points when someone replies to their message with appreciation words
- Each appreciation increases the user's karma by a configurable amount
- Daily limit prevents karma point farming
- Users can check their rank and view the leaderboard
- The bot prevents self-karma points

## Prerequisites

- Python 3.8+
- Telegram account
- Telegram Bot Token
- SQLite3

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/agsafronenko/telegram-bots.git
cd telegram-bots/karma_bot
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

## Getting a Telegram Bot Token

1. Open Telegram and search for the `BotFather`
2. Start a chat and send `/newbot`
3. Follow the prompts to name your bot
4. BotFather will provide you with a token

## Configuration

1. Create a `.env` file in the project root
2. Add your Telegram Bot Token:

```
BOT_TOKEN=your_telegram_bot_token_here
```

### Customizing Karma Settings

Edit `config.py` to modify:

- `REPUTATION_GAIN`: Points awarded per appreciation (default: 1)
- `MAX_DAILY_REPUTATION_GAIN`: Maximum daily karma points per user (default: 5)
- `DAILY_TOP_10_TIME`: Time for daily leaderboard announcement (default: '21:00')
- `REPUTATION_WORDS`: List of most popular "thank" words and emojis

#### Example Configuration

```python
# Adjust karma gain settings
REPUTATION_GAIN = 2  # Increase points per appreciation
MAX_DAILY_REPUTATION_GAIN = 10  # Allow more daily points
```

## Running the Bot

```bash
python3 bot.py
```

## Bot Commands

- `/start`: Initialize the bot and welcome message
- `/ranks` or `/ranking` and similar derived words: Show all-time top 10 users
- `/myrank`: Check your personal ranking and karma points

## Supported Appreciation Words

The bot recognizes most popular "thank" words and emojis, including:
- "thank you", "thanks", "thx", "ty", etc
- Appreciation emojis like 👍, ❤️, 🙏, 💯

## Deployment Considerations

- Use a server or cloud platform for 24/7 operation
- Ensure consistent timezone settings for daily announcements

## Security Notes

- Keep your bot token secret
- Use environment variables
