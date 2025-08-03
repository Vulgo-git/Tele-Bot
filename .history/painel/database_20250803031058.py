import sqlite3
from datetime import datetime, timedelta
import threading

# Usando thread-local storage para conexões
local = threading.local()

class Database:
    def __init__(self, db_path='acessos.db'):
        self.db_path = db_path
        self._create_table()
    
    def _create_table(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS acessos (
                user_id INTEGER PRIMARY KEY,
                expiry DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
    
    def _get_connection(self):
        if not hasattr(local, "connection") or local.connection is None:
            local.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False
            )
        return local.connection
    
    def grant_access(self, user_id: int, days: int = 5):
        expiry = datetime.now() + timedelta(days=days)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO acessos (user_id, expiry)
            VALUES (?, ?)
            ''', (user_id, expiry.isoformat()))
            conn.commit()
        return expiry
    
    def has_access(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT expiry FROM acessos WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return False
            return datetime.fromisoformat(row[0]) > datetime.now()
    
    def close(self):
        if hasattr(local, "connection") and local.connection:
            local.connection.close()
            local.connection = None# (Opcional) Conexão DB
