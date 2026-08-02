"""Testes de concorrência (Etapa 2 — item 6), src/etapa2/concorrencia.py.

Usa slots (dia/turno) que não existem no seed de ESCALA, pra não colidir
com a UNIQUE(id_unidade, dia_semana, turno, id_residente) real."""
import pytest
from sqlalchemy import delete, select

pytestmark = pytest.mark.usefixtures("seeded_db")

from src.etapa2.concorrencia import (
    ConflitoEscalaError, demo, demo_otimista,
    escalar_residente_com_lock, escalar_residente_otimista,
)
from src.etapa2.models import Escala, Session

ID_UNIDADE = "f1111111-1111-1111-1111-111111111111"
ID_RESIDENTE = "c1111111-1111-1111-1111-111111111111"
ID_PRECEPTOR_A = "b1111111-1111-1111-1111-111111111111"
ID_PRECEPTOR_B = "b2222222-2222-2222-2222-222222222222"


def _limpar_slot(dia, turno):
    with Session.begin() as s:
        s.execute(
            delete(Escala).where(
                Escala.id_unidade == ID_UNIDADE,
                Escala.dia_semana == dia,
                Escala.turno == turno,
                Escala.id_residente == ID_RESIDENTE,
            )
        )


def test_escalar_residente_com_lock_cria_escala():
    _limpar_slot("domingo", "manha")
    id_escala = escalar_residente_com_lock(
        ID_UNIDADE, "domingo", "manha", ID_RESIDENTE, ID_PRECEPTOR_A,
    )
    with Session() as s:
        escala = s.get(Escala, id_escala)
        assert escala is not None
        assert escala.id_preceptor == ID_PRECEPTOR_A
    _limpar_slot("domingo", "manha")


def test_escalar_residente_com_lock_rejeita_slot_ja_ocupado():
    _limpar_slot("domingo", "tarde")
    escalar_residente_com_lock(ID_UNIDADE, "domingo", "tarde", ID_RESIDENTE, ID_PRECEPTOR_A)
    with pytest.raises(ConflitoEscalaError):
        escalar_residente_com_lock(ID_UNIDADE, "domingo", "tarde", ID_RESIDENTE, ID_PRECEPTOR_B)
    _limpar_slot("domingo", "tarde")


def test_demo_duas_threads_concorrentes_uma_sucede_uma_e_rejeitada():
    """A demo real do enunciado: duas threads disputando o mesmo residente
    no mesmo dia/turno/unidade. O lock pessimista deve serializar — nunca
    as duas passam, nunca as duas falham com erro cru de banco."""
    _limpar_slot("domingo", "noite")
    resultados = demo(
        id_unidade=ID_UNIDADE,
        dia_semana="domingo",
        turno="noite",
        id_residente=ID_RESIDENTE,
        id_preceptor_a=ID_PRECEPTOR_A,
        id_preceptor_b=ID_PRECEPTOR_B,
    )
    status = sorted(r[0] for r in resultados.values())
    assert status == ["rejeitada", "sucesso"]
    _limpar_slot("domingo", "noite")


# --- controle otimista (sem lock; UNIQUE detecta na escrita) ---

def test_escalar_residente_otimista_cria_escala():
    _limpar_slot("sabado", "manha")
    id_escala = escalar_residente_otimista(
        ID_UNIDADE, "sabado", "manha", ID_RESIDENTE, ID_PRECEPTOR_A,
    )
    with Session() as s:
        assert s.get(Escala, id_escala) is not None
    _limpar_slot("sabado", "manha")


def test_escalar_residente_otimista_rejeita_slot_ja_ocupado():
    _limpar_slot("sabado", "tarde")
    escalar_residente_otimista(ID_UNIDADE, "sabado", "tarde", ID_RESIDENTE, ID_PRECEPTOR_A)
    with pytest.raises(ConflitoEscalaError):
        escalar_residente_otimista(ID_UNIDADE, "sabado", "tarde", ID_RESIDENTE, ID_PRECEPTOR_B)
    _limpar_slot("sabado", "tarde")


def test_demo_otimista_uma_sucede_uma_e_rejeitada():
    """Mesma disputa, controle otimista: as duas threads rodam em paralelo
    (sem lock) e a UNIQUE rejeita quem perde a corrida na escrita — nunca as
    duas passam, nunca um IntegrityError cru escapa."""
    _limpar_slot("sabado", "noite")
    resultados = demo_otimista(
        id_unidade=ID_UNIDADE,
        dia_semana="sabado",
        turno="noite",
        id_residente=ID_RESIDENTE,
        id_preceptor_a=ID_PRECEPTOR_A,
        id_preceptor_b=ID_PRECEPTOR_B,
    )
    status = sorted(r[0] for r in resultados.values())
    assert status == ["rejeitada", "sucesso"]
    _limpar_slot("sabado", "noite")
