import asyncio
from database import DatabaseManager

class NotificationManager:
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager
        self.previous_leaderboards = {}

    async def check_leaderboard_changes(self, period='all_time'):
        """Check for leaderboard changes and send notifications."""
        # Get current leaderboard
        current_leaderboard = self.db_manager.get_leaderboard(period)
        
        # Compare with previous leaderboard
        if period not in self.previous_leaderboards:
            self.previous_leaderboards[period] = current_leaderboard
            return
        
        # Check for changes
        changes = self._detect_leaderboard_changes(
            self.previous_leaderboards[period], 
            current_leaderboard
        )
        
        # Send notifications
        if changes:
            await self._send_notifications(changes, period)
        
        # Update previous leaderboard
        self.previous_leaderboards[period] = current_leaderboard

    def _detect_leaderboard_changes(self, old_leaderboard, new_leaderboard):
        """Detect changes in leaderboard."""
        changes = []
        
        for new_idx, (new_uid, new_username, new_count) in enumerate(new_leaderboard):
            # Check if user is new in top positions
            if new_idx < len(old_leaderboard):
                old_uid, _, old_count = old_leaderboard[new_idx]
                
                # Different user or significant message count change
                if old_uid != new_uid or abs(new_count - old_count) > 10:
                    changes.append({
                        'user_id': new_uid,
                        'username': new_username,
                        'new_rank': new_idx + 1,
                        'message_count': new_count
                    })
        
        return changes

    async def _send_notifications(self, changes, period):
        """Send notifications to subscribed users."""
        notification_users = self.db_manager.get_notification_users()
        
        notification_text = f"🔔 Leaderboard Update ({period.capitalize()}):\n"
        
        for change in changes:
            notification_text += (
                f"{change['username']} is now ranked #{change['new_rank']} "
                f"with {change['message_count']} messages!\n"
            )
        
        # Send notifications
        for user_id in notification_users:
            try:
                await self.bot.send_message(
                    chat_id=user_id, 
                    text=notification_text
                )
            except Exception as e:
                print(f"Failed to send notification to {user_id}: {e}")
