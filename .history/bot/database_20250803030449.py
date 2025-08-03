import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path='acessos.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_table()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS acessos (
            user_id INTEGER PRIMARY KEY,
            expiry DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()
    
    def grant_access(self, user_id: int, days: int = 5):
        expiry = datetime.now() + timedelta(days=days)
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO acessos (user_id, expiry)
        VALUES (?, ?)
        ''', (user_id, expiry))
        self.conn.commit()
        return expiry
    
    def has_access(self, user_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT expiry FROM acessos WHERE user_id = ?
        ''', (user_id,))
        row = cursor.fetchone()
        if not row:
            return False
        return datetime.fromisoformat(row[0]) > datetime.now()
    
    def get_expiry(self, user_id: int) -> datetime | None:
        cursor = self.conn.cursor()
        cursor.execute('SELECT expiry FROM acessos WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return datetime.fromisoformat(row[0]) if row else None
    
    def close(self):
        self.conn.close()