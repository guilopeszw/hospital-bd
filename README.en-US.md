# Hospital Management System — HU Dra. Yuska Maritan Brito

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

---

## Table of Contents

- [About the Project](#about-the-project)
- [What the Project Covers](#what-the-project-covers)
  - [Stage 1 — Fundamentals (Pure SQL)](#stage-1--fundamentals-pure-sql)
  - [Stage 2 — Advanced Features](#stage-2--advanced-features)
- [Tech Stack](#tech-stack)
- [Dependencies and Installation](#dependencies-and-installation)
  - [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
  - [macOS](#macos)
  - [Windows](#windows)
- [How to Run the Project](#how-to-run-the-project)
  - [1. Start the Database with Docker](#1-start-the-database-with-docker)
  - [2. Populate the Database (DDL + Seeds)](#2-populate-the-database-ddl--seeds)
  - [3. Install Python Dependencies](#3-install-python-dependencies)
  - [4. Run the Tests](#4-run-the-tests)
  - [5. Use the CLI](#5-use-the-cli)
- [Repository Structure](#repository-structure)
- [Documentation](#documentation)
- [Team — Contributors](#team--contributors)
- [License](#license)

---

## About the Project

Academic system for hospital management at **Hospital Universitário Dra. Yuska Maritan Brito**. Developed as the single project for the Database course.

Goal: register people (patients and professionals), manage visits/encounters, procedures, on-call schedules, and generate analytical indicators. The system covers everything from conceptual modeling (ERD) to the physical implementation in PostgreSQL, including normalization up to 3NF, advanced SQL, triggers, stored procedures, views, and ORM usage (SQLAlchemy).

Split into two stages of increasing complexity:

1. **Stage 1** — Relational modeling, DDL/DML, CRUD, and pure SQL queries (no ORM).
2. **Stage 2** — Stored procedures, triggers, views, migration to an ORM (SQLAlchemy), and concurrency handling.

---

## What the Project Covers

### Stage 1 — Fundamentals (Pure SQL)

- **Conceptual and Logical Modeling** — Full ERD, relational model, normalization up to 3NF/BCNF.
- **DDL and Constraints** — Creation of 12 tables with PK, FK, CHECK, NOT NULL, UNIQUE, enums, and UUIDs.
- **Seeds** — Test data: 5+ patients, residents, preceptors, units, encounters, and on-call schedules.
- **CRUD** — Full insert, list, update, and delete operations with validations.
- **Analytical Queries** — Resident ranking, preceptors with the most encounters, on-call shifts per unit, patients without high-risk procedures.
- **CLI** — Command-line interface covering all operations via `argparse`.
- **Automated Tests** — `pytest` suite with a schema isolated per session.

### Stage 2 — Advanced Features

> *Under development — expected to start after Stage 1 is complete.*

- Stored procedures with transactions (full encounter registration, schedule adjustment).
- Triggers (on-call overlap control, encounter auditing, average updates).
- Analytical views (admitted patients, residents without a supervisor, monthly statistics).
- Migration to **SQLAlchemy 2.x** with Alembic.
- Advanced ORM-based queries and concurrency handling with locks.

---

## Tech Stack

| Component     | Technology                                          |
|----------------|-----------------------------------------------------|
| Database       | PostgreSQL 16 (Alpine)                              |
| Language       | Python 3.12+                                        |
| Connector      | psycopg2 2.9                                        |
| ORM (Stage 2)  | SQLAlchemy 2.x + Alembic                             |
| Testing        | pytest                                               |
| Container      | Docker + Docker Compose                              |
| Modeling       | Mermaid (ERD)                                        |

---

## Dependencies and Installation

### Linux (Ubuntu/Debian)

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.12+ and pip
sudo apt install -y python3 python3-pip python3-venv

# Install Docker (if not installed)
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER  # log off/on after this

# Verify installation
python3 --version
docker --version
docker compose version
```

### macOS

```bash
# Install Homebrew (if you don't have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12+
brew install python@3.12

# Install Docker Desktop
brew install --cask docker
# or via: https://docs.docker.com/desktop/install/mac-install/

# Verify
python3 --version
docker --version
docker compose version
```

### Windows

```powershell
# 1. Install Python 3.12+
#    Download: https://www.python.org/downloads/
#    Check "Add Python to PATH" during installation

# 2. Install Docker Desktop
#    Download: https://docs.docker.com/desktop/install/windows-install/
#    WSL 2 backend recommended

# 3. Verify (PowerShell)
python --version
docker --version
docker compose version
```

---

## How to Run the Project

### 1. Start the Database with Docker

```bash
cd docker
docker compose up -d
```

PostgreSQL will be available at:

- **Host:** `localhost`
- **Port:** `5433`
- **User:** `postgres`
- **Password:** `password`
- **Database:** `hospital_db`

To stop: `docker compose down`

### 2. Populate the Database (DDL + Seeds)

```bash
for f in sql/ddl/*.sql sql/dml/*.sql; do
  psql "postgresql://postgres:password@localhost:5433/hospital_db" -f "$f"
done
```

> **Note:** The DDL (`sql/ddl/01`–`12`) and DML (`sql/dml/01`–`07`) files are numbered by dependency. The `for` loop automatically respects the alphabetical/numeric order.

### 3. Install Python Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows PowerShell

pip install -r requirements.txt
```

Dependencies: `psycopg2` (PostgreSQL connector) and `pytest` (testing).

### 4. Run the Tests

```bash
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" pytest
```

The tests create their own schema from scratch (`DROP SCHEMA public CASCADE`) via a fixture in `tests/conftest.py`, isolating each test session — there's no need to populate the database beforehand.

### 5. Use the CLI

Two ways to use it:

**Interactive (menu)** — navigate with the keyboard, no need to memorize commands:
```bash
source .venv/bin/activate
python -m src.etapa1.cli_interactive
```

**Args (direct commands)** — one command per execution:
```bash
# Activate the virtualenv (if not already active)
source .venv/bin/activate

# Rank residents by number of encounters
python -m src.etapa1.atendimento_crud ranking-residentes

# Average encounter time per resident
python -m src.etapa1.atendimento_crud tempo-medio-residente

# On-call shifts per unit for the current month
python -m src.etapa1.atendimento_crud plantoes-mes

# Patients without a HIGH-risk procedure
python -m src.etapa1.atendimento_crud pacientes-sem-risco-alto

# List encounters for a patient
python -m src.etapa1.atendimento_crud atendimentos-paciente <patient_id>

# List procedures for an encounter
python -m src.etapa1.atendimento_crud procedimentos-atendimento <encounter_id>

# Preceptors with more than 5 encounters in a given month
python -m src.etapa1.atendimento_crud preceptores-mes <year> <month>

# Remove a performed procedure (blocked if billing is already associated)
python -m src.etapa1.atendimento_crud remover-procedimento <encounter_id> <procedure_id>

# Update patient data
python -m src.etapa1.atendimento_crud atualizar-paciente <patient_id> --convenio NEW-PLAN

# Insert a new encounter
python -m src.etapa1.atendimento_crud inserir-atendimento "2025-07-01 10:00" 30 <patient_id> <resident_id> <preceptor_id>
```

#### Registrations

The commands above require UUIDs. Use `listar` to discover them without memorizing anything:

```bash
# List records and their UUIDs
python -m src.etapa1.atendimento_crud listar pacientes
python -m src.etapa1.atendimento_crud listar residentes | preceptores | unidades | procedimentos | atendimentos | escalas
```

```bash
# Register a patient (creates PERSON + PATIENT in a single transaction)
python -m src.etapa1.atendimento_crud cadastrar-paciente "Patient Name" 12345678901 1990-05-20 \
    --convenio UNIMED-123 --sangue A+ --alergias "Dipyrone" --telefone 83999990000

# Register a professional (resident requires --ano-residencia; preceptor requires --titulacao)
python -m src.etapa1.atendimento_crud cadastrar-profissional residente "Name" 12345678902 1998-01-10 \
    "CRM/PB 1234" 2025-02-01 Cardiology --ano-residencia R1
python -m src.etapa1.atendimento_crud cadastrar-profissional preceptor "Name" 12345678903 1975-01-10 \
    "CRM/PB 5678" 2010-02-01 Cardiology --titulacao PhD

# Register a unit and an on-call schedule
python -m src.etapa1.atendimento_crud cadastrar-unidade "North Outpatient Clinic" Ambulatorio 15
python -m src.etapa1.atendimento_crud cadastrar-escala <unit_id> monday afternoon <resident_id> <preceptor_id>

# Register a procedure performed during an encounter
python -m src.etapa1.atendimento_crud registrar-procedimento <encounter_id> <procedure_id> 1 15 \
    --obs "No complications"

# Issue billing (from this point on, the procedure can no longer be removed)
python -m src.etapa1.atendimento_crud faturar <encounter_id> <procedure_id> 130.50
```

> **Tip:** For an interactive menu, use `python -m src.etapa1.cli_interactive`. Use `--help` to see details of the direct subcommands:
> ```bash
> python -m src.etapa1.atendimento_crud --help
> python -m src.etapa1.atendimento_crud inserir-atendimento --help
> ```

---

## Repository Structure

```
hospital-bd/
├── docker/
│   └── docker-compose.yml          # PostgreSQL 16 in a container
├── sql/
│   ├── ddl/                        # CREATE TABLE (numbered: 01_enums.sql → 12_faturamento.sql)
│   ├── dml/                        # Seeds (01_pacientes → 07_faturamento)
│   └── queries/                    # Pure SQL queries (CRUD + analytical)
├── src/
│   └── etapa1/
│       └── atendimento_crud.py     # CLI + CRUD functions (psycopg2)
├── tests/
│   ├── conftest.py                 # Fixture: schema isolated per session
│   └── unit/
│       ├── test_core_entities.py   # Tests: Person/Patient
│       └── test_negocio.py         # Tests: business rules
├── docs/
│   ├── 00-especificacao.md         # Full project specification
│   ├── 01-plano-de-trabalho.md     # Planning and backlog
│   ├── 02-checklist.md             # Detailed Stage 1 progress
│   ├── 03-modelagem/
│   │   ├── 01-der.md               # ERD in Mermaid
│   │   └── 02-normalizacao.md      # Formal proof of normalization up to 3NF
│   ├── 04-banco/
│   │   ├── 01-ddl.md               # CREATE TABLE and constraints
│   │   ├── 02-dml.md               # Seeds and test data
│   │   └── 03-queries.md           # CRUD + analytical queries
│   ├── 05-aplicacao/
│   │   ├── 01-cli.md               # CLI reference
│   │   └── 02-testes.md            # Automated tests
│   └── 06-infraestrutura/
│       └── 01-docker.md            # PostgreSQL Docker setup
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

---

## Documentation

| Document | Description |
|-----------|-----------|
| [`docs/00-especificacao.md`](docs/00-especificacao.md) | Full project specification (Stage 1 and 2 requirements) |
| [`docs/01-plano-de-trabalho.md`](docs/01-plano-de-trabalho.md) | Operational planning, backlog, and strategy |
| [`docs/02-checklist.md`](docs/02-checklist.md) | Detailed Stage 1 progress + modeling decisions |
| [`docs/03-modelagem/01-der.md`](docs/03-modelagem/01-der.md) | Entity-Relationship Diagram (Mermaid) |
| [`docs/03-modelagem/02-normalizacao.md`](docs/03-modelagem/02-normalizacao.md) | Formal proof of normalization up to 3NF |
| [`docs/04-banco/01-ddl.md`](docs/04-banco/01-ddl.md) | DDL — schema definition, enums, and constraints |
| [`docs/04-banco/02-dml.md`](docs/04-banco/02-dml.md) | DML — seeds and test data |
| [`docs/04-banco/03-queries.md`](docs/04-banco/03-queries.md) | Queries — CRUD and analytical queries |
| [`docs/05-aplicacao/01-cli.md`](docs/05-aplicacao/01-cli.md) | CLI — complete subcommand reference |
| [`docs/05-aplicacao/02-testes.md`](docs/05-aplicacao/02-testes.md) | Tests — structure, fixtures, and coverage |
| [`docs/06-infraestrutura/01-docker.md`](docs/06-infraestrutura/01-docker.md) | Docker — PostgreSQL setup |

---

## Team — Contributors

| Name | GitHub |
|------|--------|
| Gabriela Zeviani | [@Gabi-Zeviani](https://github.com/Gabi-Zeviani) |
| Guilherme Lopes | [@guilopeszw](https://github.com/guilopeszw) |
| João Bosco Duarte | [@JoaoBoscoDuarte](https://github.com/JoaoBoscoDuarte) |

---

## License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for more information.
