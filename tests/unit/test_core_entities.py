import pytest
from psycopg2 import errors

def test_inserir_pessoa_valida(db_cursor):
    """Garante que uma pessoa com dados válidos é inserida com sucesso."""
    db_cursor.execute("""
        INSERT INTO PESSOA (id_pessoa, nome, cpf, data_nascimento, is_flamengo, telefone)
        VALUES ('d1111111-1111-1111-1111-111111111111', 'Zico Teste', '99988877766', '1953-03-03', TRUE, '83999999999')
        RETURNING id_pessoa;
    """)
    id_gerado = db_cursor.fetchone()[0]
    assert id_gerado == 'd1111111-1111-1111-1111-111111111111'

def test_violacao_cpf_unico(db_cursor):
    """Garante que o banco barra a inserção de dois CPFs iguais (UNIQUE constraint)."""
    # Insere o primeiro
    db_cursor.execute("""
        INSERT INTO PESSOA (nome, cpf, data_nascimento) 
        VALUES ('Pessoa A', '12345678901', '1990-01-01');
    """)
    
    # Tenta inserir o segundo com o mesmo CPF e espera um erro específico do Postgres
    with pytest.raises(errors.UniqueViolation):
        db_cursor.execute("""
            INSERT INTO PESSOA (nome, cpf, data_nascimento) 
            VALUES ('Pessoa B', '12345678901', '1995-05-05');
        """)

def test_violacao_regex_cpf(db_cursor):
    """Garante que CPFs com tamanho bizarro ou letras sejam barrados (chk_cpf_formato)."""
    with pytest.raises(errors.CheckViolation):
        db_cursor.execute("""
            INSERT INTO PESSOA (nome, cpf, data_nascimento) 
            VALUES ('CPF Invalido', '12345ABC901', '1990-01-01');
        """)

def test_violacao_grupo_sanguineo_paciente(db_cursor):
    """Garante que o banco barra tipos sanguíneos falsos (chk_grupo_sanguineo_valido)."""
    # Primeiro criamos a pessoa base
    id_pessoa = 'd2222222-2222-2222-2222-222222222222'
    db_cursor.execute("""
        INSERT INTO PESSOA (id_pessoa, nome, cpf, data_nascimento) 
        VALUES (%s, 'Paciente Teste', '11122233399', '1990-01-01');
    """, (id_pessoa,))
    
    # Tenta criar o paciente com tipo sanguíneo inválido (XYZ)
    with pytest.raises(errors.CheckViolation):
        db_cursor.execute("""
            INSERT INTO PACIENTE (id_pessoa, num_convenio, grupo_sanguineo)
            VALUES (%s, 'CONV-123', 'XYZ');
        """, (id_pessoa,))

def test_default_is_flamengo(db_cursor):
    """Garante que o valor default de is_flamengo seja TRUE se omitido."""
    db_cursor.execute("""
        INSERT INTO PESSOA (nome, cpf, data_nascimento) 
        VALUES ('Manto Sagrado', '88877766655', '2000-01-01')
        RETURNING is_flamengo;
    """)
    is_flamengo = db_cursor.fetchone()[0]
    assert is_flamengo is True