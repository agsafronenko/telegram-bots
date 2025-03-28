# Database Configuration
DATABASE_PATH = "leaderboard.db"

# Leaderboard Settings
MILESTONES = [1000, 5000, 10000]

# Anti-Spam Configuration
SPAM_THRESHOLD = {
    "messages": 5,  # Maximum number of messages
    "time_window": 10,  # Time window in seconds
}

# Leaderboard Periods
PERIODS = {
    "daily": "daily",
    "weekly": "weekly", 
    "monthly": "monthly",
    "alltime": "all_time"
}

# Notification Settings
MAX_NOTIFICATION_USERS = 1000  # Limit notifications to prevent excessive load
NOTIFICATION_INTERVAL = 60 * 60   # 1 hour in seconds




