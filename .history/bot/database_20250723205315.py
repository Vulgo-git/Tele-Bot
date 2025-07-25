import sqlite3

def create_connection():
    return sqlite3.connect('dados.db')

def get_user_data(cpf):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE cpf = ?", (cpf,))
    return cursor.fetchone()