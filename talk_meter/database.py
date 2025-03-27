import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str):
        """
        Initialize the database manager with logging and error handling.
        
        :param db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure database is set up
        try:
            self._create_tables()
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """
        Create and return a new database connection.
        
        :return: SQLite database connection
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"Connection creation failed: {e}")
            raise

    def _create_tables(self) -> None:
        """
        Create necessary database tables if they don't exist.
        Uses a comprehensive schema with additional constraints.
        """
        create_queries = [
            '''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                total_messages INTEGER DEFAULT 0,
                highest_rank INTEGER DEFAULT 0,
                last_message_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                first_message_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS notifications (
                user_id INTEGER PRIMARY KEY,
                is_subscribed INTEGER DEFAULT 1 CHECK(is_subscribed IN (0, 1)),
                subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE INDEX IF NOT EXISTS idx_messages_user_timestamp 
            ON messages(user_id, timestamp)'''
        ]
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for query in create_queries:
                    cursor.execute(query)
                conn.commit()
            self.logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating tables: {e}")
            raise

    def log_message(self, user_id: int, username: str) -> None:
        """
        Log a message for a user, updating user statistics.
        
        :param user_id: Telegram user ID
        :param username: Telegram username
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Upsert user 
                cursor.execute('''
                    INSERT INTO users (
                        user_id, 
                        username, 
                        total_messages, 
                        last_message_time
                    ) VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET 
                        total_messages = total_messages + 1,
                        last_message_time = CURRENT_TIMESTAMP
                ''', (user_id, username or str(user_id)))
                
                # Log message
                cursor.execute(
                    'INSERT INTO messages (user_id) VALUES (?)', 
                    (user_id,)
                )
                
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error logging message for user {user_id}: {e}")

    def get_user_stats(self, user_id: int) -> Tuple[int, int]:
        """
        Retrieve user's total messages and highest rank.
        
        :param user_id: Telegram user ID
        :return: Tuple of (total_messages, highest_rank)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT total_messages, highest_rank 
                    FROM users 
                    WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                return (result['total_messages'], result['highest_rank']) if result else (0, 0)
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving user stats for {user_id}: {e}")
            return (0, 0)

    def get_leaderboard(self, period: str = 'all_time', limit: int = 10) -> List[Tuple[int, str, int]]:
        """
        Generate leaderboard with strict first-to-count priority.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Period filtering
                period_filters = {
                    'daily': 'AND m.timestamp >= date("now", "-1 day")',
                    'weekly': 'AND m.timestamp >= date("now", "-7 days")',
                    'monthly': 'AND m.timestamp >= date("now", "-1 month")',
                    'all_time': ''
                }
                
                query = f'''
                    WITH user_messages AS (
                        SELECT 
                            u.user_id, 
                            u.username, 
                            COUNT(m.id) as message_count,
                            MAX(m.timestamp) as last_count_time,  -- Changed to last message timestamp
                            ROW_NUMBER() OVER (
                                PARTITION BY COUNT(m.id) 
                                ORDER BY MAX(m.timestamp) ASC  -- Order by earliest timestamp to reach count
                            ) as message_count_order
                        FROM users u
                        JOIN messages m ON u.user_id = m.user_id
                        WHERE 1=1 {period_filters.get(period, '')}
                        GROUP BY u.user_id, u.username
                    )
                    SELECT 
                        user_id, 
                        username, 
                        message_count
                    FROM user_messages
                    ORDER BY 
                        message_count DESC, 
                        last_count_time ASC  -- Tiebreaker: who reached the count first
                    LIMIT ?
                '''
                
                cursor.execute(query, (limit,))
                return [
                    (row['user_id'], row['username'], row['message_count']) 
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            self.logger.error(f"Error generating leaderboard for {period}: {e}")
            return []

    def get_user_rank(self, user_id: int, period: str = 'all_time') -> Optional[int]:
        """
        Get user's rank with first-to-count mechanism.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Period filtering
                period_filters = {
                    'daily': 'AND m.timestamp >= date("now", "-1 day")',
                    'weekly': 'AND m.timestamp >= date("now", "-7 days")',
                    'monthly': 'AND m.timestamp >= date("now", "-1 month")',
                    'all_time': ''
                }
                
                query = f'''
                    WITH user_messages AS (
                        SELECT 
                            u.user_id, 
                            u.username,
                            COUNT(m.id) as message_count,
                            MIN(m.timestamp) as first_message_time,
                            ROW_NUMBER() OVER (
                                PARTITION BY COUNT(m.id) 
                                ORDER BY MIN(m.timestamp)
                            ) as message_count_order
                        FROM users u
                        LEFT JOIN messages m ON u.user_id = m.user_id
                        WHERE 1=1 {period_filters.get(period, '')}
                        GROUP BY u.user_id, u.username
                    ),
                    ranked_messages AS (
                        SELECT 
                            user_id, 
                            username,
                            message_count,
                            first_message_time,
                            COUNT(DISTINCT other.message_count) + 1 AS base_rank,
                            message_count_order
                        FROM user_messages
                        LEFT JOIN user_messages other ON other.message_count > user_messages.message_count
                        GROUP BY user_id, username, message_count, first_message_time, message_count_order
                    )
                    SELECT 
                        base_rank + (message_count_order - 1) AS final_rank
                    FROM ranked_messages 
                    WHERE user_id = ?
                '''
                
                cursor.execute(query, (user_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting user rank for {user_id} in {period}: {e}")
            return None

    def toggle_notifications(self, user_id: int, subscribe: bool = True) -> None:
        """
        Toggle notification subscription for a user.
        
        :param user_id: Telegram user ID
        :param subscribe: True to subscribe, False to unsubscribe
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO notifications 
                    (user_id, is_subscribed)
                    VALUES (?, ?)
                ''', (user_id, 1 if subscribe else 0))
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error toggling notifications for {user_id}: {e}")

    def get_notification_users(self, limit: int = 1000) -> List[int]:
        """
        Retrieve users subscribed to notifications.
        
        :param limit: Maximum number of users to return
        :return: List of user IDs
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id 
                    FROM notifications 
                    WHERE is_subscribed = 1 
                    LIMIT ?
                ''', (limit,))
                return [row['user_id'] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving notification users: {e}")
            return []

    def cleanup_old_messages(self, days: int = 90) -> None:
        """
        Remove messages older than specified number of days.
        
        :param days: Number of days to retain messages
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM messages 
                    WHERE timestamp < date('now', ?)
                ''', (f'-{days} days',))
                conn.commit()
                self.logger.info(f"Cleaned up messages older than {days} days")
        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning up old messages: {e}")