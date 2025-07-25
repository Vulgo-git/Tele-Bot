import sqlite3
from datetime import datetime, timedelta
from typing import Optional

def criar_acesso(user_id: int):
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    expiracao = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT OR REPLACE INTO acessos (user_id, expiracao)
        VALUES (?, ?)
    """, (user_id, expiracao))
    
    conn.commit()
    conn.close()

def verificar_acesso(user_id: int) -> bool:
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT expiracao FROM acessos 
        WHERE user_id = ? AND expiracao > datetime('now')
    """, (user_id,))
    
    acesso = cursor.fetchone()
    conn.close()
    return bool(acesso)  # Retorna True se encontrou acesso