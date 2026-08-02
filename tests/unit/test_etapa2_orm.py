"""Testes da ORM (Etapa 2 — item 4), src/etapa2/crud_orm.py.

Usa a fixture seeded_db (conftest.py): schema + seeds reais carregados uma
vez por sessão. As consultas somente-leitura rodam primeiro (contam com os
totais exatos do seed); as mutações ficam no fim do arquivo para não
derrubar as contagens exatas de quem roda antes.
"""
import uuid

import psycopg2
import pytest

pytestmark = pytest.mark.usefixtures("seeded_db")

from src.etapa2 import crud_orm

ID_PACIENTE_GABIGOL = "a2222222-2222-2222-2222-222222222222"
ID_RESIDENTE = "c1111111-1111-1111-1111-111111111111"
ID_PRECEPTOR = "b1111111-1111-1111-1111-111111111111"
ID_UNIDADE = "f1111111-1111-1111-1111-111111111111"
ID_PROCEDIMENTO = "d1111111-1111-1111-1111-111111111111"


# ---- somente leitura: contam com o volume exato do seed -----------------

def test_ranking_residentes_bate_com_seed():
    ranking = crud_orm.ranking_residentes()
    assert len(ranking) == 5
    assert ranking[0]["residente"] == "Residente Ayrton Lucas"
    assert ranking[0]["total_atendimentos"] == 4


def test_tempo_medio_por_residente_inclui_todos():
    linhas = crud_orm.tempo_medio_por_residente()
    assert len(linhas) == 5
    assert all(l["total_atendimentos"] > 0 for l in linhas)


def test_preceptores_mais_atendimentos_mes_bate_com_seed():
    linhas = crud_orm.preceptores_mais_atendimentos_mes(2025, 6)
    assert linhas == [{"preceptor": "Dr. Jorge Jesus", "total_atendimentos": 8}]


def test_preceptores_mais_atendimentos_mes_sem_resultado_fora_do_periodo():
    assert crud_orm.preceptores_mais_atendimentos_mes(2030, 1) == []


def test_pacientes_sem_procedimento_risco_alto_bate_com_seed():
    # >= (não ==): outros módulos de teste (ex. webapp) podem ter criado
    # pacientes extras sem nenhum procedimento, que também qualificam como
    # "sem risco ALTO" — o comportamento correto da query, não um bug.
    nomes = {p["paciente"] for p in crud_orm.pacientes_sem_procedimento_risco_alto()}
    assert nomes.issuperset({"Gabigol da Silva", "Arrascaeta Giorgian", "Pedro Guilherme"})


def test_listar_procedimentos_atendimento_traz_nivel_risco():
    procs = crud_orm.listar_procedimentos_atendimento("e1111111-1111-1111-1111-111111111111")
    assert len(procs) == 2
    assert {p["procedimento"] for p in procs} == {"Sutura simples", "Coleta de sangue"}
    assert all("nivel_risco" in p for p in procs)


# ---- mutação: rodam por último, cada uma isolada em ids próprios --------

def test_inserir_atendimento_e_listar_round_trip():
    antes = len(crud_orm.listar_atendimentos_paciente(ID_PACIENTE_GABIGOL))
    novo_id = crud_orm.inserir_atendimento(
        "2025-06-25 10:00:00", 30, ID_PACIENTE_GABIGOL, ID_RESIDENTE, ID_PRECEPTOR, ID_UNIDADE,
    )
    depois = crud_orm.listar_atendimentos_paciente(ID_PACIENTE_GABIGOL)
    assert len(depois) == antes + 1
    assert depois[0]["id_atendimento"] == novo_id  # mais recente primeiro (ORDER BY data_hora DESC)
    assert depois[0]["residente"] == "Residente Gerson"


def test_inserir_atendimento_com_paciente_inexistente_levanta_valueerror():
    with pytest.raises(ValueError, match="paciente não encontrado"):
        crud_orm.inserir_atendimento(
            "2025-06-25 10:00:00", 30, str(uuid.uuid4()), ID_RESIDENTE, ID_PRECEPTOR, ID_UNIDADE,
        )


def test_atualizar_paciente_persiste():
    crud_orm.atualizar_paciente(ID_PACIENTE_GABIGOL, novo_convenio="NOVO-CONV-999")
    with psycopg2.connect(
        "dbname=hospital_db user=postgres password=password host=localhost port=5433"
    ) as conn, conn.cursor() as cur:
        cur.execute("SELECT num_convenio FROM PACIENTE WHERE id_pessoa = %s", (ID_PACIENTE_GABIGOL,))
        assert cur.fetchone()[0] == "NOVO-CONV-999"


def _criar_procedimento_realizado_isolado(id_atendimento, id_procedimento_realizado_extra=None):
    """Cria um atendimento novo + um procedimento realizado próprio, sem
    faturamento, pra testar remoção sem interferir no seed."""
    conn = psycopg2.connect(
        "dbname=hospital_db user=postgres password=password host=localhost port=5433"
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO ATENDIMENTO (id_atendimento, data_hora, duracao_minutos,
                   id_paciente, id_residente, id_preceptor, id_unidade)
               VALUES (%s, '2025-06-26 10:00:00', 20, %s, %s, %s, %s)""",
            (id_atendimento, ID_PACIENTE_GABIGOL, ID_RESIDENTE, ID_PRECEPTOR, ID_UNIDADE),
        )
        cur.execute(
            """INSERT INTO PROCEDIMENTO_REALIZADO
                   (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio)
               VALUES (%s, %s, 1, 5, '2025-06-26 10:05:00')""",
            (id_atendimento, ID_PROCEDIMENTO),
        )
    conn.close()


def test_remover_procedimento_realizado_sem_faturamento():
    id_atendimento = str(uuid.uuid4())
    _criar_procedimento_realizado_isolado(id_atendimento)
    apagadas = crud_orm.remover_procedimento_realizado(id_atendimento, ID_PROCEDIMENTO)
    assert apagadas == 1


def test_remover_procedimento_realizado_bloqueado_com_faturamento():
    id_atendimento = str(uuid.uuid4())
    _criar_procedimento_realizado_isolado(id_atendimento)
    conn = psycopg2.connect(
        "dbname=hospital_db user=postgres password=password host=localhost port=5433"
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO FATURAMENTO (id_atendimento, id_procedimento, valor) VALUES (%s, %s, 100.00)",
            (id_atendimento, ID_PROCEDIMENTO),
        )
    conn.close()

    apagadas = crud_orm.remover_procedimento_realizado(id_atendimento, ID_PROCEDIMENTO)
    assert apagadas == 0
