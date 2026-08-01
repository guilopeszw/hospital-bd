"""
Etapa 2 — item 5: consultas avançadas via ORM.

As três consultas exigidas no enunciado, além das que já foram
reimplementadas em crud_orm.py (que cobre só o que já existia na
Etapa 1). Tudo em DSL do SQLAlchemy — nenhuma delas usa SQL cru.

Rodar o self-check:  python -m src.etapa2.consultas_avancadas
"""
from sqlalchemy import select, func, case
from sqlalchemy.orm import aliased, selectinload

from src.etapa2.models import (
    Session, Pessoa, Paciente, Profissional, Preceptor, Residente,
    Atendimento, Procedimento, ProcedimentoRealizado,
)


def preceptores_supervisionaram_flamenguistas():
    """
    Preceptores que supervisionaram (em qualquer atendimento) um residente
    que atendeu ao menos um paciente flamenguista (is_flamengo = TRUE).

    Pessoa aparece duas vezes na consulta — uma para o preceptor, outra para
    o paciente — por isso o `aliased` na Pessoa do lado do preceptor: sem
    isso o SQLAlchemy não saberia distinguir os dois JOINs na mesma tabela.
    """
    PessoaPreceptor = aliased(Pessoa)
    with Session() as s:
        stmt = (
            select(PessoaPreceptor.nome)
            .distinct()
            .select_from(Atendimento)
            .join(Preceptor, Preceptor.id_pessoa == Atendimento.id_preceptor)
            .join(PessoaPreceptor, PessoaPreceptor.id_pessoa == Preceptor.id_pessoa)
            .join(Paciente, Paciente.id_pessoa == Atendimento.id_paciente)
            .join(Pessoa, Pessoa.id_pessoa == Paciente.id_pessoa)
            .where(Pessoa.is_flamengo.is_(True))
            .order_by(PessoaPreceptor.nome)
        )
        return [nome for (nome,) in s.execute(stmt)]


def ultimo_atendimento_por_paciente():
    """
    Para cada paciente: data/hora, residente, preceptor e a lista de
    procedimentos do seu atendimento mais recente.

    Estratégia: uma subquery agrega MAX(data_hora) por paciente; o SELECT
    principal junta ATENDIMENTO de volta por (id_paciente, data_hora) —
    dá o mesmo resultado de uma window function (ROW_NUMBER), mas fica
    mais direto de ler na DSL do SQLAlchemy. Único caso de borda: se um
    paciente tiver dois atendimentos empatados no mesmo segundo, os dois
    aparecem (raro o bastante para não justificar a complexidade extra
    de uma window function aqui).

    Eager loading (selectinload) em cascata evita N+1 ao ler nome do
    residente/preceptor (que passam por PROFISSIONAL → PESSOA) e a lista
    de procedimentos de cada atendimento.
    """
    with Session() as s:
        ultima_data = (
            select(
                Atendimento.id_paciente,
                func.max(Atendimento.data_hora).label("ultima_data"),
            )
            .group_by(Atendimento.id_paciente)
            .subquery()
        )
        stmt = (
            select(Atendimento)
            .join(
                ultima_data,
                (Atendimento.id_paciente == ultima_data.c.id_paciente)
                & (Atendimento.data_hora == ultima_data.c.ultima_data),
            )
            .options(
                selectinload(Atendimento.paciente).selectinload(Paciente.pessoa),
                selectinload(Atendimento.residente)
                    .selectinload(Residente.profissional).selectinload(Profissional.pessoa),
                selectinload(Atendimento.preceptor)
                    .selectinload(Preceptor.profissional).selectinload(Profissional.pessoa),
                selectinload(Atendimento.procedimentos)
                    .selectinload(ProcedimentoRealizado.procedimento),
            )
            .order_by(Atendimento.data_hora.desc())
        )
        out = []
        for a in s.scalars(stmt):
            out.append({
                "paciente": a.paciente.pessoa.nome,
                "data_hora": a.data_hora,
                "residente": a.residente.profissional.pessoa.nome,
                "preceptor": a.preceptor.profissional.pessoa.nome,
                "procedimentos": [pr.procedimento.nome for pr in a.procedimentos],
            })
        return out


def percentual_procedimentos_alto_risco_por_residente():
    """
    Para cada residente: total de procedimentos realizados (soma de
    `quantidade`) e qual fatia disso é de nível de risco ALTO.

    Usa outerjoin em toda a cadeia (Atendimento → ProcedimentoRealizado →
    Procedimento) para que um residente sem nenhum procedimento ainda
    apareça no relatório com 0/0% — mesmo espírito do LEFT JOIN usado em
    `tempo_medio_por_residente` no crud_orm.py. `case()` soma só a
    quantidade dos procedimentos ALTO; a divisão é feita em Python para
    tratar o caso total=0 sem se preocupar com o dialeto do banco.
    """
    with Session() as s:
        total_col = func.coalesce(func.sum(ProcedimentoRealizado.quantidade), 0)
        alto_col = func.coalesce(
            func.sum(
                case((Procedimento.nivel_risco == "ALTO", ProcedimentoRealizado.quantidade), else_=0)
            ),
            0,
        )
        stmt = (
            select(Pessoa.nome, total_col.label("total"), alto_col.label("alto_risco"))
            .select_from(Residente)
            .join(Pessoa, Pessoa.id_pessoa == Residente.id_pessoa)
            .outerjoin(Atendimento, Atendimento.id_residente == Residente.id_pessoa)
            .outerjoin(ProcedimentoRealizado, ProcedimentoRealizado.id_atendimento == Atendimento.id_atendimento)
            .outerjoin(Procedimento, Procedimento.id_procedimento == ProcedimentoRealizado.id_procedimento)
            .group_by(Residente.id_pessoa, Pessoa.nome)
            .order_by(Pessoa.nome)
        )
        out = []
        for nome, total, alto in s.execute(stmt):
            pct = round((alto / total) * 100, 1) if total else 0.0
            out.append({
                "residente": nome,
                "total_procedimentos": int(total),
                "alto_risco": int(alto),
                "percentual_alto_risco": pct,
            })
        return out


def _demo():
    """Self-check: exercita as três consultas contra o banco populado."""
    print("preceptores com residentes que atenderam flamenguistas:")
    print(" ", preceptores_supervisionaram_flamenguistas())

    print("\núltimo atendimento por paciente:")
    for linha in ultimo_atendimento_por_paciente():
        print(" ", linha)

    print("\n% de procedimentos de alto risco por residente:")
    for linha in percentual_procedimentos_alto_risco_por_residente():
        print(" ", linha)

    print("\nOK")


if __name__ == "__main__":
    _demo()