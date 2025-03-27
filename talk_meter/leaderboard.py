from database import DatabaseManager
from config import MILESTONES

class LeaderboardManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def process_message(self, user_id, username):
        """Process a new message and check for milestones."""
        # Log message
        self.db_manager.log_message(user_id, username)
        
        # Check milestones
        total_messages = self.db_manager.get_user_stats(user_id)[0]

        milestone_reached = [
            milestone for milestone in MILESTONES 
            if total_messages == milestone
        ]
        
        return milestone_reached

    def get_leaderboard_message(self, period='all-time', user_id=None):
        """Generate leaderboard message."""
        # Get leaderboard
        leaderboard = self.db_manager.get_leaderboard(period)
        print("leaderaboard",leaderboard)
        
        # Prepare message
        message_lines = [f"🏆 {period.capitalize()} Leaderboard:"]
        
        for idx, (uid, username, count) in enumerate(leaderboard, 1):
            message_lines.append(f"{idx}. [{username}](tg://user?id={uid}): {count} messages")

            
        
        # Add user's rank if provided
        if user_id is not None:
            user_rank = self.db_manager.get_user_rank(user_id, period)
            if user_rank:
                message_lines.append(f"\nYour Rank: {user_rank}")
        
        return "\n".join(message_lines)

    def get_user_stats(self, user_id):
        """Generate comprehensive user stats."""
        # Get total messages and highest rank
        total_messages, highest_rank = self.db_manager.get_user_stats(user_id)
        
        # Get ranks for different periods
        ranks = {
            "Daily": self.db_manager.get_user_rank(user_id, 'day'),
            "Weekly": self.db_manager.get_user_rank(user_id, 'week'),
            "Monthly": self.db_manager.get_user_rank(user_id, 'month'),
            "All-Time": self.db_manager.get_user_rank(user_id, 'all_time')
        }
        
        # Prepare stats message
        stats_message = [
            "🌟 Your Stats:",
            f"Total Messages: {total_messages}",
            f"Highest Rank Achieved: {highest_rank or 'N/A'}",
            "\nCurrent Rankings:"
        ]
        
        for period, rank in ranks.items():
            stats_message.append(f"{period} Rank: {rank or 'Not Ranked'}")
        
        return "\n".join(stats_message)
