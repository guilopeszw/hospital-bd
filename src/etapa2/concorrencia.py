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

Duas soluções, para comparar as duas famílias de controle de concorrência:

1. LOCK PESSIMISTA — `escalar_residente_com_lock()`: `SELECT ... FOR UPDATE`
   na linha do RESIDENTE antes da checagem. A primeira transação trava a
   linha e só libera no commit; a segunda fica BLOQUEADA esperando, e quando
   acorda já enxerga a escala criada e é rejeitada de forma limpa. Serializa
   ANTES do conflito acontecer.

2. CONTROLE OTIMISTA — `escalar_residente_otimista()`: NÃO segura lock
   nenhum. As duas transações seguem em paralelo e tentam o INSERT; a
   `UNIQUE(id_unidade, dia_semana, turno, id_residente)` é o detector de
   conflito. Quem perde a corrida recebe o `IntegrityError`, que é capturado
   e traduzido para a mesma exceção de negócio. Detecta o conflito DEPOIS,
   no momento da escrita — mais concorrência, ao custo de retrabalho de quem
   perde.

Rodar as duas demos (schema + seeds precisam estar carregados):
    python -m src.etapa2.concorrencia
"""
import threading
import time
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

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


def escalar_residente_otimista(id_unidade, dia_semana, turno, id_residente, id_preceptor,
                               atraso_simulado=0.0):
    """
    Versão OTIMISTA: não trava linha nenhuma. Faz a checagem best-effort e
    tenta o INSERT; se outra transação inseriu o mesmo slot no meio do
    caminho, a UNIQUE dispara `IntegrityError` no commit/flush — que é
    capturado e traduzido para `ConflitoEscalaError` (mesma regra de negócio
    do caminho pessimista, sem vazar erro cru do driver).

    atraso_simulado: mesmo papel da versão pessimista — alarga o race window
    entre a checagem e o INSERT para o conflito ficar visível nos logs.
    """
    try:
        with Session.begin() as s:
            _log("sem lock — checando conflito (best-effort) e tentando inserir…")
            conflito = s.execute(
                select(Escala).where(
                    Escala.id_unidade == id_unidade,
                    Escala.dia_semana == dia_semana,
                    Escala.turno == turno,
                    Escala.id_residente == id_residente,
                )
            ).first()
            if conflito:
                _log("CONFLITO já visível na checagem. Abortando.")
                raise ConflitoEscalaError(
                    f"Residente {id_residente} já está escalado em {dia_semana}/{turno} nessa unidade."
                )

            if atraso_simulado:
                time.sleep(atraso_simulado)  # janela onde a outra thread pode inserir

            nova = Escala(
                id_unidade=id_unidade, dia_semana=dia_semana, turno=turno,
                id_residente=id_residente, id_preceptor=id_preceptor,
            )
            s.add(nova)
            s.flush()  # aqui a UNIQUE é checada; se a outra ganhou, estoura IntegrityError
            _log(f"OK — escala {nova.id_escala} criada. Commitando.")
            return nova.id_escala
    except IntegrityError:
        # Perdeu a corrida: a outra transação inseriu o mesmo slot primeiro.
        _log("CONFLITO detectado na escrita (UNIQUE) — perdeu a corrida. Rejeitando.")
        raise ConflitoEscalaError(
            f"Residente {id_residente} já está escalado em {dia_semana}/{turno} nessa unidade."
        )


def _rodar_demo(fn, nome_estrategia, id_unidade, dia_semana, turno,
                id_residente, id_preceptor_a, id_preceptor_b, atraso=0.5):
    """Dispara duas threads quase simultâneas usando a função de escala `fn`.
    Esperado sempre: exatamente 1 sucesso e 1 rejeição de negócio."""
    print(f"\n===== DEMO: {nome_estrategia} =====")
    resultados = {}

    def tentativa(nome, id_preceptor):
        try:
            id_escala = fn(id_unidade, dia_semana, turno, id_residente, id_preceptor,
                           atraso_simulado=atraso)
            resultados[nome] = ("sucesso", id_escala)
        except ConflitoEscalaError as e:
            resultados[nome] = ("rejeitada", str(e))

    t1 = threading.Thread(target=tentativa, args=("thread-A", id_preceptor_a), name="thread-A")
    t2 = threading.Thread(target=tentativa, args=("thread-B", id_preceptor_b), name="thread-B")
    t1.start()
    time.sleep(0.05)
    t2.start()
    t1.join()
    t2.join()

    print("\n--- resultado final ---")
    for nome, r in resultados.items():
        print(f"{nome}: {r}")

    sucessos = [r for r in resultados.values() if r[0] == "sucesso"]
    rejeitadas = [r for r in resultados.values() if r[0] == "rejeitada"]
    assert len(sucessos) == 1 and len(rejeitadas) == 1, (
        f"[{nome_estrategia}] esperado exatamente 1 sucesso e 1 rejeição"
    )
    print(f"\nOK — {nome_estrategia}: impediu a dupla escala do mesmo residente no mesmo slot.")
    return resultados


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


def demo_otimista(id_unidade, dia_semana, turno, id_residente, id_preceptor_a, id_preceptor_b):
    """Mesma disputa, mas com controle OTIMISTA (sem lock; UNIQUE detecta o
    conflito na escrita). Esperado idêntico: 1 sucesso, 1 rejeição."""
    return _rodar_demo(
        escalar_residente_otimista, "controle otimista (sem lock, UNIQUE detecta)",
        id_unidade, dia_semana, turno, id_residente, id_preceptor_a, id_preceptor_b,
    )


def _limpar_slot(id_unidade, dia_semana, turno, id_residente):
    with Session.begin() as s:
        s.execute(
            delete(Escala).where(
                Escala.id_unidade == id_unidade,
                Escala.dia_semana == dia_semana,
                Escala.turno == turno,
                Escala.id_residente == id_residente,
            )
        )


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

    args = dict(
        id_unidade=unidade.id_unidade,
        id_residente=residente.id_pessoa,
        id_preceptor_a=preceptores[0].id_pessoa,
        id_preceptor_b=preceptores[1].id_pessoa,
    )

    # Cada estratégia usa um slot próprio, limpo antes, para a disputa ser
    # sempre entre as duas threads — não contra uma escala antiga.
    _limpar_slot(unidade.id_unidade, "segunda", "noite", residente.id_pessoa)
    demo(dia_semana="segunda", turno="noite", **args)

    _limpar_slot(unidade.id_unidade, "terca", "noite", residente.id_pessoa)
    demo_otimista(dia_semana="terca", turno="noite", **args)