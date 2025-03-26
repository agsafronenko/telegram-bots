import sqlite3
from datetime import datetime, timedelta

class ReputationDatabase:
    def __init__(self, db_name='reputation.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                reputation INTEGER DEFAULT 0,
                last_reputation_update TEXT
            )
        ''')
        
        # Add a new table for tracking active chats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_chats (
                chat_id INTEGER PRIMARY KEY,
                last_active TEXT
            )
        ''')
        
        self.conn.commit()

    def add_active_chat(self, chat_id):
        """Add or update an active chat"""
        cursor = self.conn.cursor()
        today = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO active_chats (chat_id, last_active) 
            VALUES (?, ?)
        ''', (chat_id, today))
        
        self.conn.commit()

    def get_active_chats(self):
        """Retrieve all active chat IDs"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT chat_id FROM active_chats')
        return [chat[0] for chat in cursor.fetchall()]

    def update_reputation(self, user_id, first_name, username, points):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        # Check if user exists
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            # Update existing user
            cursor.execute('''
                UPDATE users 
                SET reputation = reputation + ?, 
                    first_name = ?,
                    username = ?,
                    last_reputation_update = ? 
                WHERE user_id = ?
            ''', (points, first_name, username, now, user_id))
        else:
            # Insert new user
            cursor.execute('''
                INSERT INTO users (user_id, first_name, username, reputation, last_reputation_update) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, first_name, username, points, now))
        
        self.conn.commit()

    def get_top_users(self, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, first_name, username, reputation 
            FROM users 
            ORDER BY reputation DESC, 
                     last_reputation_update ASC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()

    def get_user_rank(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            WITH user_to_rank AS (
                SELECT 
                    user_id, 
                    reputation, 
                    last_reputation_update,
                    (
                        SELECT COUNT(*) + 1 
                        FROM users u2 
                        WHERE (u2.reputation > users.reputation) OR 
                            (u2.reputation = users.reputation AND 
                            u2.last_reputation_update < users.last_reputation_update)
                    ) as calculated_rank
                FROM users
                WHERE user_id = ?
            )
            SELECT calculated_rank, reputation 
            FROM user_to_rank
        ''', (user_id,))
        return cursor.fetchone()

    def close(self):
        self.conn.close()