# Sistema de Gestão Hospitalar — HU Dra. Yuska Maritan Brito

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

---

## Sumário

- [Sobre o Projeto](#sobre-o-projeto)
- [O que o Projeto Cobre](#o-que-o-projeto-cobre)
  - [Etapa 1 — Fundamentos (SQL Puro)](#etapa-1--fundamentos-sql-puro)
  - [Etapa 2 — Funcionalidades Avançadas](#etapa-2--funcionalidades-avançadas)
- [Stack Tecnológica](#stack-tecnológica)
- [Dependências e Instalação](#dependências-e-instalação)
  - [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
  - [macOS](#macos)
  - [Windows](#windows)
- [Como Rodar o Projeto](#como-rodar-o-projeto)
  - [1. Subir o Banco com Docker](#1-subir-o-banco-com-docker)
  - [2. Popular o Banco (DDL + Seeds)](#2-popular-o-banco-ddl--seeds)
  - [3. Instalar Dependências Python](#3-instalar-dependências-python)
  - [4. Rodar os Testes](#4-rodar-os-testes)
  - [5. Usar a CLI](#5-usar-a-cli)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Documentação](#documentação)
- [Equipe — Contribuidores](#equipe--contribuidores)
- [Licença](#licença)

---

## Sobre o Projeto

Sistema acadêmico para gestão hospitalar do **Hospital Universitário Dra. Yuska Maritan Brito**. Desenvolvido como projeto único da disciplina de Banco de Dados.

Objetivo: cadastrar pessoas (pacientes e profissionais), gerenciar atendimentos, procedimentos, escalas de plantão e gerar indicadores analíticos. O sistema cobre desde a modelagem conceitual (DER) até a implementação física em PostgreSQL, passando por normalização até 3FN, SQL avançado, triggers, stored procedures, views e uso de ORM (SQLAlchemy).

Dividido em duas etapas de complexidade crescente:

1. **Etapa 1** — Modelagem relacional, DDL/DML, CRUD e consultas em SQL puro (sem ORM).
2. **Etapa 2** — Stored procedures, triggers, views, migração para ORM (SQLAlchemy) e tratamento de concorrência.

---

## O que o Projeto Cobre

### Etapa 1 — Fundamentos (SQL Puro)

- **Modelagem Conceitual e Lógica** — DER completo, modelo relacional, normalização até 3FN/BCNF.
- **DDL e Constraints** — Criação de 12 tabelas com PK, FK, CHECK, NOT NULL, UNIQUE, enums e UUIDs.
- **Seeds** — Dados de teste: 5+ pacientes, residentes, preceptores, unidades, atendimentos e escalas.
- **CRUD** — Operações completas de inserção, listagem, atualização e remoção com validações.
- **Consultas Analíticas** — Ranking de residentes, preceptores com mais atendimentos, plantões por unidade, pacientes sem procedimentos de alto risco.
- **CLI** — Interface de linha de comando cobrindo todas as operações via `argparse`.
- **Testes Automatizados** — Suite `pytest` com schema isolado por sessão.

### Etapa 2 — Funcionalidades Avançadas

> *Em desenvolvimento — previsão de início após conclusão da Etapa 1.*

- Stored procedures com transações (registro completo de atendimento, reajuste de escala).
- Triggers (controle de sobreposição de escala, auditoria de atendimentos, atualização de médias).
- Views analíticas (pacientes internados, residentes sem supervisor, estatísticas mensais).
- Migração para **SQLAlchemy 2.x** com Alembic.
- Consultas avançadas via ORM e tratamento de concorrência com locks.

---

## Stack Tecnológica

| Componente   | Tecnologia                                          |
|-------------|-----------------------------------------------------|
| Banco       | PostgreSQL 16 (Alpine)                              |
| Linguagem   | Python 3.12+                                        |
| Conector    | psycopg2 2.9                                        |
| ORM (Etapa 2) | SQLAlchemy 2.x + Alembic                          |
| Testes      | pytest                                              |
| Container   | Docker + Docker Compose                             |
| Modelagem   | Mermaid (DER)                                       |

---

## Dependências e Instalação

### Linux (Ubuntu/Debian)

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.12+ e pip
sudo apt install -y python3 python3-pip python3-venv

# Instalar Docker (se não instalado)
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER  # fazer logoff/login após

# Verificar instalação
python3 --version
docker --version
docker compose version
```

### macOS

```bash
# Instalar Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python 3.12+
brew install python@3.12

# Instalar Docker Desktop
brew install --cask docker
# ou via: https://docs.docker.com/desktop/install/mac-install/

# Verificar
python3 --version
docker --version
docker compose version
```

### Windows

```powershell
# 1. Instalar Python 3.12+
#    Download: https://www.python.org/downloads/
#    Marcar "Add Python to PATH" durante instalação

# 2. Instalar Docker Desktop
#    Download: https://docs.docker.com/desktop/install/windows-install/
#    WSL 2 backend recomendado

# 3. Verificar (PowerShell)
python --version
docker --version
docker compose version
```

---

## Como Rodar o Projeto

### 1. Subir o Banco com Docker

```bash
cd docker
docker compose up -d
```

PostgreSQL fica disponível em:

- **Host:** `localhost`
- **Porta:** `5433`
- **Usuário:** `postgres`
- **Senha:** `password`
- **Database:** `hospital_db`

Para parar: `docker compose down`

### 2. Popular o Banco (DDL + Seeds)

```bash
for f in sql/ddl/*.sql sql/dml/*.sql; do
  psql "postgresql://postgres:password@localhost:5433/hospital_db" -f "$f"
done
```

> **Nota:** Os arquivos DDL (`sql/ddl/01`–`12`) e DML (`sql/dml/01`–`07`) são numerados por dependência. O laço `for` respeita a ordem alfabética/numérica automaticamente.

### 3. Instalar Dependências Python

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows PowerShell

pip install -r requirements.txt
```

Dependências: `psycopg2` (conector PostgreSQL) e `pytest` (testes).

### 4. Rodar os Testes

```bash
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" pytest
```

Os testes criam o próprio schema do zero (`DROP SCHEMA public CASCADE`) via fixture em `tests/conftest.py`, isolando cada sessão de teste — não é necessário popular o banco antes.

### 5. Usar a CLI

```bash
# Ativar virtualenv (se não estiver ativo)
source .venv/bin/activate

# Ranking de residentes por número de atendimentos
python -m src.etapa1.atendimento_crud ranking-residentes

# Tempo médio de atendimento por residente
python -m src.etapa1.atendimento_crud tempo-medio-residente

# Plantões por unidade no mês corrente
python -m src.etapa1.atendimento_crud plantoes-mes

# Pacientes sem procedimento de risco ALTO
python -m src.etapa1.atendimento_crud pacientes-sem-risco-alto

# Listar atendimentos de um paciente
python -m src.etapa1.atendimento_crud atendimentos-paciente <id_paciente>

# Listar procedimentos de um atendimento
python -m src.etapa1.atendimento_crud procedimentos-atendimento <id_atendimento>

# Preceptores com mais de 5 atendimentos em um mês
python -m src.etapa1.atendimento_crud preceptores-mes <ano> <mes>

# Remover procedimento realizado (bloqueado se faturado)
python -m src.etapa1.atendimento_crud remover-procedimento <id_atendimento> <id_procedimento>

# Atualizar dados de paciente
python -m src.etapa1.atendimento_crud atualizar-paciente <id_paciente> --convenio NOVO-CONV

# Inserir novo atendimento
python -m src.etapa1.atendimento_crud inserir-atendimento "2025-07-01 10:00" 30 <id_paciente> <id_residente> <id_preceptor>
```

> **Dica:** Use `--help` para ver detalhes de cada subcomando:
> ```bash
> python -m src.etapa1.atendimento_crud --help
> python -m src.etapa1.atendimento_crud inserir-atendimento --help
> ```

---

## Estrutura do Repositório

```
hospital-bd/
├── docker/
│   └── docker-compose.yml          # PostgreSQL 16 em container
├── sql/
│   ├── ddl/                        # CREATE TABLE (numerado: 01_enums.sql → 12_faturamento.sql)
│   ├── dml/                        # Seeds (01_pacientes → 07_faturamento)
│   └── queries/                    # Consultas SQL puras (CRUD + analíticas)
├── src/
│   └── etapa1/
│       └── atendimento_crud.py     # CLI + funções CRUD (psycopg2)
├── tests/
│   ├── conftest.py                 # Fixture: schema isolado por sessão
│   └── unit/
│       ├── test_core_entities.py   # Testes: Pessoa/Paciente
│       └── test_negocio.py         # Testes: regras de negócio
├── docs/
│   ├── der/
│   │   └── der_hospitalar.md       # DER em Mermaid
│   ├── normalizacao.md             # Prova formal de normalização até 3FN
│   ├── checklist_etapa1.md         # Progresso detalhado da Etapa 1
│   └── ...                         # Novos documentos por etapa
├── projeto_bd.md                   # Especificação completa do projeto
├── plano_de_trabalho_projeto_hospitalar.md  # Planejamento e backlog
├── requirements.txt                # Dependências Python
└── README.md                       # Este arquivo
```

---

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [`docs/der/der_hospitalar.md`](docs/der/der_hospitalar.md) | Diagrama Entidade-Relacionamento (Mermaid) |
| [`docs/normalizacao.md`](docs/normalizacao.md) | Modelo lógico + prova formal de normalização até 3FN |
| [`docs/checklist_etapa1.md`](docs/checklist_etapa1.md) | Checklist de progresso da Etapa 1 com decisões de modelagem |
| [`projeto_bd.md`](projeto_bd.md) | Especificação completa do projeto (requisitos das Etapas 1 e 2) |
| [`plano_de_trabalho_projeto_hospitalar.md`](plano_de_trabalho_projeto_hospitalar.md) | Planejamento operacional, backlog e estratégia de organização |

---

## Equipe — Contribuidores

| Nome | GitHub |
|------|--------|
| Gabriela Zeviani | [@Gabi-Zeviani](https://github.com/Gabi-Zeviani) |
| Guilherme Lopes | [@guilherme-lopes](https://github.com/guilherme-lopes) |
| João Bosco Duarte | [@JoaoBoscoDuarte](https://github.com/JoaoBoscoDuarte) |

---

## Licença

Distribuído sob licença MIT. Veja [`LICENSE`](./LICENSE) para mais informações.
