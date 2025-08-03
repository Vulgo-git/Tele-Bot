import sqlite3
from datetime import datetime, timedelta
import os
import logging
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database')

# Obter caminho absoluto para o banco de dados
def get_db_path():
    if os.getenv('RAILWAY_ENVIRONMENT'):
        return '/data/dados.db'
    return 'dados.db'

def criar_tabela():
    db_path = get_db_path()
    dir_path = os.path.dirname(db_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acessos (
                user_id INTEGER PRIMARY KEY,
                expiracao DATETIME NOT NULL,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expiracao 
            ON acessos (expiracao)
        """)
        
        conn.commit()
        logger.info("Tabela 'acessos' verificada/criada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabela: {e}")
    finally:
        if conn:
            conn.close()

criar_tabela()

def criar_acesso(user_id: int):
    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        expiracao = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT OR REPLACE INTO acessos (user_id, expiracao)
            VALUES (?, ?)
        """, (user_id, expiracao))
        
        conn.commit()
        logger.info(f"Acesso criado/atualizado para user_id: {user_id} até {expiracao}")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar acesso para {user_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verificar_acesso(user_id: int) -> bool:
    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT expiracao FROM acessos 
            WHERE user_id = ? AND expiracao > datetime('now')
        """, (user_id,))
        
        acesso = cursor.fetchone()
        return bool(acesso)
    except Exception as e:
        logger.error(f"Erro ao verificar acesso para {user_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def limpar_acessos_expirados():
    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM acessos 
            WHERE expiracao <= datetime('now')
        """)
        
        count = cursor.rowcount
        conn.commit()
        logger.info(f"{count} acessos expirados removidos")
        return count
    except Exception as e:
        logger.error(f"Erro ao limpar acessos expirados: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def tempo_restante(user_id: int) -> Optional[timedelta]:
    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT expiracao FROM acessos 
            WHERE user_id = ? AND expiracao > datetime('now')
        """, (user_id,))
        
        acesso = cursor.fetchone()
        if acesso:
            expiracao = datetime.strptime(acesso[0], "%Y-%m-%d %H:%M:%S")
            return expiracao - datetime.now()
        return None
    except Exception as e:
        logger.error(f"Erro ao obter tempo restante para {user_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()
