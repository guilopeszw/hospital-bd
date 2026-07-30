"""
Operações da Etapa 1 reimplementadas via ORM (Etapa 2 — item 4).

Tudo aqui usa a DSL do SQLAlchemy (select/func/session), não SQL cru.
Demonstra: mapeamento (models.py), sessões/transações, DSL de consulta,
relacionamentos com lazy vs eager loading.

Rodar o self-check:  python -m src.etapa2.crud_orm
"""
from datetime import datetime

from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from src.etapa2.models import (
    Session, Pessoa, Paciente, Profissional, Preceptor, Residente,
    Unidade, Procedimento, Atendimento, ProcedimentoRealizado, Faturamento,
)


# ---- CRUD / consultas básicas -----------------------------------

def inserir_atendimento(data_hora, duracao, id_paciente, id_residente,
                        id_preceptor, id_unidade):
    """Insere um atendimento validando as FKs via ORM (get). Transação
    via context manager: commit no fim, rollback se estourar."""
    with Session.begin() as s:
        if not s.get(Paciente, id_paciente):
            raise ValueError("paciente não encontrado")
        if not s.get(Residente, id_residente):
            raise ValueError("residente não encontrado")
        if not s.get(Preceptor, id_preceptor):
            raise ValueError("preceptor não encontrado")
        if not s.get(Unidade, id_unidade):
            raise ValueError("unidade não encontrada")
        at = Atendimento(
            data_hora=data_hora, duracao_minutos=duracao,
            id_paciente=id_paciente, id_residente=id_residente,
            id_preceptor=id_preceptor, id_unidade=id_unidade,
        )
        s.add(at)
        s.flush()
        return at.id_atendimento


def listar_atendimentos_paciente(id_paciente):
    """Atendimentos de um paciente, mais recentes primeiro. Eager loading
    (selectinload) de residente/preceptor/unidade para não disparar uma
    query por linha ao ler os nomes (evita N+1)."""
    with Session() as s:
        stmt = (
            select(Atendimento)
            .where(Atendimento.id_paciente == id_paciente)
            .order_by(Atendimento.data_hora.desc())
            .options(
                selectinload(Atendimento.residente).selectinload(Residente.profissional).selectinload(Profissional.pessoa),
                selectinload(Atendimento.preceptor).selectinload(Preceptor.profissional).selectinload(Profissional.pessoa),
                selectinload(Atendimento.unidade),
            )
        )
        out = []
        for a in s.scalars(stmt):
            out.append({
                "id_atendimento": a.id_atendimento,
                "data_hora": a.data_hora,
                "duracao_minutos": a.duracao_minutos,
                "residente": a.residente.profissional.pessoa.nome,
                "preceptor": a.preceptor.profissional.pessoa.nome,
                "unidade": a.unidade.nome,
            })
        return out


def listar_procedimentos_atendimento(id_atendimento):
    """Procedimentos realizados num atendimento. Lazy loading padrão em
    ProcedimentoRealizado.procedimento (uma query ao acessar .procedimento)."""
    with Session() as s:
        stmt = select(ProcedimentoRealizado).where(
            ProcedimentoRealizado.id_atendimento == id_atendimento
        )
        return [
            {
                "procedimento": pr.procedimento.nome,
                "nivel_risco": pr.procedimento.nivel_risco,
                "quantidade": pr.quantidade,
                "tempo_real_minutos": pr.tempo_real_minutos,
                "observacao": pr.observacao,
            }
            for pr in s.scalars(stmt)
        ]


def atualizar_paciente(id_paciente, novo_convenio=None, novas_alergias=None):
    """UPDATE via ORM: carrega, muda atributo, commit."""
    with Session.begin() as s:
        pac = s.get(Paciente, id_paciente)
        if not pac:
            raise ValueError("paciente não encontrado")
        if novo_convenio is not None:
            pac.num_convenio = novo_convenio
        if novas_alergias is not None:
            pac.alergias = novas_alergias
        return pac.id_pessoa


def remover_procedimento_realizado(id_atendimento, id_procedimento):
    """Remove só se não houver faturamento associado. Retorna nº de linhas
    apagadas (0 = bloqueado/não existe)."""
    with Session.begin() as s:
        existe_fat = s.scalar(
            select(func.count())
            .select_from(Faturamento)
            .where(Faturamento.id_atendimento == id_atendimento,
                   Faturamento.id_procedimento == id_procedimento)
        )
        if existe_fat:
            return 0
        res = s.execute(
            delete(ProcedimentoRealizado).where(
                ProcedimentoRealizado.id_atendimento == id_atendimento,
                ProcedimentoRealizado.id_procedimento == id_procedimento,
            )
        )
        return res.rowcount


def tempo_medio_por_residente():
    """AVG(duracao) por residente via func.avg + group_by. LEFT JOIN (outerjoin)
    para incluir residente sem atendimento."""
    with Session() as s:
        stmt = (
            select(Pessoa.nome,
                   func.round(func.avg(Atendimento.duracao_minutos), 1).label("tempo_medio"),
                   func.count(Atendimento.id_atendimento).label("total"))
            .select_from(Residente)
            .join(Pessoa, Pessoa.id_pessoa == Residente.id_pessoa)
            .outerjoin(Atendimento, Atendimento.id_residente == Residente.id_pessoa)
            .group_by(Residente.id_pessoa, Pessoa.nome)
            .order_by(func.avg(Atendimento.duracao_minutos).desc().nullslast())
        )
        return [{"residente": n, "tempo_medio_minutos": t, "total_atendimentos": c}
                for n, t, c in s.execute(stmt)]


# ---- Consultas analíticas ---------------------------------------

def ranking_residentes():
    with Session() as s:
        stmt = (
            select(Pessoa.nome, func.count(Atendimento.id_atendimento).label("total"))
            .select_from(Residente)
            .join(Pessoa, Pessoa.id_pessoa == Residente.id_pessoa)
            .outerjoin(Atendimento, Atendimento.id_residente == Residente.id_pessoa)
            .group_by(Residente.id_pessoa, Pessoa.nome)
            .order_by(func.count(Atendimento.id_atendimento).desc(), Pessoa.nome)
        )
        return [{"residente": n, "total_atendimentos": t} for n, t in s.execute(stmt)]


def preceptores_mais_atendimentos_mes(ano, mes):
    with Session() as s:
        stmt = (
            select(Pessoa.nome, func.count(Atendimento.id_atendimento).label("total"))
            .select_from(Atendimento)
            .join(Preceptor, Preceptor.id_pessoa == Atendimento.id_preceptor)
            .join(Pessoa, Pessoa.id_pessoa == Preceptor.id_pessoa)
            .where(func.extract("year", Atendimento.data_hora) == ano,
                   func.extract("month", Atendimento.data_hora) == mes)
            .group_by(Pessoa.nome)
            .having(func.count(Atendimento.id_atendimento) > 5)
            .order_by(func.count(Atendimento.id_atendimento).desc())
        )
        return [{"preceptor": n, "total_atendimentos": t} for n, t in s.execute(stmt)]


def pacientes_sem_procedimento_risco_alto():
    """Pacientes sem nenhum procedimento ALTO — NOT EXISTS via ~.any() da DSL."""
    with Session() as s:
        sub = (
            select(ProcedimentoRealizado.id_atendimento)
            .join(Procedimento, Procedimento.id_procedimento == ProcedimentoRealizado.id_procedimento)
            .join(Atendimento, Atendimento.id_atendimento == ProcedimentoRealizado.id_atendimento)
            .where(Atendimento.id_paciente == Paciente.id_pessoa,
                   Procedimento.nivel_risco == "ALTO")
        )
        stmt = (
            select(Pessoa.nome, Paciente.num_convenio)
            .join(Pessoa, Pessoa.id_pessoa == Paciente.id_pessoa)
            .where(~sub.exists())
            .order_by(Pessoa.nome)
        )
        return [{"paciente": n, "num_convenio": c} for n, c in s.execute(stmt)]


def _demo():
    """Self-check: exercita as operações contra o banco populado.
    Requer o schema + seeds carregados. Não altera dados de forma
    permanente (usa rollback no teste de escrita)."""
    print("ranking_residentes:", ranking_residentes())
    print("tempo_medio_por_residente:", tempo_medio_por_residente())
    print("preceptores 2025/6:", preceptores_mais_atendimentos_mes(2025, 6))
    print("sem risco ALTO:", pacientes_sem_procedimento_risco_alto())
    assert len(ranking_residentes()) == 5, "esperado 5 residentes"
    print("OK")


if __name__ == "__main__":
    _demo()
