# ORM — Camada SQLAlchemy (Etapa 2)

## Visão Geral

Item 4 da Etapa 2: as operações da Etapa 1 reimplementadas via ORM, usando a DSL
do SQLAlchemy 2.0 — não SQL cru. A camada SQL pura da Etapa 1
([`01-cli.md`](01-cli.md)) continua existindo; esta é a versão orientada a objetos.

**Arquivos:**

| Arquivo | Papel |
|---|---|
| [`../../src/etapa2/models.py`](../../src/etapa2/models.py) | Classes mapeadas + relacionamentos + engine/sessão |
| [`../../src/etapa2/crud_orm.py`](../../src/etapa2/crud_orm.py) | Operações via DSL; self-check em `__main__` |

**Dependência:** `sqlalchemy==2.0.51` (em `requirements.txt`).

---

## Como rodar

```bash
pip install -r requirements.txt
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" \
  python -m src.etapa2.crud_orm      # self-check: roda as consultas e valida
```

O `models.py` converte o DSN psycopg2 usado no resto do projeto
(`dbname=... user=...`) para a URL do SQLAlchemy
(`postgresql+psycopg2://...`); a env `SQLALCHEMY_URL` sobrescreve se necessário.

---

## O que a Etapa 2 exige demonstrar

| Requisito | Onde |
|---|---|
| Mapeamento objeto-relacional | `models.py` — 13 classes com `Mapped`/`mapped_column` |
| Sessões e transações | `crud_orm.py` — `Session.begin()` (commit/rollback automáticos) |
| Consultas via DSL (não SQL cru) | `select()`, `func.avg`, `.group_by`, `.having`, `~sub.exists()` |
| Relacionamentos lazy vs eager | `selectinload()` em `listar_atendimentos_paciente` (eager, evita N+1); lazy default em `ProcedimentoRealizado.procedimento` |

## Operações implementadas

`inserir_atendimento`, `listar_atendimentos_paciente`,
`listar_procedimentos_atendimento`, `atualizar_paciente`,
`remover_procedimento_realizado` (bloqueia se houver faturamento),
`tempo_medio_por_residente`, `ranking_residentes`,
`preceptores_mais_atendimentos_mes`, `pacientes_sem_procedimento_risco_alto`.

## Detalhes notáveis

- **Eager vs lazy:** `listar_atendimentos_paciente` usa `selectinload` encadeado
  (residente→profissional→pessoa, idem preceptor, e unidade) para trazer os nomes
  sem disparar uma query por linha. `listar_procedimentos_atendimento` deixa o
  lazy default agir ao acessar `.procedimento`.
- **`NOT EXISTS` na DSL:** `pacientes_sem_procedimento_risco_alto` usa
  `~subquery.exists()` em vez de SQL cru.
- **Enums e UUID:** mapeados como `str` (o driver faz o cast), para casar com os
  UUIDs usados nos seeds e testes.
