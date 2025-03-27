# Database Configuration
DATABASE_PATH = "leaderboard.db"

# Leaderboard Settings
MILESTONES = [65, 70, 75]

# Anti-Spam Configuration
SPAM_THRESHOLD = {
    "messages": 5,  # Maximum number of messages
    "time_window": 10,  # Time window in seconds
}

# Leaderboard Periods
PERIODS = {
    "day": "day",
    "week": "week", 
    "month": "month",
    "alltime": "all_time"
}

# Notification Settings
MAX_NOTIFICATION_USERS = 1000  # Limit notifications to prevent excessive load
