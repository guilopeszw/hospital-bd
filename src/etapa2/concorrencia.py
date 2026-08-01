"""
Etapa 2 — item 6: concorrência e transações.

Cenário do enunciado: duas transações tentam, ao mesmo tempo, escalar o
MESMO residente para o MESMO dia/turno/unidade (só o preceptor muda entre
as duas tentativas).

O problema sem controle de concorrência: as duas transações fariam
"checa se já existe conflito → se não existe, insere" de forma
independente. Como o SELECT de checagem de cada uma roda ANTES do INSERT
da outra, as duas podem ler "sem conflito" e seguir para o INSERT. O
UNIQUE(id_unidade, dia_semana, turno, id_residente) do banco ainda impede
a inconsistência final, mas quem perde a corrida recebe um IntegrityError
cru do driver — não um erro de negócio tratável.

Solução aqui: LOCK PESSIMISTA via `SELECT ... FOR UPDATE` na linha do
RESIDENTE antes da checagem. A primeira transação a chegar trava a linha
e só libera no commit/rollback; a segunda fica bloqueada esperando — e
quando acorda, já enxerga a escala recém-criada pela primeira e é
rejeitada de forma limpa, com uma exceção de negócio.

Rodar a demo (schema + seeds precisam estar carregados):
    python -m src.etapa2.concorrencia
"""
import threading
import time
from datetime import datetime

from sqlalchemy import select, delete

from src.etapa2.models import Session, Residente, Preceptor, Unidade, Escala


class ConflitoEscalaError(Exception):
    """Levantado quando o residente já está escalado nesse dia/turno/unidade."""


def _log(msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] [{threading.current_thread().name}] {msg}")


def escalar_residente_com_lock(id_unidade, dia_semana, turno, id_residente, id_preceptor,
                                atraso_simulado=0.0):
    """
    Cria uma ESCALA para (id_unidade, dia_semana, turno, id_residente),
    serializando tentativas concorrentes com o mesmo residente via lock
    pessimista (`SELECT ... FOR UPDATE`) na linha de RESIDENTE.

    atraso_simulado: segundos de "trabalho" entre travar a linha e
    commitar — só existe para deixar o race window visível nos logs
    da demo (sem isso, a corrida seria rápida demais para observar).
    """
    with Session.begin() as s:
        _log(f"tentando travar a linha do residente {id_residente}…")
        residente = s.execute(
            select(Residente).where(Residente.id_pessoa == id_residente).with_for_update()
        ).scalar_one_or_none()
        if not residente:
            raise ValueError("residente não encontrado")
        _log("lock adquirido — checando conflito de escala…")

        if atraso_simulado:
            time.sleep(atraso_simulado)

        conflito = s.execute(
            select(Escala).where(
                Escala.id_unidade == id_unidade,
                Escala.dia_semana == dia_semana,
                Escala.turno == turno,
                Escala.id_residente == id_residente,
            )
        ).first()
        if conflito:
            _log("CONFLITO — residente já escalado nesse dia/turno/unidade. Abortando.")
            raise ConflitoEscalaError(
                f"Residente {id_residente} já está escalado em {dia_semana}/{turno} nessa unidade."
            )

        nova = Escala(
            id_unidade=id_unidade, dia_semana=dia_semana, turno=turno,
            id_residente=id_residente, id_preceptor=id_preceptor,
        )
        s.add(nova)
        s.flush()
        _log(f"OK — escala {nova.id_escala} criada. Commitando (lock será liberado agora).")
        return nova.id_escala
    # ao sair do `with Session.begin()` o commit acontece e o lock cai.


def demo(id_unidade, dia_semana, turno, id_residente, id_preceptor_a, id_preceptor_b):
    """
    Dispara duas threads quase simultâneas tentando escalar o MESMO
    residente no MESMO dia/turno/unidade, cada uma com um preceptor
    diferente. Esperado: uma cria a escala, a outra é rejeitada com
    ConflitoEscalaError — nunca as duas, e nunca um erro cru de banco.
    """
    resultados = {}

    def tentativa(nome, id_preceptor):
        try:
            id_escala = escalar_residente_com_lock(
                id_unidade, dia_semana, turno, id_residente, id_preceptor,
                atraso_simulado=0.5,
            )
            resultados[nome] = ("sucesso", id_escala)
        except ConflitoEscalaError as e:
            resultados[nome] = ("rejeitada", str(e))

    t1 = threading.Thread(target=tentativa, args=("thread-A", id_preceptor_a), name="thread-A")
    t2 = threading.Thread(target=tentativa, args=("thread-B", id_preceptor_b), name="thread-B")

    t1.start()
    time.sleep(0.05)  # A chega um instante antes, mas ambas competem pelo mesmo lock
    t2.start()
    t1.join()
    t2.join()

    print("\n--- resultado final ---")
    for nome, r in resultados.items():
        print(f"{nome}: {r}")

    sucessos = [r for r in resultados.values() if r[0] == "sucesso"]
    rejeitadas = [r for r in resultados.values() if r[0] == "rejeitada"]
    assert len(sucessos) == 1 and len(rejeitadas) == 1, (
        "esperado exatamente 1 sucesso e 1 rejeição — o lock não serializou como deveria"
    )
    print("\nOK — o lock pessimista impediu a dupla escala do mesmo residente no mesmo slot.")
    return resultados


if __name__ == "__main__":
    with Session() as s:
        residente = s.execute(select(Residente)).scalars().first()
        preceptores = s.execute(select(Preceptor)).scalars().all()
        unidade = s.execute(select(Unidade)).scalars().first()

    if not residente or len(preceptores) < 2 or not unidade:
        raise SystemExit(
            "Banco precisa de pelo menos 1 residente, 2 preceptores e 1 unidade "
            "(rode os seeds em sql/dml antes de executar a demo)."
        )

    DIA, TURNO = "segunda", "noite"

    # limpa qualquer escala pré-existente nesse exato slot para a demo ser
    # determinística (senão as duas threads podem ser rejeitadas por um
    # conflito antigo, em vez de rejeitarem uma à outra).
    with Session.begin() as s:
        s.execute(
            delete(Escala).where(
                Escala.id_unidade == unidade.id_unidade,
                Escala.dia_semana == DIA,
                Escala.turno == TURNO,
                Escala.id_residente == residente.id_pessoa,
            )
        )

    demo(
        id_unidade=unidade.id_unidade,
        dia_semana=DIA,
        turno=TURNO,
        id_residente=residente.id_pessoa,
        id_preceptor_a=preceptores[0].id_pessoa,
        id_preceptor_b=preceptores[1].id_pessoa,
    )