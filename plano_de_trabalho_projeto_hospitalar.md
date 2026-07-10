# Plano de Trabalho — Sistema de Gestão Hospitalar

Este documento substitui o planejamento genérico anterior (sprints fixos, divisão de papéis por pessoa, etc. — não estava sendo seguido e não ajudava a saber "onde estamos"). A partir de agora ele é só isto: **um checklist operacional** ligado aos arquivos reais do repo, mais decisões de organização e estratégia de entrega. A fonte de verdade dos requisitos continua sendo [`projeto_bd.md`](./projeto_bd.md).

---

## 1. Checklist — Etapa 1 (SQL puro)

### 1. Modelagem (2 pts)
- [x] DER completo — [`docs/der/der_hospitalar.md`](docs/der/der_hospitalar.md) (Mermaid)
- [ ] Exportar o DER para PDF (hoje só existe em Mermaid — é um requisito explícito da entrega)
- [x] Modelo relacional completo — [`docs/normalizacao.md`](docs/normalizacao.md) (seções 1 e 3)
- [x] Normalização até 3FN justificada — `docs/normalizacao.md` (seções 2 e 4, todas as tabelas)

### 2. Implementação do BD (3 pts)
- [x] DDL completo com PK/FK/CHECK/UNIQUE/NOT NULL — [`sql/ddl/01`–`11`](sql/ddl/)
- [x] Seeds mínimos exigidos (5 pacientes, 5 residentes, 5 preceptores, 3 unidades, 10 atendimentos, 10 procedimentos realizados) — [`sql/dml/01`–`06`](sql/dml/)

### 3. CRUD e consultas básicas (3 pts)
| Operação | Python | SQL puro |
|---|---|---|
- [x] Inserir atendimento (valida paciente/residente/preceptor) | `atendimento_crud.py::inserir_atendimento` | `sql/queries/inserir_atendimentos.sql` |
- [x] Listar atendimentos de um paciente (por data) | `::listar_atendimentos_paciente` | `sql/queries/listar_atendimentos_paciente.sql` |
- [x] Listar procedimentos de um atendimento | `::listar_procedimentos_atendimento` | `sql/queries/listar_procedimentos_atendimento.sql` |
- [x] Atualizar dados de paciente | `::atualizar_paciente` | `sql/queries/atualizar_paciente.sql` |
- [x] Remover procedimento realizado (bloqueado se `faturado`) | `::remover_procedimento_realizado` | `sql/queries/remover_procedimento_realizado.sql` |
- [x] Tempo médio de atendimento por residente | `::tempo_medio_por_residente` | `sql/queries/tempo_medio_atendimento_residente.sql` |
- [x] CLI cobrindo as 6 operações acima — `python -m src.etapa1.atendimento_crud <comando>` (argparse, stdlib)

*(tabela informal — todos os arquivos ficam em [`src/etapa1/atendimento_crud.py`](src/etapa1/atendimento_crud.py) e [`sql/queries/`](sql/queries/))*

### 4. Consultas analíticas (2 pts)
- [x] Ranking de residentes por atendimentos — `::ranking_residentes` + `sql/queries/ranking_residentes_atendimentos.sql`
- [x] Preceptores com +5 atendimentos no mês — `::preceptores_mais_atendimentos_mes` + `sql/queries/preceptores_mais_atendimentos_mes.sql`
- [x] Plantões por unidade/residente no mês corrente — `::plantoes_por_unidade_mes` + `sql/queries/plantoes_por_unidade_residente_mes.sql`
- [x] Pacientes sem procedimento de risco ALTO — `::pacientes_sem_procedimento_risco_alto` + `sql/queries/pacientes_sem_procedimento_risco_alto.sql`

### 5. Documentação e apresentação (1 pt extra)
- [x] `README.md` (instalação, Docker, seeds, testes, CLI)
- [ ] Apresentação de 10 minutos (fora do escopo de código — combinar com o time)
- [ ] Revisão cruzada do modelo entre integrantes (recomendado, não bloqueia nota)

**Status Etapa 1: praticamente fechada.** Só falta o que não é código (PDF do DER, apresentação, revisão cruzada).

---

## 2. Checklist — Etapa 2 (avançado) — nada iniciado ainda

> Não começar antes da Etapa 1 estar 100% fechada (PDF + apresentação). Os caminhos de arquivo abaixo são **propostos**, ainda não existem.

### 1. Stored Procedures (1,5 pt)
- [ ] `sp_registrar_atendimento_completo` (transação com rollback) → `sql/procedures/sp_registrar_atendimento_completo.sql`
- [ ] `sp_calcular_tempo_medio_espera` → `sql/procedures/sp_calcular_tempo_medio_espera.sql`
- [ ] `sp_reajustar_escala` (com checagem de conflito) → `sql/procedures/sp_reajustar_escala.sql`

### 2. Triggers (1,5 pt)
- [ ] `trg_check_sobreposicao_escala` (BEFORE INSERT/UPDATE em ESCALA) → `sql/triggers/trg_check_sobreposicao_escala.sql`
- [ ] `trg_audita_atendimento` + tabela `AUDITORIA_ATENDIMENTO` → `sql/triggers/trg_audita_atendimento.sql`
- [ ] `trg_atualiza_media_procedimentos` (coluna `media_tempo_procedimento` em PROCEDIMENTO) → `sql/triggers/trg_atualiza_media_procedimentos.sql`

### 3. Views (1,0 pt)
- [ ] `vw_pacientes_internados` → **depende de uma tabela `INTERNACAO`, que não existe** (foi removida do DER da Etapa 1 por estar fora de escopo — decisão pendente: criar agora)
- [ ] `vw_residentes_sem_supervisor` → `sql/views/vw_residentes_sem_supervisor.sql`
- [ ] `vw_estatisticas_atendimentos_mensal` → `sql/views/vw_estatisticas_atendimentos_mensal.sql`

### 4. ORM (2,0 pts)
- [ ] Modelos SQLAlchemy (herança Pessoa/Paciente/Profissional via Joined Table Inheritance) → `src/etapa2/models.py`
- [ ] Alembic para migrations
- [ ] Reimplementar as operações da Etapa 1 usando sessões/transações da ORM
- [ ] Demonstrar lazy vs eager loading em pelo menos uma relação

### 5. Consultas avançadas com ORM (1,0 pt)
- [ ] Preceptores que supervisionaram residentes que atenderam pacientes flamenguistas
- [ ] Último atendimento de cada paciente (data, residente, preceptor, procedimentos)
- [ ] % de procedimentos de alto risco por residente

### 6. Concorrência e transações (1,0 pt)
- [ ] Cenário de duas transações concorrentes escalando o mesmo residente no mesmo dia/turno/unidade, com lock otimista ou pessimista + logs

### 7. Entrega final (1 pt extra)
- [ ] Tag `v1.0-etapa1` (retroativa, no commit que fecha a Etapa 1 — ver seção 4)
- [ ] Tag `v1.0-etapa2`
- [ ] Vídeo de até 8 minutos
- [ ] Relatório de 2 páginas (`docs/relatorio_etapa2.md`) — decisões de trigger vs procedure, escolha da ORM

---

## 3. Organização do projeto — decisões

### 3.1 `sql/` — está ok como está, não criar pasta "crud"
`sql/ddl/`, `sql/dml/`, `sql/queries/` já separam schema, seed e consultas. `queries/` tem 10 arquivos flat com nomes claros (`inserir_atendimentos.sql`, `listar_atendimentos_paciente.sql`, etc.) — criar uma subpasta `queries/crud/` vs `queries/analiticas/` para 10 arquivos é organizar por organizar. Numeração de `ddl/`/`dml/` já é consistente (01–11 / 01–06). Nada a mudar aqui agora.

Quando a Etapa 2 chegar, ela já ganha pastas próprias por natureza do objeto SQL (não por reorganizar a Etapa 1): `sql/procedures/`, `sql/triggers/`, `sql/views/`.

### 3.2 `src/etapa1/` — manter, não separar por branch
A Etapa 2 pede explicitamente para **reimplementar** as operações da Etapa 1 via ORM — ou seja, as duas versões (SQL puro e ORM) precisam existir **ao mesmo tempo** no repositório final. O item 7 da Etapa 2 pede um "repositório com commits separados por Etapa 1 e Etapa 2", não um repositório onde só uma etapa está visível por vez. Se o código da Etapa 1 morasse numa branch separada, a entrega final (main) só mostraria a Etapa 2 — quebra o requisito. Então:

- Manter `src/etapa1/` como está.
- Quando começar a Etapa 2, criar `src/etapa2/` do lado, não substituir.
- Branches continuam servindo para trabalho em andamento (feature branches mergeadas em `main`), não para particionar entregas que precisam coexistir.

### 3.3 `atendimento_crud.py` monolítico (404 linhas) — concordo em parte
Um esquema de camadas tipo `models/repositories/services` seria over-engineering para CRUD em SQL puro (isso é literalmente o trabalho da ORM na Etapa 2). O problema real hoje é mais simples: o arquivo mistura funções de acesso a dados com o parsing do CLI (`argparse`) — quem importar o módulo (um teste, ou futuramente `etapa2` comparando comportamento) carrega a montagem do CLI sem precisar. Split mínimo que resolve isso, sem inventar camada nova:

- `src/etapa1/atendimento_crud.py` — só as funções de dados (o que já é hoje, menos o bloco de CLI).
- `src/etapa1/cli.py` — `argparse`, dispatch e `if __name__ == "__main__"`.

Dois arquivos, não mais que isso. Registrado como item de "Melhorias" abaixo — é polimento, não bloqueia nota.

### 3.4 Padronização de nomes
Já está padronizado: `ddl`/`dml` numerados por dependência, `queries/` em `snake_case` batendo com o nome da operação/tabela. Nenhuma renomeação necessária.

---

## 4. Estratégia GitHub — separar Etapa 1 de Etapa 2

O requisito ("commits separados por Etapa 1 e Etapa 2") é resolvido com **tags do git**, não com branches long-lived — é o recurso nativo pra marcar um corte no histórico sem duplicar/esconder código:

1. Marcar agora, retroativamente, o commit que fecha a Etapa 1 com a tag `v1.0-etapa1`.
2. Todo o trabalho da Etapa 2 continua como commits normais em `main`, seguindo a mesma convenção já usada (`feat(orm):`, `feat(trigger):`, `feat(procedure):`, `docs(etapa2):`, etc.).
3. Ao final, marcar o último commit da Etapa 2 com a tag `v1.0-etapa2`.
4. Qualquer pessoa (incluindo quem for corrigir) vê exatamente o que foi Etapa 2 com `git log v1.0-etapa1..v1.0-etapa2` ou comparando as tags no GitHub — zero ferramenta extra, zero branch para gerenciar.

Custo total: dois comandos `git tag`. Mencionar as tags no `README.md` quando a Etapa 2 estiver perto do fim.

---

## 5. Melhorias (backlog — não bloqueia nota)

- [ ] Dividir `atendimento_crud.py` em funções + `cli.py` (seção 3.3)
- [ ] Exportar `docs/der/der_hospitalar.md` para PDF
- [ ] Revisão cruzada do modelo entre os integrantes do grupo
- [ ] `.env.example` documentando `DATABASE_URL` (hoje funciona via variável de ambiente com default hardcoded, mas não há um arquivo de exemplo commitado)

## 6. Futuro (Etapa 2 — só começar depois da Etapa 1 fechada)

- Criar `sql/procedures/`, `sql/triggers/`, `sql/views/`
- Criar `src/etapa2/` com models SQLAlchemy + Alembic
- Decidir e criar a tabela `INTERNACAO` (necessária só para `vw_pacientes_internados`)
- Tags `v1.0-etapa1` / `v1.0-etapa2` (seção 4)

---

## 7. Stack (referência rápida)

PostgreSQL 16 (Docker) · Python 3.12 · `psycopg2` (Etapa 1) · SQLAlchemy 2.x + Alembic (Etapa 2) · `pytest` · Mermaid para o DER.
