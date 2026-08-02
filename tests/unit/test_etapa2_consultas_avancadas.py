"""Testes das consultas avançadas via ORM (Etapa 2 — item 5),
src/etapa2/consultas_avancadas.py. Somente leitura contra o seed real."""
import pytest

pytestmark = pytest.mark.usefixtures("seeded_db")

from src.etapa2 import consultas_avancadas as ca


def test_preceptores_supervisionaram_flamenguistas_bate_com_seed():
    nomes = ca.preceptores_supervisionaram_flamenguistas()
    assert nomes == sorted(nomes)  # ORDER BY nome
    assert set(nomes) == {"Dr. Dorival Junior", "Dr. Jorge Jesus", "Dra. Yuska Maritan"}


def test_ultimo_atendimento_por_paciente_uma_linha_por_paciente():
    linhas = ca.ultimo_atendimento_por_paciente()
    pacientes = [l["paciente"] for l in linhas]
    assert len(pacientes) == len(set(pacientes)), "não deve haver paciente duplicado"
    assert len(linhas) == 5
    for l in linhas:
        assert l["procedimentos"], f"{l['paciente']} deveria ter ao menos 1 procedimento"


def test_ultimo_atendimento_e_realmente_o_mais_recente():
    linhas = {l["paciente"]: l for l in ca.ultimo_atendimento_por_paciente()}
    gabigol = linhas["Gabigol da Silva"]
    assert gabigol["data_hora"].isoformat().startswith("2025-06-20")


def test_percentual_alto_risco_soma_bate_e_inclui_residente_zerado():
    linhas = ca.percentual_procedimentos_alto_risco_por_residente()
    assert len(linhas) == 5
    for l in linhas:
        if l["total_procedimentos"] == 0:
            assert l["percentual_alto_risco"] == 0.0
        else:
            esperado = round((l["alto_risco"] / l["total_procedimentos"]) * 100, 1)
            assert l["percentual_alto_risco"] == esperado
        assert l["alto_risco"] <= l["total_procedimentos"]
