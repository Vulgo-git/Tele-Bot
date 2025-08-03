import sqlite3
from datetime import datetime, timedelta
import threading
import os
import logging

logger = logging.getLogger(__name__)

# Thread-local storage para conexões SQLite
local = threading.local()

class Database:
    def __init__(self, db_path=None):
        # Define caminho do banco de dados
        self.db_path = db_path or os.getenv('SQLITE_PATH', 'acessos.db')
        
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Cria tabela inicial
        self._create_table()
    
    def _get_connection(self):
        """Obtém uma conexão SQLite exclusiva para a thread atual"""
        if not hasattr(local, "connection") or local.connection is None:
            logger.info(f"Criando nova conexão SQLite para thread {threading.get_ident()}")
            local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False  # Permite acesso multi-thread
            )
            local.connection.row_factory = sqlite3.Row
        return local.connection
    
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
            logger.info("Tabela 'acessos' criada/verificada")
    
    def grant_access(self, user_id: int, days: int = 5):
        expiry = datetime.now() + timedelta(days=days)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO acessos (user_id, expiry)
            VALUES (?, ?)
            ''', (user_id, expiry.isoformat()))
            conn.commit()
        logger.info(f"Acesso concedido para user_id: {user_id} até {expiry}")
        return expiry
    
    def has_access(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT expiry FROM acessos WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                logger.info(f"Usuário {user_id} sem acesso registrado")
                return False
            
            expiry = datetime.fromisoformat(row['expiry'])
            has_access = expiry > datetime.now()
            
            # Limpeza automática de acessos expirados
            if not has_access:
                self._clean_expired_access(user_id)
            
            return has_access
    
    def _clean_expired_access(self, user_id: int):
        """Remove acesso expirado do banco de dados"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM acessos WHERE user_id = ?', (user_id,))
            conn.commit()
            logger.info(f"Removido acesso expirado para user_id: {user_id}")
    
    def close_connection(self):
        """Fecha a conexão da thread atual"""
        if hasattr(local, "connection") and local.connection:
            local.connection.close()
            local.connection = None
            logger.info(f"Conexão SQLite fechada para thread {threading.get_ident()}")