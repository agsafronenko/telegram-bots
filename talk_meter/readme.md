# Telegram Leaderboard Bot

## Features
- Daily, Weekly, Monthly, and All-Time Leaderboards
- Personal Message Statistics
- Message Milestones
- Anti-Spam Detection
- Notification System

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set your Telegram Bot Token in `config.py`
4. Run the bot: `python main.py`

## Commands
- `/start` - Get bot overview
- `/rank` - All-time leaderboard
- `/dayrank` - Daily leaderboard
- `/weekrank` - Weekly leaderboard
- `/monthrank` - Monthly leaderboard
- `/mystats` - Your personal statistics
- `/notifyme` - Enable leaderboard notifications
- `/stopnotify` - Disable leaderboard notifications

## Configuration
Customize bot behavior in `config.py`:
- Bot Token
- Database Path
- Message Milestones
- Anti-Spam Thresholds

## Dependencies
- python-telegram-bot
- sqlite3
