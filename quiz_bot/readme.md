# Telegram Trivia Quiz Bot

## Overview

An advanced Telegram bot that offers customizable trivia quizzes across multiple difficulty levels, categories, and game lengths. Test your knowledge with this interactive quiz experience!

## Key Features

- Multiple difficulty levels (Easy, Medium, Hard)
- Wide range of trivia categories
- Configurable quiz length (10, 25, or 50 questions by default)
- Personal best score tracking
- 30-second timer for each question by default
- Real-time score updates
- Detailed end-of-game statistics

## Prerequisites

- Python 3.8+
- Telegram account
- Telegram Bot Token

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/agsafronenko/telegram-bots.git
cd telegram-bots/quiz_bot
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

## Getting Telegram Bot Token

1. Open Telegram and search for the `BotFather`
2. Start a chat and send `/newbot`
3. Follow the prompts to name your bot
4. BotFather will provide you with a token

## Configuration

1. Create a `.env` file in the project root
2. Add your Telegram bot token:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

## Running the Bot

Run this command from the project's root directory:

```bash
python3 main.py
```

## Bot Commands

- `/start_quiz`: Begin a new trivia quiz
  - Choose difficulty level
  - Select a category
  - Pick number of questions
- `/stop_quiz`: Immediately end your current quiz
- `/help`: Show help and instructions

## How to Play

1. Use `/start_quiz` to begin
2. Select quiz difficulty (Easy, Medium, Hard)
3. Choose a trivia category
4. Pick the number of questions
5. Answer questions within 30 seconds
6. Receive immediate feedback
7. Track your personal best scores

## Customization

Edit `config.py` to modify:

- `ANSWER_TIMEOUT`: Change question response time
- `DEFAULT_GAME_LENGTHS`: Adjust available quiz lengths

## Deployment Considerations

- Use a server or cloud platform for 24/7 operation
- Ensure stable internet connection
- Monitor API request limits

## API Used

- Open Trivia Database (https://opentdb.com/api_config.php)
