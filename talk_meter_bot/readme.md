# Talk Meter Telegram Bot

## Overview

Talk Meter is a Telegram bot that tracks and gamifies group chat messaging activity. It provides real-time leaderboards, message milestones, and personalized statistics to encourage active participation in group chats.

## Key Features

- Real-time message tracking
- Multiple leaderboard periods (Daily, Weekly, Monthly, All-Time)
- User message milestones
- Personal statistics tracking
- Anti-spam protection
- Optional leaderboard update notifications

## Tracking Mechanics

- Tracks total messages sent by each user
- Calculates rankings with a first-to-count priority mechanism
- Supports multiple time-based leaderboards
- Celebrates user messaging milestones

## Prerequisites

- Python 3.8+
- Telegram account
- Telegram Bot Token
- SQLite database support

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/agsafronenko/telegram-bots.git
cd telegram-bots/talk_meter_bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install python-telegram-bot python-dotenv
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
TALK_METER=your_telegram_bot_token_here
```

### Customizable Settings in `config.py`

- `DATABASE_PATH`: Specify the SQLite database file location
- `MILESTONES`: Define message count milestones for celebrations
  - Current: `[1000, 5000, 10000]`
  - Customize to match your group's activity level
- `SPAM_THRESHOLD`: Control anti-spam behavior
  - `messages`: Maximum messages allowed
  - `time_window`: Time window for message count (in seconds)
  - Current: 5 messages in 10 seconds
- `MAX_NOTIFICATION_USERS`: Limit notifications to prevent system load
- `NOTIFICATION_INTERVAL`: Frequency of leaderboard checks (in seconds)
  - Current: 1 hour (3600 seconds)

## Bot Commands

- `/start`: Get bot introduction and command list
- `/rank`: All-time leaderboard
- `/dailyrank`: Today's leaderboard
- `/weeklyrank`: Weekly leaderboard
- `/monthlyrank`: Monthly leaderboard
- `/mystats`: Personal messaging statistics
- `/notifyme`: Enable leaderboard notifications
- `/stopnotify`: Disable leaderboard notifications

## Running the Bot

```bash
python3 bot.py
```

## Deployment Considerations

- Use a server or cloud platform for 24/7 operation
- Monitor database size and use periodic message cleanup

## Database Management

- SQLite database stores user messages and statistics
- Supports scaling to multiple group chats

## Security and Performance

- Implements anti-spam mechanisms
- Limits notification users to prevent excessive load
- Efficient database queries with indexing
