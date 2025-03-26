# Telegram Verification Bot

## Overview

This is a customizable Telegram bot designed to verify new members joining a chat group. In its basic implementation, the bot challenges new members with programming-related questions, but it can be easily adapted to different themes or verification methods.

## Key Features

- Automatic verification of new chat members
- Customizable verification questions
- Temporary message restrictions
- Automatic banning for failed verifications
- Flexible configuration

## Customization

The bot is highly adaptable. While the default configuration focuses on programming questions, you can easily modify `config.py` to:

- Change verification questions
- Adjust timeout durations
- Customize welcome and failure messages
- Create verification challenges for any theme (e.g., trivia, language skills, community-specific knowledge)

## Prerequisites

- Python 3.8+
- Telegram account
- Telegram Bot Token

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/agsafronenko/telegram-bots.git
cd telegram-bots/dev_gatekeeper_bot
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
DEV_GATEKEEPER_BOT=your_telegram_bot_token_here
```

## Customizing Verification Questions

Edit `src/config.py` to modify:

- `CODING_QUESTIONS`: Replace with your own questions
- `TIMEOUT_SECONDS`: Adjust verification time
- Message generation functions

### Example of Customization

```python
# Change from programming to movie trivia
CODING_QUESTIONS = [
    {
        "question": "Who directed the movie Inception?",
        "answer": "Christopher Nolan"
    },
    # Add more movie trivia questions
]
```

## Running the Bot

Run this command from the project's root directory:

```bash
python3 -m src.main
```

## Deployment Considerations

- Use a server or cloud platform for 24/7 operation

## Security Notes

- Keep your bot token secret
- Use environment variables
