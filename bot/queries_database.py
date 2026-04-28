import sqlite3
from datetime import datetime, timedelta
import threading
import os
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# Thread-local storage para conexões SQLite
local = threading.local()


class QueriesDatabase:
    """
    Banco de dados para armazenar dados pessoais e histórico de consultas.
    Estrutura de dados:
    - people: Tabela com dados pessoais
    - queries_log: Histórico de consultas de usuários
    """

    def __init__(self, db_path=None):
        """Inicializa o banco de dados de consultas"""
        self.db_path = db_path or os.getenv('QUERIES_DB_PATH', 'data/pessoas.db')
        
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        
        # Cria tabelas
        self._create_tables()
        logger.info(f"✅ Banco de dados de consultas inicializado: {self.db_path}")
    
    def _get_connection(self):
        """Obtém uma conexão SQLite exclusiva para a thread atual"""
        if not hasattr(local, "connection") or local.connection is None:
            logger.debug(f"Criando nova conexão SQLite para thread {threading.get_ident()}")
            local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            local.connection.row_factory = sqlite3.Row
        return local.connection
    
    def _create_tables(self):
        """Cria as tabelas necessárias"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de pessoas com dados pessoais
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpf TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                birth_date TEXT,
                mother_name TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zipcode TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Tabela de histórico de consultas
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query_type TEXT NOT NULL,
                query_value TEXT NOT NULL,
                result_found BOOLEAN DEFAULT 0,
                person_id INTEGER,
                queried_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES people(id)
            )
            ''')
            
            # Criar índices para melhor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cpf ON people(cpf)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_phone ON people(phone)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON people(full_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_queries ON queries_log(user_id)')
            
            conn.commit()
            logger.info("✅ Tabelas criadas/verificadas com sucesso")
    
    # ===== OPERAÇÕES DE PESSOAS =====
    
    def add_person(self, cpf: str, full_name: str, phone: str = None, 
                   email: str = None, birth_date: str = None, 
                   mother_name: str = None, address: str = None,
                   city: str = None, state: str = None, zipcode: str = None) -> bool:
        """
        Adiciona uma pessoa ao banco de dados
        Retorna True se sucesso, False se CPF já existe
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO people 
                (cpf, full_name, phone, email, birth_date, mother_name, 
                 address, city, state, zipcode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (cpf, full_name, phone, email, birth_date, mother_name,
                      address, city, state, zipcode))
                conn.commit()
                logger.info(f"✅ Pessoa adicionada: {full_name} ({cpf})")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ CPF duplicado: {cpf}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar pessoa: {e}")
            return False
    
    def search_by_cpf(self, cpf: str) -> Optional[Dict]:
        """Busca uma pessoa pelo CPF"""
        try:
            # Limpar CPF (remover caracteres especiais)
            clean_cpf = ''.join(filter(str.isdigit, cpf))
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM people WHERE cpf = ?', (clean_cpf,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar CPF: {e}")
            return None
    
    def search_by_phone(self, phone: str) -> Optional[Dict]:
        """Busca uma pessoa pelo telefone"""
        try:
            # Limpar telefone (remover caracteres especiais)
            clean_phone = ''.join(filter(str.isdigit, phone))
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM people WHERE phone LIKE ?', 
                             (f'%{clean_phone}%',))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar telefone: {e}")
            return None
    
    def search_by_name(self, name: str) -> List[Dict]:
        """Busca pessoas pelo nome (suporta busca parcial)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM people WHERE full_name LIKE ? LIMIT 10', 
                             (f'%{name}%',))
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Erro ao buscar por nome: {e}")
            return []
    
    def search_by_email(self, email: str) -> Optional[Dict]:
        """Busca uma pessoa pelo email"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM people WHERE email = ?', (email,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar email: {e}")
            return None
    
    def update_person(self, cpf: str, **kwargs) -> bool:
        """Atualiza dados de uma pessoa"""
        try:
            clean_cpf = ''.join(filter(str.isdigit, cpf))
            
            # Construir query dinamicamente
            allowed_fields = ['full_name', 'phone', 'email', 'birth_date', 
                            'mother_name', 'address', 'city', 'state', 'zipcode']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not updates:
                return False
            
            set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
            values = list(updates.values()) + [clean_cpf]
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'UPDATE people SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE cpf = ?', values)
                conn.commit()
                logger.info(f"✅ Pessoa atualizada: {cpf}")
                return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar pessoa: {e}")
            return False
    
    def delete_person(self, cpf: str) -> bool:
        """Deleta uma pessoa do banco de dados"""
        try:
            clean_cpf = ''.join(filter(str.isdigit, cpf))
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM people WHERE cpf = ?', (clean_cpf,))
                conn.commit()
                logger.info(f"✅ Pessoa deletada: {cpf}")
                return True
        except Exception as e:
            logger.error(f"❌ Erro ao deletar pessoa: {e}")
            return False
    
    # ===== OPERAÇÕES DE LOG DE CONSULTAS =====
    
    def log_query(self, user_id: int, query_type: str, query_value: str, 
                  result_found: bool = False, person_id: int = None) -> bool:
        """Registra uma consulta no histórico"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO queries_log 
                (user_id, query_type, query_value, result_found, person_id)
                VALUES (?, ?, ?, ?, ?)
                ''', (user_id, query_type, query_value, result_found, person_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Erro ao registrar consulta: {e}")
            return False
    
    def get_user_queries(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Retorna histórico de consultas de um usuário"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM queries_log 
                WHERE user_id = ? 
                ORDER BY queried_at DESC 
                LIMIT ?
                ''', (user_id, limit))
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Erro ao obter histórico: {e}")
            return []
    
    def get_query_count(self, user_id: int, hours: int = 24) -> int:
        """Retorna quantidade de consultas do usuário nas últimas X horas"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                cursor.execute('''
                SELECT COUNT(*) as count FROM queries_log 
                WHERE user_id = ? AND queried_at > ?
                ''', (user_id, cutoff_time.isoformat()))
                
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"❌ Erro ao contar consultas: {e}")
            return 0
    
    # ===== OPERAÇÕES ADMINISTRATIVAS =====
    
    def get_total_people(self) -> int:
        """Retorna total de pessoas no banco"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM people')
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"❌ Erro ao contar pessoas: {e}")
            return 0
    
    def get_total_queries(self) -> int:
        """Retorna total de consultas realizadas"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM queries_log')
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"❌ Erro ao contar consultas: {e}")
            return 0
    
    def export_people(self, limit: int = None) -> List[Dict]:
        """Exporta dados de pessoas"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if limit:
                    cursor.execute('SELECT * FROM people LIMIT ?', (limit,))
                else:
                    cursor.execute('SELECT * FROM people')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Erro ao exportar pessoas: {e}")
            return []
    
    def close_connection(self):
        """Fecha a conexão da thread atual"""
        if hasattr(local, "connection") and local.connection:
            local.connection.close()
            local.connection = None
            logger.info(f"✅ Conexão SQLite fechada para thread {threading.get_ident()}")
