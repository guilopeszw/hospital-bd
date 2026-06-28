# Checklist de Progresso — Etapa 1: Sistema de Gestão Hospitalar (SQL Puro)

---

## Estado Geral

- **Progresso estimado Etapa 1**: ~25-30%
  - Core (modelagem + DDL + seeds + testes): **feito**
  - Domínio operacional (atendimentos, procedimentos, escalas, unidades, internações): **0%**
  - Código Python + CLI: **0%**
  - Documentação final (README + normalização completa): **parcial**
- **Estágio atual**: Final da **Sprint 3** (DDL e seed de dados) — somente o domínio "A" (core de Pessoas/Profissionais/Pacientes) foi implementado.
- **Sprint 1**: Parcialmente feito.
- **Sprint 2**: Parcial (normalização cobre apenas o core).
- **Sprint 3**: Parcial (~40-50% — apenas core).
- **Sprint 4**: Não iniciado (0%).
- **Sprint 5**: Não iniciado (0%).

**Entregáveis principais pendentes (do plano):**
- DDL completo + seeds completos (3 unidades + 10 atend + 10 proc)
- Operações CRUD + CLI em Python (psycopg)
- As 4 consultas analíticas
- README + .env.example
- Normalização completa de todo o modelo
- Estrutura `src/` conforme planejado

---

## O que já foi feito (resumo executivo)

- Modelagem conceitual completa (DER com Mermaid cobrindo **todas** as entidades).
- DDL + constraints fortes + seeds determinísticos do núcleo Pessoa → Paciente / Profissional → Preceptor / Residente.
- Testes automatizados (pytest) que validam as constraints do schema core.
- Docker básico para rodar o Postgres.
- Documentação parcial de normalização (3FN provada para o core usando joined table inheritance).

---

## O que falta fazer (mapeado para o plano de trabalho)

- [ ] Completar DDL das tabelas de negócio em `sql/ddl/` (ATENDIMENTO, PROCEDIMENTO, ATENDIMENTO_PROCEDIMENTO, UNIDADE_HOSPITALAR, ESCALA_PLANTAO, INTERNACAO).
- [ ] Criar seeds mínimos exigidos (3+ unidades, 10+ atendimentos, 10+ procedimentos realizados).
- [ ] Implementar as operações de CRUD da Sprint 4 em Python usando psycopg2.
- [ ] Criar CLI simples (`src/cli` ou similar).
- [ ] Implementar as 4 consultas analíticas.
- [ ] Completar `docs/normalizacao.md` para todas as tabelas.
- [ ] Criar `README.md` completo + `.env.example`.
- [ ] Definir e aplicar forma unificada de inicializar o banco (DDL + DML).
- [ ] Tratar/limpar arquivos legados inconsistentes.

---

## Sprint 1 — Setup & Modelagem conceitual

- [x] Repositório configurado (estrutura com `sql/ddl/`, `sql/dml/`, `docs/`, `docker/`, `tests/`, `scripts/`, `requirements.txt`).
- [x] DER completo construído — ver [docs/der/der_hospitalar.md](/docs/der/der_hospitalar.md) (todas as entidades, especializações Pessoa→, relacionamentos de Atendimento, Procedimentos via tabela associativa, Escala, Unidade, Internação).
- [ ] Exportar DER para PDF (exigido no plano — atualmente só Mermaid).
- [x] Justificativas de cardinalidade e especialização (presentes no DER e introduzidas em normalizacao.md).
- [ ] Configuração de Git flow + GitHub Projects + Issues (não visível no checkout local — responsabilidade do time).

---

## Sprint 2 — Modelo relacional e normalização

- [x] Modelo relacional do core derivado e implementado (DDL + [docs/normalizacao.md](/docs/normalizacao.md)).
- [x] `docs/normalizacao.md` existe com prova formal de 1FN, 2FN e 3FN (para tabelas core usando herança por tabelas associadas).
- [ ] Expandir `normalizacao.md` com justificativas para as tabelas de negócio (Atendimento, Procedimento, Escala etc.).
- [ ] Revisão cruzada completa do modelo (cada pessoa revisa domínio de outra).
- [x] Listagem clara do modelo relacional do core (chaves sublinhadas, FKs marcadas).

---

## Sprint 3 — DDL e seed de dados

- [x] DDL core completo e sequencial:
  - `sql/ddl/01_enums.sql` (papel_profissional_enum, ano_residencia_enum)
  - `sql/ddl/02_pessoa.sql`
  - `sql/ddl/03_paciente.sql`
  - `sql/ddl/04_profissional.sql`
  - `sql/ddl/05_preceptor.sql`
  - `sql/ddl/06_residente.sql`
- [ ] DDL das tabelas de negócio (recomendado: 07_unidade.sql, 08_procedimento.sql, 09_atendimento.sql, 10_atendimento_procedimento.sql, 11_escala.sql, 12_internacao.sql etc.).
- [x] Seeds core (mínimo exigido para pacientes/profissionais):
  - `sql/dml/01_seed_pacientes.sql` (5 pacientes)
  - `sql/dml/02_seed_preceptores.sql` (5 preceptores)
  - `sql/dml/03_seed_residentes.sql` (5 residentes)
- [ ] Seeds de negócio (3 unidades hospitalares, 10 atendimentos, 10 procedimentos realizados).
- [x] Banco sobe via Docker (`docker/docker-compose.yml` — Postgres 16 na porta 5433).
- [ ] Forma unificada / script para aplicar **todo** o DDL + DML de uma vez (hoje depende de execução manual ou do fixture de testes).
- [x] Extensão uuid-ossp + UUIDs com default + CHECKs + UNIQUEs + FKs bem definidos no core.

**Observação importante de schema:**  
Todo o DDL atual usa **UUID** (consistente com o DER). Qualquer DDL novo **deve** seguir o mesmo padrão. A tabela associativa no DER é chamada `ATENDIMENTO_PROCEDIMENTO`.

---

## Sprint 4 — CRUD e consultas básicas (Python + psycopg)

- [ ] Estrutura de código Python para Etapa 1 criada (`src/` ou `src/etapa1/`, `src/cli/` — atualmente inexistente).
- [ ] Função: Inserir atendimento (com validação de existência de paciente, residente e preceptor).
- [ ] Função: Listar atendimentos de um paciente (ordenado por data/hora).
- [ ] Função: Listar procedimentos realizados em um atendimento específico.
- [ ] Função: Atualizar dados de paciente.
- [ ] Função: Remover procedimento realizado (respeitando a flag `faturado`).
- [ ] Função: Calcular tempo médio de atendimento por residente.
- [ ] CLI simples e usável (com Typer ou argparse) para demonstrar as operações.
- [ ] `scripts/inserir_atendimento.py` (protótipo atual) funciona ou foi migrado/substituído pelo código oficial da CLI.

**Status atual do protótipo em `scripts/inserir_atendimento.py`:**
- Usa psycopg2 corretamente.
- Tenta validação + INSERT com RETURNING.
- **Não funciona** com o schema atual (tabelas de atendimento não existem + usa IDs inteiros + nomes de coluna errados).

---

## Sprint 5 — Consultas analíticas, README e apresentação

- [ ] Consulta 1: Ranking de residentes (provavelmente por número de atendimentos ou tempo médio).
- [ ] Consulta 2: Preceptores que supervisionaram 5+ atendimentos no mês.
- [ ] Consulta 3: Plantões/escalas por unidade no mês.
- [ ] Consulta 4: Pacientes que não realizaram nenhum procedimento de risco ALTO.
- [ ] `README.md` finalizado (instruções de instalação, Docker, popular banco, rodar CLI e consultas).
- [ ] Preparação da apresentação de 10 minutos (divisão entre membros).
- [ ] PR `develop → main` + tag `v1.0-etapa1`.

**Consultas SQL legadas existentes (precisam ser reescritas/corrigidas):**
- `sql/listar_atendimentos_pacientes.sql`
- `sql/listar_procedimentos_atendimentos.sql`
- `sql/tempo_medio_atendimento_residente.sql`

---

## Legado / Arquivos Desatualizados ou Inconsistentes

- [ ] `sql/tabela_procedimeto_atendimento.sql` — **legado obsoleto**. Usa SERIAL + INT, nomes de coluna errados (`id_profissional`), tabela `PROCEDIMENTO_REALIZADO`. Substituir pelo DDL oficial ou mover para `docs/legacy/`.
- [ ] `sql/dados_test.sql` — obsoleto (mesmo problema de IDs e tabelas faltando).
- [ ] Arquivos de consulta `.sql` soltos — reorganizar em `sql/consultas/` quando Sprint 4/5 avançar.
- [ ] `scripts/inserir_atendimento.py` — protótipo útil para referência de lógica, mas corrigir ou descartar.

---

## Como as coisas funcionam hoje (situação atual do projeto)

### 1. Subir o banco de dados
```bash
cd docker
docker compose up -d
```
- Banco fica disponível em **localhost:5433**
- Credenciais padrão (do docker-compose):  
  user=`postgres`, password=`password`, database=`hospital_db`

### 2. Popular o banco (hoje só o core)
Opções atuais:
- Executar manualmente (na ordem):
  1. `sql/ddl/01_enums.sql`
  2. ... até `06_residente.sql`
  3. `sql/dml/01_seed_pacientes.sql` etc.
- Ou simplesmente rodar os testes: `pytest` (o `conftest.py` aplica automaticamente o DDL do core na fixture).

### 3. Executar testes
```bash
pytest
```
- Usa a variável `DATABASE_URL` (default: localhost:5433)
- Fixture de sessão carrega só DDL core
- Cada teste usa transação com rollback (isolamento)
- Atualmente testa apenas constraints do domínio de Pessoas (CPF único, regex, grupo sanguíneo válido, default is_flamengo etc.)

### 4. Usar Python / psycopg hoje
- Único script existente: `scripts/inserir_atendimento.py`
- Ele **não roda com sucesso** atualmente porque as tabelas de atendimento/procedimento ainda não foram criadas e há divergência de tipos de ID.

### 5. O que realmente funciona agora
- Criação de Pessoas, Pacientes, Profissionais, Preceptores e Residentes com validações fortes no banco.
- Seeds reprodutíveis com UUIDs fixos.
- Testes automáticos que garantem que o DDL core está correto.
- Docker reprodutível.

### 6. O que está bloqueado / não funciona
- Qualquer operação de **Atendimento**, **Procedimento**, **Escala** ou **Internação** (tabelas não existem).
- CRUD e consultas da Sprint 4/5.
- Demonstração completa do projeto.

### Stack em uso (100% alinhado ao plano para Etapa 1)
- **BD**: PostgreSQL 16 (Docker)
- **Conector**: psycopg2
- **Testes**: pytest
- **Docs**: Markdown + Mermaid (DER)
- **Containerização**: Docker Compose (somente DB por enquanto)

---

## Próximos Passos Recomendados (Etapa 1)

1. Criar o DDL completo das tabelas de negócio seguindo o padrão UUID + numeração sequencial em `sql/ddl/`.
2. Criar os seeds mínimos (unidades + atendimentos + procedimentos realizados).
3. Implementar as funções de CRUD em Python (começando pelo inserir atendimento com validações).
4. Estruturar uma CLI básica.
5. Reescrever/mover as consultas analíticas.
6. Escrever `README.md` + `.env.example`.
7. Completar a seção de normalização para todo o modelo.
8. Revisão cruzada + limpeza de arquivos legados.

---

**Checklist gerado com base na análise do `plano_de_trabalho_projeto_hospitalar.md` em 2026-06-28.**

Para atualizar este checklist conforme o trabalho avança, basta marcar os itens como `[x]`.
