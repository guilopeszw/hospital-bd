# Sistema de Gestão Hospitalar — Etapa 1

Modelo relacional, DDL/DML e CRUD/consultas em SQL puro (sem ORM — ORM é Etapa 2).

## Requisitos

- Docker + Docker Compose
- Python 3.12+, `psql` (cliente do PostgreSQL)

## 1. Subir o banco

```bash
cd docker
docker compose up -d
```

Postgres fica disponível em `localhost:5433` (user=`postgres`, password=`password`, db=`hospital_db`).

## 2. Popular o banco (DDL + seeds)

```bash
for f in sql/ddl/*.sql sql/dml/*.sql; do
  psql "postgresql://postgres:password@localhost:5433/hospital_db" -f "$f"
done
```

Os arquivos são numerados e devem rodar nessa ordem (o `for` acima já respeita a ordem alfabética/numérica).

## 3. Instalar dependências Python e rodar os testes

```bash
pip install -r requirements.txt
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" pytest
```

Os testes criam o próprio schema do zero (via fixture em `tests/conftest.py`), então não é necessário ter rodado o passo 2 antes de testar.

## 4. Usar a CLI

```bash
python -m src.etapa1.atendimento_crud ranking-residentes
python -m src.etapa1.atendimento_crud tempo-medio-residente
python -m src.etapa1.atendimento_crud plantoes-mes
python -m src.etapa1.atendimento_crud pacientes-sem-risco-alto
python -m src.etapa1.atendimento_crud atendimentos-paciente a1111111-1111-1111-1111-111111111111
python -m src.etapa1.atendimento_crud procedimentos-atendimento e1111111-1111-1111-1111-111111111111
python -m src.etapa1.atendimento_crud preceptores-mes 2025 6
python -m src.etapa1.atendimento_crud remover-procedimento <id_atendimento> <id_procedimento>
python -m src.etapa1.atendimento_crud atualizar-paciente <id_paciente> --convenio NOVO-CONV
python -m src.etapa1.atendimento_crud inserir-atendimento "2025-07-01 10:00:00" 30 <id_paciente> <id_residente> <id_preceptor>
```

## Estrutura do repositório

```
docs/          # DER, normalização, checklist de progresso
docker/        # docker-compose do Postgres
sql/ddl/       # CREATE TABLE, numerado por dependência
sql/dml/       # seeds
sql/queries/   # CRUD e consultas analíticas em SQL puro
src/etapa1/    # CRUD/consultas em Python (psycopg2)
tests/         # pytest (schema de teste isolado, criado a cada sessão)
```
