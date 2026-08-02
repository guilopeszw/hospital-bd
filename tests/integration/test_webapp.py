"""Testes da API Flask do webapp (webapp/api/app.py).

Carrega o módulo direto do arquivo (webapp/api não é um pacote Python) e
usa o test client do Flask — sobe nenhum processo, mas bate no Postgres
real via seeded_db. Evita asserções de contagem global frágeis: onde
precisa de um número exato, mede antes/depois em vez de fixar o total.
"""
import importlib.util
import os

import pytest

pytestmark = pytest.mark.usefixtures("seeded_db")

_APP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "webapp", "api", "app.py",
)


@pytest.fixture(scope="module")
def client():
    spec = importlib.util.spec_from_file_location("webapp_app", _APP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.app.testing = True
    with module.app.test_client() as c:
        yield c


def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_dashboard_summary_tem_todos_os_campos(client):
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.get_json()
    for campo in (
        "total_pacientes", "total_profissionais", "atendimentos_mes",
        "plantoes_hoje", "faturamento_mes", "pacientes_sem_risco_alto",
    ):
        assert campo in body


def test_listar_pacientes_bate_com_seed(client):
    resp = client.get("/api/pacientes")
    assert resp.status_code == 200
    nomes = {p["nome"] for p in resp.get_json()}
    assert "Gabigol da Silva" in nomes
    assert len(resp.get_json()) == 5


def test_listar_pacientes_busca_filtra(client):
    resp = client.get("/api/pacientes?busca=Gabigol")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body) == 1
    assert body[0]["nome"] == "Gabigol da Silva"


def test_criar_paciente_persiste_e_retorna_201(client):
    antes = len(client.get("/api/pacientes").get_json())
    resp = client.post("/api/pacientes", json={
        "nome": "Paciente Teste Webapp",
        "cpf": "10920930450",
        "data_nascimento": "1990-01-01",
    })
    assert resp.status_code == 201
    assert "id_pessoa" in resp.get_json()
    depois = len(client.get("/api/pacientes").get_json())
    assert depois == antes + 1


def test_criar_paciente_sem_campo_obrigatorio_retorna_400(client):
    resp = client.post("/api/pacientes", json={"nome": "Sem CPF"})
    assert resp.status_code == 400
    assert "erro" in resp.get_json()


def test_criar_paciente_cpf_duplicado_retorna_409(client):
    dados = {"nome": "Duplicado", "cpf": "10920930451", "data_nascimento": "1990-01-01"}
    r1 = client.post("/api/pacientes", json=dados)
    assert r1.status_code == 201
    r2 = client.post("/api/pacientes", json=dados)
    assert r2.status_code == 409


def test_atendimentos_do_paciente(client):
    pacientes = client.get("/api/pacientes").get_json()
    gabigol = next(p for p in pacientes if p["nome"] == "Gabigol da Silva")
    resp = client.get(f"/api/pacientes/{gabigol['id_pessoa']}/atendimentos")
    assert resp.status_code == 200
    assert len(resp.get_json()) > 0


def test_criar_atendimento_unidade_invalida_retorna_404(client):
    pacientes = client.get("/api/pacientes").get_json()
    resp = client.post("/api/atendimentos", json={
        "data_hora": "2025-07-01 10:00:00",
        "duracao_minutos": 30,
        "id_paciente": pacientes[0]["id_pessoa"],
        "id_residente": "c1111111-1111-1111-1111-111111111111",
        "id_preceptor": "b1111111-1111-1111-1111-111111111111",
        "id_unidade": "00000000-0000-0000-0000-000000000000",
    })
    assert resp.status_code == 404


def test_criar_atendimento_valido_persiste(client):
    # Data de propósito ANTERIOR ao seed (2020, não 2025): outros módulos
    # de teste (consultas avançadas) esperam que o atendimento mais
    # recente de cada paciente continue sendo o do seed. Uma data no
    # passado prova a persistência sem virar o "último atendimento".
    resp = client.post("/api/atendimentos", json={
        "data_hora": "2020-01-01 10:00:00",
        "duracao_minutos": 30,
        "id_paciente": "a2222222-2222-2222-2222-222222222222",
        "id_residente": "c1111111-1111-1111-1111-111111111111",
        "id_preceptor": "b1111111-1111-1111-1111-111111111111",
        "id_unidade": "f1111111-1111-1111-1111-111111111111",
    })
    assert resp.status_code == 201
    assert "id_atendimento" in resp.get_json()


def test_unidades_procedimentos_escalas_listam(client):
    assert len(client.get("/api/unidades").get_json()) == 3
    assert len(client.get("/api/procedimentos").get_json()) == 10
    assert len(client.get("/api/escalas").get_json()) >= 8


def test_profissionais_lista_residentes_e_preceptores(client):
    body = client.get("/api/profissionais").get_json()
    assert len(body) == 10
    papeis = {p["papel_atual"] for p in body}
    assert papeis == {"residente", "preceptor"}


def test_analytics_ranking_residentes(client):
    resp = client.get("/api/analytics/ranking-residentes")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 5


def test_analytics_preceptores_mais_atendimentos_bate_com_seed(client):
    resp = client.get("/api/analytics/preceptores-mais-atendimentos?ano=2025&mes=6&minimo=5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == [{"preceptor": "Dr. Jorge Jesus", "total_atendimentos": 8}]


def test_analytics_pacientes_sem_risco_alto(client):
    # Roda depois dos testes de criação de paciente neste módulo — um
    # paciente novo sem nenhum procedimento também conta como "sem risco
    # ALTO" (não tem procedimento nenhum, logo não tem um de risco ALTO).
    # Por isso superset, não igualdade exata.
    resp = client.get("/api/analytics/pacientes-sem-risco-alto")
    nomes = {p["paciente"] for p in resp.get_json()}
    assert nomes.issuperset({"Gabigol da Silva", "Arrascaeta Giorgian", "Pedro Guilherme"})


def test_analytics_tempo_medio_residente(client):
    resp = client.get("/api/analytics/tempo-medio-residente")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 5


# ---------------------------------------------------------------------
# Etapa 2 no webapp: views, stored procedures e triggers via HTTP.
# Testes abaixo rodam por ÚLTIMO neste arquivo de propósito — os que
# criam dado novo (residente, escala, atendimento) fazem sua própria
# limpeza no fim, pra não quebrar as contagens exatas usadas pelos
# módulos de teste de ORM/consultas avançadas (que rodam depois deste
# arquivo, na mesma sessão de pytest).
# ---------------------------------------------------------------------

def _psycopg2_conn():
    import psycopg2
    conn = psycopg2.connect(
        "dbname=hospital_db user=postgres password=password host=localhost port=5433"
    )
    conn.autocommit = True
    return conn


def test_dashboard_usa_as_views_da_etapa2(client):
    body = client.get("/api/dashboard/summary").get_json()
    assert body["pacientes_internados"] == 2  # vw_pacientes_internados, seed real
    assert body["residentes_sem_supervisor"] >= 1  # vw_residentes_sem_supervisor


def test_views_pacientes_internados(client):
    resp = client.get("/api/views/pacientes-internados")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_views_residentes_sem_supervisor(client):
    resp = client.get("/api/views/residentes-sem-supervisor")
    assert resp.status_code == 200
    linhas = resp.get_json()
    assert linhas
    assert all("titulacao" in l for l in linhas)


def test_views_estatisticas_mensais(client):
    # Não fixa o total de linhas: outros testes desta suite criam
    # atendimentos isolados em datas antigas (ex. 2020) pra não virar o
    # "mais recente" de ninguém, e isso soma outro mês na view. Filtra só
    # junho/2025 (mês do seed original), que sempre tem as 3 unidades.
    resp = client.get("/api/views/estatisticas-mensais")
    assert resp.status_code == 200
    linhas_junho = [l for l in resp.get_json() if l["mes"].startswith("Sun, 01 Jun 2025")]
    assert {l["unidade"] for l in linhas_junho} == {"Enfermaria Central", "Pronto-Socorro", "UTI Adulto"}


def test_analytics_tempo_medio_espera_chama_procedure(client):
    resp = client.get("/api/analytics/tempo-medio-espera")
    assert resp.status_code == 200
    unidades = {l["unidade"] for l in resp.get_json()}
    assert unidades == {"Enfermaria Central", "Pronto-Socorro", "UTI Adulto"}


def test_listar_procedimentos_atendimento(client):
    resp = client.get("/api/atendimentos/e1111111-1111-1111-1111-111111111111/procedimentos")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body) == 2
    assert all("faturado" in p for p in body)


def test_registrar_e_remover_procedimento_dispara_trigger_media(client):
    """POST em /procedimentos dispara trg_atualiza_media_procedimentos —
    confere que media_tempo_procedimento muda de verdade no banco."""
    id_atendimento = "e1111111-1111-1111-1111-111111111111"
    id_procedimento = "d6666666-6666-6666-6666-666666666666"  # CURATIVO, não usado nesse atendimento

    conn = _psycopg2_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT media_tempo_procedimento FROM procedimento WHERE id_procedimento = %s",
            (id_procedimento,),
        )
        media_antes = cur.fetchone()[0]

    resp = client.post(
        f"/api/atendimentos/{id_atendimento}/procedimentos",
        json={"id_procedimento": id_procedimento, "tempo_real_minutos": 999, "data_hora_inicio": "2025-06-10 08:30:00"},
    )
    assert resp.status_code == 201

    conn2 = _psycopg2_conn()
    with conn2.cursor() as cur:
        cur.execute(
            "SELECT media_tempo_procedimento FROM procedimento WHERE id_procedimento = %s",
            (id_procedimento,),
        )
        media_depois = cur.fetchone()[0]
    assert media_depois != media_antes, "trigger deveria ter recalculado a média"

    # remove sem faturamento — permitido
    resp = client.delete(f"/api/atendimentos/{id_atendimento}/procedimentos/{id_procedimento}")
    assert resp.status_code == 204


def test_registrar_procedimento_campo_obrigatorio_ausente(client):
    resp = client.post(
        "/api/atendimentos/e1111111-1111-1111-1111-111111111111/procedimentos",
        json={"id_procedimento": "d1111111-1111-1111-1111-111111111111"},
    )
    assert resp.status_code == 400


def test_remover_procedimento_bloqueado_com_faturamento(client):
    id_atendimento = str(__import__("uuid").uuid4())
    id_procedimento = "d7777777-7777-7777-7777-777777777777"
    conn = _psycopg2_conn()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO ATENDIMENTO (id_atendimento, data_hora, duracao_minutos,
                   id_paciente, id_residente, id_preceptor, id_unidade)
               VALUES (%s, '2020-01-01 08:00:00', 10,
                   'a1111111-1111-1111-1111-111111111111', 'c1111111-1111-1111-1111-111111111111',
                   'b1111111-1111-1111-1111-111111111111', 'f1111111-1111-1111-1111-111111111111')""",
            (id_atendimento,),
        )
        cur.execute(
            """INSERT INTO PROCEDIMENTO_REALIZADO
                   (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio)
               VALUES (%s, %s, 1, 5, '2020-01-01 08:05:00')""",
            (id_atendimento, id_procedimento),
        )
        cur.execute(
            "INSERT INTO FATURAMENTO (id_atendimento, id_procedimento, valor) VALUES (%s, %s, 50.00)",
            (id_atendimento, id_procedimento),
        )

    resp = client.delete(f"/api/atendimentos/{id_atendimento}/procedimentos/{id_procedimento}")
    assert resp.status_code == 409


def test_criar_faturamento_bloqueia_duplicado(client):
    id_atendimento = str(__import__("uuid").uuid4())
    id_procedimento = "d8888888-8888-8888-8888-888888888888"
    conn = _psycopg2_conn()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO ATENDIMENTO (id_atendimento, data_hora, duracao_minutos,
                   id_paciente, id_residente, id_preceptor, id_unidade)
               VALUES (%s, '2020-01-01 08:00:00', 10,
                   'a1111111-1111-1111-1111-111111111111', 'c1111111-1111-1111-1111-111111111111',
                   'b1111111-1111-1111-1111-111111111111', 'f1111111-1111-1111-1111-111111111111')""",
            (id_atendimento,),
        )
        cur.execute(
            """INSERT INTO PROCEDIMENTO_REALIZADO
                   (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio)
               VALUES (%s, %s, 1, 5, '2020-01-01 08:05:00')""",
            (id_atendimento, id_procedimento),
        )

    r1 = client.post("/api/faturamentos", json={
        "id_atendimento": id_atendimento, "id_procedimento": id_procedimento, "valor": 80.0,
    })
    assert r1.status_code == 201
    r2 = client.post("/api/faturamentos", json={
        "id_atendimento": id_atendimento, "id_procedimento": id_procedimento, "valor": 80.0,
    })
    assert r2.status_code == 409


def test_criar_escala_e_trigger_bloqueia_sobreposicao(client):
    """POST /api/escalas dispara trg_check_sobreposicao_escala de verdade
    (mesmo residente, mesmo dia/turno, unidade diferente = 409)."""
    payload_base = {
        "dia_semana": "domingo", "turno": "manha",
        "id_residente": "c5555555-5555-5555-5555-555555555555",
        "id_preceptor": "b1111111-1111-1111-1111-111111111111",
    }
    r1 = client.post("/api/escalas", json={**payload_base, "id_unidade": "f1111111-1111-1111-1111-111111111111"})
    assert r1.status_code == 201
    r2 = client.post("/api/escalas", json={**payload_base, "id_unidade": "f2222222-2222-2222-2222-222222222222"})
    assert r2.status_code == 409
    assert "sobreposi" in r2.get_json()["erro"].lower()

    # limpeza: não deixar essa escala extra pra trás
    conn = _psycopg2_conn()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ESCALA WHERE id_residente = %s AND dia_semana = 'domingo' AND turno = 'manha'",
            ("c5555555-5555-5555-5555-555555555555",),
        )


def test_reajustar_escala_via_procedure(client):
    """POST /api/escalas/reajustar chama sp_reajustar_escala de verdade —
    confere no banco que a escala realmente mudou de slot."""
    conn = _psycopg2_conn()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO ESCALA (id_unidade, dia_semana, turno, id_residente, id_preceptor)
               VALUES ('f1111111-1111-1111-1111-111111111111', 'domingo', 'tarde',
                       'c5555555-5555-5555-5555-555555555555', 'b1111111-1111-1111-1111-111111111111')"""
        )

    resp = client.post("/api/escalas/reajustar", json={
        "id_residente": "c5555555-5555-5555-5555-555555555555",
        "dia_origem": "domingo", "turno_origem": "tarde",
        "dia_destino": "domingo", "turno_destino": "noite",
    })
    assert resp.status_code == 200
    assert resp.get_json()["escalas_movidas"] == 1

    with conn.cursor() as cur:
        cur.execute(
            "SELECT turno FROM ESCALA WHERE id_residente = %s AND dia_semana = 'domingo'",
            ("c5555555-5555-5555-5555-555555555555",),
        )
        turnos = {r[0] for r in cur.fetchall()}
    assert "noite" in turnos and "tarde" not in turnos

    # limpeza
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ESCALA WHERE id_residente = %s AND dia_semana = 'domingo'",
            ("c5555555-5555-5555-5555-555555555555",),
        )


def test_criar_atendimento_com_procedimentos_via_stored_procedure(client):
    """Confirma que POST /api/atendimentos com `procedimentos` realmente
    persiste via sp_registrar_atendimento_completo — não só retorna 201,
    confere no banco (bug real encontrado e corrigido: a versão anterior
    usava a conexão de leitura, que nunca comita, e o INSERT feito
    dentro da function era silenciosamente descartado)."""
    resp = client.post("/api/atendimentos", json={
        "data_hora": "2020-01-01 09:00:00", "duracao_minutos": 20,
        "id_paciente": "a3333333-3333-3333-3333-333333333333",
        "id_residente": "c3333333-3333-3333-3333-333333333333",
        "id_preceptor": "b2222222-2222-2222-2222-222222222222",
        "id_unidade": "f2222222-2222-2222-2222-222222222222",
        "procedimentos": [{
            "id_procedimento": "d2222222-2222-2222-2222-222222222222",
            "quantidade": 1, "tempo_real_minutos": 9,
            "data_hora_inicio": "2020-01-01 09:05:00",
        }],
    })
    assert resp.status_code == 201
    id_atendimento = resp.get_json()["id_atendimento"]

    conn = _psycopg2_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM ATENDIMENTO WHERE id_atendimento = %s", (id_atendimento,))
        assert cur.fetchone() is not None, "atendimento não foi persistido"
        cur.execute(
            "SELECT 1 FROM PROCEDIMENTO_REALIZADO WHERE id_atendimento = %s", (id_atendimento,)
        )
        assert cur.fetchone() is not None, "procedimento não foi persistido"


def test_cadastrar_profissional_residente_e_preceptor(client):
    """Cadastra 1 residente + 1 preceptor via API e confere persistência.
    Remove os dois no fim — outros módulos de teste (ORM/consultas
    avançadas) assumem exatamente 5 residentes e quebrariam se esse
    residente novo ficasse para trás."""
    conn = _psycopg2_conn()

    r_prec = client.post("/api/profissionais", json={
        "tipo": "preceptor", "nome": "Dra. Teste Webapp", "cpf": "90019002900",
        "data_nascimento": "1975-01-01", "crm": "CRM/PB 0001",
        "data_admissao": "2010-01-01", "especialidade": "Clinica Geral", "titulacao": "Doutor",
    })
    assert r_prec.status_code == 201
    id_preceptor = r_prec.get_json()["id_pessoa"]

    r_res = client.post("/api/profissionais", json={
        "tipo": "residente", "nome": "Residente Teste Webapp", "cpf": "90029003900",
        "data_nascimento": "1998-01-01", "crm": "CRM/PB 0002",
        "data_admissao": "2025-02-01", "especialidade": "Clinica Geral", "ano_residencia": "R1",
    })
    assert r_res.status_code == 201
    id_residente = r_res.get_json()["id_pessoa"]

    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM PRECEPTOR WHERE id_pessoa = %s", (id_preceptor,))
        assert cur.fetchone() is not None
        cur.execute("SELECT 1 FROM RESIDENTE WHERE id_pessoa = %s", (id_residente,))
        assert cur.fetchone() is not None

        for id_pessoa in (id_preceptor, id_residente):
            cur.execute("DELETE FROM PROFISSIONAL WHERE id_pessoa = %s", (id_pessoa,))
            cur.execute("DELETE FROM PESSOA WHERE id_pessoa = %s", (id_pessoa,))


def test_cadastrar_profissional_cpf_duplicado_retorna_409(client):
    resp = client.post("/api/profissionais", json={
        "tipo": "preceptor", "nome": "Duplicado", "cpf": "12312312311",  # CPF real do seed (Residente Gerson)
        "data_nascimento": "1975-01-01", "crm": "CRM/PB 0003",
        "data_admissao": "2010-01-01", "especialidade": "Clinica Geral", "titulacao": "Doutor",
    })
    assert resp.status_code == 409


def test_cadastrar_unidade(client):
    resp = client.post("/api/unidades", json={
        "nome": "Unidade Teste Webapp", "tipo": "Ambulatorio", "capacidade_leitos": 5,
    })
    assert resp.status_code == 201
    id_unidade = resp.get_json()["id_unidade"]

    conn = _psycopg2_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM UNIDADE WHERE id_unidade = %s", (id_unidade,))
        assert cur.fetchone() is not None
        cur.execute("DELETE FROM UNIDADE WHERE id_unidade = %s", (id_unidade,))


def test_atualizar_paciente_via_put(client):
    id_paciente = "a5555555-5555-5555-5555-555555555555"  # Pedro Guilherme
    resp = client.put(f"/api/pacientes/{id_paciente}", json={"num_convenio": "CONV-WEBAPP-TESTE"})
    assert resp.status_code == 200

    conn = _psycopg2_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT num_convenio FROM PACIENTE WHERE id_pessoa = %s", (id_paciente,))
        assert cur.fetchone()[0] == "CONV-WEBAPP-TESTE"


def test_atualizar_paciente_inexistente_retorna_404(client):
    resp = client.put(
        f"/api/pacientes/{'0' * 8}-0000-0000-0000-{'0' * 12}",
        json={"num_convenio": "X"},
    )
    assert resp.status_code == 404
