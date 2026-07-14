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


def _criar_procedimento_realizado(db_cursor, sufixo_cpf, id_atendimento, id_procedimento, codigo):
    """Monta a cadeia mínima paciente/residente/preceptor -> atendimento -> procedimento realizado."""
    id_residente = f'9{sufixo_cpf[0]}cccccc-cccc-cccc-cccc-cccccccccccc'
    id_preceptor = f'9{sufixo_cpf[0]}dddddd-dddd-dddd-dddd-dddddddddddd'
    id_paciente = f'9{sufixo_cpf[0]}eeeeee-eeee-eeee-eeee-eeeeeeeeeeee'

    _criar_residente(db_cursor, id_residente, sufixo_cpf + '01')
    _criar_preceptor(db_cursor, id_preceptor, sufixo_cpf + '02')
    db_cursor.execute("""
        INSERT INTO PESSOA (id_pessoa, nome, cpf, data_nascimento) VALUES (%s, 'Paciente Teste', %s, '1999-01-01');
    """, (id_paciente, sufixo_cpf + '03'))
    db_cursor.execute("INSERT INTO PACIENTE (id_pessoa) VALUES (%s);", (id_paciente,))
    db_cursor.execute("""
        INSERT INTO ATENDIMENTO (id_atendimento, data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor)
        VALUES (%s, '2025-02-01 08:00:00', 20, %s, %s, %s);
    """, (id_atendimento, id_paciente, id_residente, id_preceptor))
    db_cursor.execute("""
        INSERT INTO PROCEDIMENTO (id_procedimento, codigo, nome, tempo_medio_minutos)
        VALUES (%s, %s, 'Procedimento Teste', 10);
    """, (id_procedimento, codigo))
    db_cursor.execute("""
        INSERT INTO PROCEDIMENTO_REALIZADO (id_atendimento, id_procedimento, quantidade, tempo_real_minutos)
        VALUES (%s, %s, 1, 10);
    """, (id_atendimento, id_procedimento))


def test_delete_bloqueado_quando_ha_faturamento(db_cursor):
    """DELETE com NOT EXISTS não remove procedimento realizado que tem faturamento."""
    id_atendimento = '9fffffff-ffff-ffff-ffff-ffffffffffff'
    id_procedimento = '9a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a'
    _criar_procedimento_realizado(db_cursor, '444444444', id_atendimento, id_procedimento, 'TESTE-01')

    db_cursor.execute("""
        INSERT INTO FATURAMENTO (id_atendimento, id_procedimento, valor)
        VALUES (%s, %s, 150.00);
    """, (id_atendimento, id_procedimento))

    db_cursor.execute("""
        DELETE FROM PROCEDIMENTO_REALIZADO pr
        WHERE pr.id_atendimento = %s AND pr.id_procedimento = %s
          AND NOT EXISTS (
              SELECT 1 FROM FATURAMENTO f
              WHERE f.id_atendimento = pr.id_atendimento
                AND f.id_procedimento = pr.id_procedimento
          );
    """, (id_atendimento, id_procedimento))
    assert db_cursor.rowcount == 0


def test_delete_direto_de_faturado_viola_fk(db_cursor):
    """Sem o NOT EXISTS, a FK ON DELETE RESTRICT de FATURAMENTO barra o DELETE."""
    id_atendimento = '5fffffff-ffff-ffff-ffff-ffffffffffff'
    id_procedimento = '5a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a'
    _criar_procedimento_realizado(db_cursor, '555555555', id_atendimento, id_procedimento, 'TESTE-05')

    db_cursor.execute("""
        INSERT INTO FATURAMENTO (id_atendimento, id_procedimento, valor)
        VALUES (%s, %s, 90.00);
    """, (id_atendimento, id_procedimento))

    with pytest.raises(errors.ForeignKeyViolation):
        db_cursor.execute("""
            DELETE FROM PROCEDIMENTO_REALIZADO
            WHERE id_atendimento = %s AND id_procedimento = %s;
        """, (id_atendimento, id_procedimento))


def test_delete_permitido_sem_faturamento(db_cursor):
    """Procedimento realizado sem faturamento é removido normalmente."""
    id_atendimento = '6fffffff-ffff-ffff-ffff-ffffffffffff'
    id_procedimento = '6a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a'
    _criar_procedimento_realizado(db_cursor, '666666666', id_atendimento, id_procedimento, 'TESTE-06')

    db_cursor.execute("""
        DELETE FROM PROCEDIMENTO_REALIZADO pr
        WHERE pr.id_atendimento = %s AND pr.id_procedimento = %s
          AND NOT EXISTS (
              SELECT 1 FROM FATURAMENTO f
              WHERE f.id_atendimento = pr.id_atendimento
                AND f.id_procedimento = pr.id_procedimento
          );
    """, (id_atendimento, id_procedimento))
    assert db_cursor.rowcount == 1


def test_faturamento_unico_por_procedimento_realizado(db_cursor):
    """Um procedimento realizado não pode ser faturado duas vezes."""
    id_atendimento = '7fffffff-ffff-ffff-ffff-ffffffffffff'
    id_procedimento = '7a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a'
    _criar_procedimento_realizado(db_cursor, '777777777', id_atendimento, id_procedimento, 'TESTE-07')

    db_cursor.execute("""
        INSERT INTO FATURAMENTO (id_atendimento, id_procedimento, valor) VALUES (%s, %s, 10.00);
    """, (id_atendimento, id_procedimento))

    with pytest.raises(errors.UniqueViolation):
        db_cursor.execute("""
            INSERT INTO FATURAMENTO (id_atendimento, id_procedimento, valor) VALUES (%s, %s, 20.00);
        """, (id_atendimento, id_procedimento))
