# Sistema de Gestão Hospitalar — HU Dra. Yuska Maritan Brito

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

---

## Sobre o Projeto

Sistema acadêmico de gestão hospitalar, desenvolvido como projeto da disciplina de Banco de Dados. Cobre da modelagem conceitual (DER) à implementação física em PostgreSQL: DDL/DML, SQL avançado, triggers, stored procedures, views e ORM (SQLAlchemy).

## Etapas

**Etapa 1 — Fundamentos (SQL puro)** — DER, normalização até 3FN, 12 tabelas com constraints, seeds, CRUD e consultas analíticas, CLI (`argparse`) e testes `pytest`.

**Etapa 2 — Funcionalidades avançadas** — stored procedures com transações, triggers (sobreposição de escala, auditoria, média de procedimentos), views analíticas, migração para SQLAlchemy 2.x, consultas avançadas via ORM e concorrência com lock pessimista (`SELECT ... FOR UPDATE`).

▶ **Vídeo da Etapa 2:** <https://youtu.be/udv6v6rAX9c>

## Stack

| Componente | Tecnologia |
|---|---|
| Banco | PostgreSQL 16 (Alpine) |
| Linguagem | Python 3.12+ |
| Conector / ORM | psycopg2 · SQLAlchemy 2.x |
| Webapp | Flask + flask-cors · HTML/CSS/JS puro |
| Testes | pytest |
| Container | Docker + Docker Compose |
| Modelagem | Mermaid (DER) |

---

## Quickstart

Pré-requisitos: **Docker** e **Python 3.12+**. Instalação por SO em [`docs/06-infraestrutura/01-docker.md`](docs/06-infraestrutura/01-docker.md).

### 1. Subir o banco

```bash
cd docker && docker compose up -d
```

PostgreSQL em `localhost:5433`, usuário `postgres`, senha `password`, db `hospital_db`. Parar: `docker compose down`.

### 2. Aplicar schema + seeds + Etapa 2

```bash
for f in sql/ddl/*.sql sql/dml/*.sql sql/procedures/*.sql sql/triggers/*.sql sql/views/*.sql; do
  psql "postgresql://postgres:password@localhost:5433/hospital_db" -f "$f"
done
```

DDL/DML são numerados por dependência — o laço respeita a ordem. Procedures/triggers/views são da Etapa 2: a CLI da Etapa 1 funciona sem elas; ORM, consultas avançadas, concorrência e webapp exigem o schema completo.

### 3. Ambiente Python

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Testes

```bash
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" pytest
```

Os testes criam schema próprio do zero (fixture em `tests/conftest.py`) — não é preciso popular o banco antes.

### 5. CLI

- **Interativa (menu):** `python -m src.etapa1.cli_interactive`
- **Args (um comando por vez):** `python -m src.etapa1.atendimento_crud <comando>`

```bash
python -m src.etapa1.atendimento_crud ranking-residentes
python -m src.etapa1.atendimento_crud inserir-atendimento "2025-07-01 10:00" 30 <id_paciente> <id_residente> <id_preceptor>
python -m src.etapa1.atendimento_crud cadastrar-paciente "Nome do Paciente" 12345678901 1990-05-20 --convenio UNIMED-123
```

Use `listar` para descobrir UUIDs e `--help` para detalhes de cada subcomando. Referência completa: [`docs/05-aplicacao/01-cli.md`](docs/05-aplicacao/01-cli.md).

### 6. Webapp (API Flask + painel web)

Front-end opcional: API REST em Flask + painel em HTML/CSS/JS puro (sem build step).

**Pré-requisitos:** passos 1 e 2 já executados (banco no ar + schema/seeds completos) e dependências instaladas (passo 3 — o `requirements.txt` da raiz já cobre Flask, flask-cors, psycopg2 e sqlalchemy).

**1. Subir a API:**

```bash
cd webapp/api
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" python app.py
```

Sobe em `http://localhost:5055` (env `PORT` sobrescreve). Verifique com `curl http://localhost:5055/api/health` — deve responder com status do banco.

> **Porta 5055, não 5000:** no macOS, o AirPlay Receiver ocupa a `5000` e responde `403` a tudo — por isso a API usa `5055`, e o front aponta pra ela.

**2. Abrir o painel:** abrir `webapp/frontend/index.html` no navegador (arquivo estático, não precisa de servidor). O front usa `fetch()` para `http://localhost:5055/api/...` (CORS liberado via `flask-cors`).

**O que o painel cobre:** dashboard, CRUD de pacientes/atendimentos/escalas, faturamento e os indicadores analíticos (incluindo as 3 views e as consultas via ORM da Etapa 2).

Detalhes de rotas, segurança (XSS) e arquitetura: [`docs/05-aplicacao/04-webapp.md`](docs/05-aplicacao/04-webapp.md).

---

## Estrutura do Repositório

```
hospital-bd/
├── docker/            # PostgreSQL 16 em container (docker-compose.yml)
├── sql/
│   ├── ddl/           # CREATE TABLE (01_enums.sql → 14_internacao.sql)
│   ├── dml/           # Seeds (01_pacientes → 08_internacao)
│   ├── queries/       # SQL puro: CRUD + consultas analíticas
│   ├── procedures/    # Stored procedures (Etapa 2)
│   ├── triggers/      # Triggers (Etapa 2)
│   └── views/         # Views analíticas (Etapa 2)
├── src/
│   ├── etapa1/        # CLI + CRUD (psycopg2)
│   └── etapa2/        # SQLAlchemy: models, crud_orm, consultas, concorrência
├── webapp/
│   ├── api/           # Flask: app.py, db.py, routes/
│   └── frontend/      # HTML/CSS/JS puro
├── tests/             # pytest — schema isolado por sessão
├── docs/              # Documentação detalhada
└── requirements.txt
```

---

## Documentação

| Área | Documentos |
|---|---|
| Projeto | [Especificação](docs/00-especificacao.md) · [Plano de trabalho](docs/01-plano-de-trabalho.md) · [Checklist](docs/02-checklist.md) |
| Modelagem | [DER](docs/03-modelagem/01-der.md) · [Normalização 3FN](docs/03-modelagem/02-normalizacao.md) · [Cardinalidades](docs/03-modelagem/03-justificativa_cardinalidades.md) |
| Banco | [DDL](docs/04-banco/01-ddl.md) · [DML](docs/04-banco/02-dml.md) · [Queries](docs/04-banco/03-queries.md) · [Procedures](docs/04-banco/04-procedures.md) · [Views](docs/04-banco/05-views.md) · [Triggers](docs/04-banco/06-triggers.md) |
| Aplicação | [CLI](docs/05-aplicacao/01-cli.md) · [Testes](docs/05-aplicacao/02-testes.md) · [ORM](docs/05-aplicacao/03-orm.md) · [Webapp](docs/05-aplicacao/04-webapp.md) · [Consultas avançadas](docs/05-aplicacao/05-consultas_avancadas.md) · [Concorrência](docs/05-aplicacao/06-concorrencia.md) |
| Infra | [Docker](docs/06-infraestrutura/01-docker.md) |

---

## Equipe — Contribuidores

| Nome | GitHub |
|------|--------|
| Gabriela Zeviani | [@Gabi-Zeviani](https://github.com/Gabi-Zeviani) |
| Guilherme Lopes | [@guilopeszw](https://github.com/guilopeszw) |
| João Bosco Duarte | [@JoaoBoscoDuarte](https://github.com/JoaoBoscoDuarte) |

---

## Licença

Distribuído sob licença MIT. Veja [`LICENSE`](./LICENSE).
