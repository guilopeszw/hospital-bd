import pytest
from psycopg2 import errors


def _criar_residente(cur, id_pessoa, cpf):
    cur.execute("""
        INSERT INTO PESSOA (id_pessoa, nome, cpf, data_nascimento)
        VALUES (%s, 'Residente Teste', %s, '1995-01-01');
    """, (id_pessoa, cpf))
    cur.execute("""
        INSERT INTO PROFISSIONAL (id_pessoa, crm, data_admissao, especialidade, papel_atual)
        VALUES (%s, %s, '2020-01-01', 'Clinica Geral', 'residente');
    """, (id_pessoa, cpf))
    cur.execute("""
        INSERT INTO RESIDENTE (id_pessoa, ano_residencia) VALUES (%s, 'R1');
    """, (id_pessoa,))


def _criar_preceptor(cur, id_pessoa, cpf):
    cur.execute("""
        INSERT INTO PESSOA (id_pessoa, nome, cpf, data_nascimento)
        VALUES (%s, 'Preceptor Teste', %s, '1980-01-01');
    """, (id_pessoa, cpf))
    cur.execute("""
        INSERT INTO PROFISSIONAL (id_pessoa, crm, data_admissao, especialidade, papel_atual)
        VALUES (%s, %s, '2010-01-01', 'Clinica Geral', 'preceptor');
    """, (id_pessoa, cpf))
    cur.execute("""
        INSERT INTO PRECEPTOR (id_pessoa, titulacao) VALUES (%s, 'Doutor');
    """, (id_pessoa,))


def _criar_unidade(cur, id_unidade):
    cur.execute("""
        INSERT INTO UNIDADE (id_unidade, nome, tipo, capacidade_leitos)
        VALUES (%s, 'Unidade Teste', 'Enfermaria', 10);
    """, (id_unidade,))


def test_atendimento_fk_paciente_inexistente(db_cursor):
    """FK de ATENDIMENTO barra id_paciente que não existe em PACIENTE."""
    id_residente = '91111111-1111-1111-1111-111111111111'
    id_preceptor = '92222222-2222-2222-2222-222222222222'
    _criar_residente(db_cursor, id_residente, '11111111101')
    _criar_preceptor(db_cursor, id_preceptor, '11111111102')

    with pytest.raises(errors.ForeignKeyViolation):
        db_cursor.execute("""
            INSERT INTO ATENDIMENTO (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor)
            VALUES ('2025-01-01 10:00:00', 30, '93333333-3333-3333-3333-333333333333', %s, %s);
        """, (id_residente, id_preceptor))


def test_escala_unique_constraint(db_cursor):
    """Mesmo residente/unidade/dia/turno com preceptores diferentes viola a UNIQUE."""
    id_unidade = '94444444-4444-4444-4444-444444444444'
    id_residente = '95555555-5555-5555-5555-555555555555'
    id_preceptor_1 = '96666666-6666-6666-6666-666666666666'
    id_preceptor_2 = '97777777-7777-7777-7777-777777777777'
    _criar_unidade(db_cursor, id_unidade)
    _criar_residente(db_cursor, id_residente, '22222222201')
    _criar_preceptor(db_cursor, id_preceptor_1, '22222222202')
    _criar_preceptor(db_cursor, id_preceptor_2, '22222222203')

    db_cursor.execute("""
        INSERT INTO ESCALA (id_unidade, dia_semana, turno, id_residente, id_preceptor)
        VALUES (%s, 'segunda', 'manha', %s, %s);
    """, (id_unidade, id_residente, id_preceptor_1))

    with pytest.raises(errors.UniqueViolation):
        db_cursor.execute("""
            INSERT INTO ESCALA (id_unidade, dia_semana, turno, id_residente, id_preceptor)
            VALUES (%s, 'segunda', 'manha', %s, %s);
        """, (id_unidade, id_residente, id_preceptor_2))


def test_escala_mesmo_preceptor_residentes_diferentes_permitido(db_cursor):
    """Um preceptor pode supervisionar dois residentes diferentes no mesmo plantão."""
    id_unidade = '98888888-8888-8888-8888-888888888888'
    id_residente_1 = '99999999-9999-9999-9999-999999999999'
    id_residente_2 = '9aaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    id_preceptor = '9bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
    _criar_unidade(db_cursor, id_unidade)
    _criar_residente(db_cursor, id_residente_1, '33333333301')
    _criar_residente(db_cursor, id_residente_2, '33333333302')
    _criar_preceptor(db_cursor, id_preceptor, '33333333303')

    db_cursor.execute("""
        INSERT INTO ESCALA (id_unidade, dia_semana, turno, id_residente, id_preceptor)
        VALUES (%s, 'terca', 'tarde', %s, %s);
    """, (id_unidade, id_residente_1, id_preceptor))
    db_cursor.execute("""
        INSERT INTO ESCALA (id_unidade, dia_semana, turno, id_residente, id_preceptor)
        VALUES (%s, 'terca', 'tarde', %s, %s);
    """, (id_unidade, id_residente_2, id_preceptor))

    db_cursor.execute("SELECT COUNT(*) FROM ESCALA WHERE id_preceptor = %s;", (id_preceptor,))
    assert db_cursor.fetchone()[0] == 2


def test_procedimento_realizado_faturado_bloqueia_delete(db_cursor):
    """DELETE com filtro faturado=FALSE não remove um procedimento já faturado."""
    id_residente = '9ccccccc-cccc-cccc-cccc-cccccccccccc'
    id_preceptor = '9ddddddd-dddd-dddd-dddd-dddddddddddd'
    id_paciente = '9eeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'
    id_atendimento = '9fffffff-ffff-ffff-ffff-ffffffffffff'
    id_procedimento = '9a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a'

    _criar_residente(db_cursor, id_residente, '44444444401')
    _criar_preceptor(db_cursor, id_preceptor, '44444444402')
    db_cursor.execute("""
        INSERT INTO PESSOA (id_pessoa, nome, cpf, data_nascimento) VALUES (%s, 'Paciente Teste', '44444444403', '1999-01-01');
    """, (id_paciente,))
    db_cursor.execute("INSERT INTO PACIENTE (id_pessoa) VALUES (%s);", (id_paciente,))
    db_cursor.execute("""
        INSERT INTO ATENDIMENTO (id_atendimento, data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor)
        VALUES (%s, '2025-02-01 08:00:00', 20, %s, %s, %s);
    """, (id_atendimento, id_paciente, id_residente, id_preceptor))
    db_cursor.execute("""
        INSERT INTO PROCEDIMENTO (id_procedimento, codigo, nome, tempo_medio_minutos)
        VALUES (%s, 'TESTE-01', 'Procedimento Teste', 10);
    """, (id_procedimento,))
    db_cursor.execute("""
        INSERT INTO PROCEDIMENTO_REALIZADO (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, faturado)
        VALUES (%s, %s, 1, 10, TRUE);
    """, (id_atendimento, id_procedimento))

    db_cursor.execute("""
        DELETE FROM PROCEDIMENTO_REALIZADO
        WHERE id_atendimento = %s AND id_procedimento = %s AND faturado = FALSE;
    """, (id_atendimento, id_procedimento))
    assert db_cursor.rowcount == 0


def test_procedimento_nivel_risco_enum_invalido(db_cursor):
    """Valor fora do enum nivel_risco_enum é rejeitado."""
    with pytest.raises(errors.InvalidTextRepresentation):
        db_cursor.execute("""
            INSERT INTO PROCEDIMENTO (codigo, nome, tempo_medio_minutos, nivel_risco)
            VALUES ('TESTE-02', 'Procedimento Invalido', 10, 'EXTREMO');
        """)


def test_unidade_capacidade_leitos_positiva(db_cursor):
    """capacidade_leitos <= 0 viola o CHECK da tabela UNIDADE."""
    with pytest.raises(errors.CheckViolation):
        db_cursor.execute("""
            INSERT INTO UNIDADE (nome, tipo, capacidade_leitos)
            VALUES ('Unidade Invalida', 'Enfermaria', 0);
        """)
