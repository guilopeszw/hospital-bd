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
