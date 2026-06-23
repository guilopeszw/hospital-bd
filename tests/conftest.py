import pytest
import psycopg2
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "dbname=hospital_db user=postgres password=password host=localhost port=5433"
)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Roda uma vez por sessão calculando caminhos absolutos corretos e criando o schema."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    ddl_files = [
        "sql/ddl/01_enums.sql",
        "sql/ddl/02_pessoa.sql",
        "sql/ddl/03_paciente.sql",
        "sql/ddl/04_profissional.sql",
        "sql/ddl/05_preceptor.sql",
        "sql/ddl/06_residente.sql"
    ]
    
    try:
        for file_name in ddl_files:
            file_path = os.path.join(base_dir, file_name)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Script DDL crucial não encontrado no caminho: {file_path}")
                
            with open(file_path, "r", encoding="utf-8") as f:
                cursor.execute(f.read())
                
        conn.commit()
    except Exception as e:
        conn.rollback()
        pytest.fail(f"Falha crítica na automação do Schema DDL: {e}")
    finally:
        cursor.close()
        conn.close()

@pytest.fixture(scope="session")
def db_connection():
    """Cria uma conexão única com o banco para a sessão de testes."""
    conn = psycopg2.connect(DATABASE_URL)
    yield conn
    conn.close()

@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """Cria um cursor para cada teste e isola as transações com ROLLBACK."""
    cursor = db_connection.cursor()
    yield cursor
    db_connection.rollback()
    cursor.close()