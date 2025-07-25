import sqlite3

def create_connection():
    return sqlite3.connect('dados.db')

def get_user_data(cpf):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE cpf = ?", (cpf,))
    return cursor.fetchone()

def user_paid(cpf):
    user = get_user_data(cpf)
    if user is None:
        return False
    # Suponha que a 3ª coluna (índice 2) seja "pagamento_realizado"
    return user[2] == 1  # ou 'True', dependendo de como está salvo
