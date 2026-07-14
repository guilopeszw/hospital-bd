# Docker — Ambiente PostgreSQL

## Visão Geral

Container PostgreSQL 16 Alpine para ambiente de desenvolvimento. Configuração mínima com Docker Compose.

**Arquivo:** [`../../docker/docker-compose.yml`](../../docker/docker-compose.yml)

---

## docker-compose.yml

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: hospital_db_container
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: hospital_db
    ports:
      - "5433:5432"
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
```

---

## Conexão

| Parâmetro | Valor |
|-----------|-------|
| Host | `localhost` |
| Porta | `5433` (host) → `5432` (container) |
| Usuário | `postgres` |
| Senha | `password` |
| Database | `hospital_db` |
| String URL | `postgresql://postgres:password@localhost:5433/hospital_db` |

A porta `5433` foi escolhida para evitar conflito com uma eventual instância local do PostgreSQL na porta padrão `5432`.

---

## Comandos

```bash
# Subir o container
cd docker && docker compose up -d

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f

# Parar
docker compose down

# Parar e remover volume de dados
docker compose down -v
```

---

## Dados Persistentes

O volume `./postgres_data/` monta os dados do PostgreSQL fora do container. Enquanto esse diretório existir, os dados persistem entre execuções de `docker compose down`/`up`.

Para resetar o banco:

```bash
docker compose down -v    # Remove volume
docker compose up -d      # Recria do zero
```

---

## Executando SQL via Container

Sem precisar instalar `psql` no host:

```bash
# DDL
docker exec -i hospital_db_container psql -U postgres -d hospital_db < sql/ddl/01_enums.sql

# Todos os DDLs
for f in sql/ddl/*.sql; do
  docker exec -i hospital_db_container psql -U postgres -d hospital_db < "$f"
done

# Todos os DMLs
for f in sql/dml/*.sql; do
  docker exec -i hospital_db_container psql -U postgres -d hospital_db < "$f"
done
```
