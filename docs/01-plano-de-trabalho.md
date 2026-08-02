# Plano de Trabalho — Sistema de Gestão Hospitalar

Este documento substitui o planejamento genérico anterior (sprints fixos, divisão de papéis por pessoa, etc. — não estava sendo seguido e não ajudava a saber "onde estamos"). A partir de agora ele é só isto: **um checklist operacional** ligado aos arquivos reais do repo, mais decisões de organização e estratégia de entrega. A fonte de verdade dos requisitos continua sendo [`00-especificacao.md`](./00-especificacao.md).

---

## 1. Checklist — Etapa 1 (SQL puro)

### 1. Modelagem (2 pts)
- [x] DER completo — [`03-modelagem/01-der.md`](03-modelagem/01-der.md) (Mermaid)
- [x] Entrega do DER com justificativa de cardinalidade — [`03-modelagem/03-justificativa_cardinalidades.md`](03-modelagem/03-justificativa_cardinalidades.md) + [`04-diagrama.png`](03-modelagem/04-diagrama.png) + `DER_e_cardinalidades_atualizado.docx`
- [x] Modelo relacional completo — [`03-modelagem/02-normalizacao.md`](03-modelagem/02-normalizacao.md) (seções 1 e 3)
- [x] Normalização até 3FN justificada — `03-modelagem/02-normalizacao.md` (seções 2 e 4, todas as tabelas)

### 2. Implementação do BD (3 pts)
- [x] DDL completo com PK/FK/CHECK/UNIQUE/NOT NULL — [`../sql/ddl/`](../sql/ddl/) (14 arquivos, inclui `AUDITORIA_ATENDIMENTO` e `INTERNACAO` da Etapa 2)
- [x] Seeds acima do mínimo exigido (5 pacientes, 5 residentes, 5 preceptores, 3 unidades, 10 procedimentos, 16 atendimentos, 18 procedimentos realizados) — [`../sql/dml/`](../sql/dml/)

### 3. CRUD e consultas básicas (3 pts)
| Operação | Python | SQL puro |
|---|---|---|
- [x] Inserir atendimento (valida paciente/residente/preceptor) | `atendimento_crud.py::inserir_atendimento` | `../sql/queries/inserir_atendimentos.sql` |
- [x] Listar atendimentos de um paciente (por data) | `::listar_atendimentos_paciente` | `../sql/queries/listar_atendimentos_paciente.sql` |
- [x] Listar procedimentos de um atendimento | `::listar_procedimentos_atendimento` | `../sql/queries/listar_procedimentos_atendimento.sql` |
- [x] Atualizar dados de paciente | `::atualizar_paciente` | `../sql/queries/atualizar_paciente.sql` |
- [x] Remover procedimento realizado (bloqueado se houver faturamento) | `::remover_procedimento_realizado` | `../sql/queries/remover_procedimento_realizado.sql` |
- [x] Tempo médio de atendimento por residente | `::tempo_medio_por_residente` | `../sql/queries/tempo_medio_atendimento_residente.sql` |
- [x] CLI cobrindo as operações acima — `python -m src.etapa1.atendimento_crud <comando>` (argparse, stdlib)

*(tabela informal — todos os arquivos ficam em [`../src/etapa1/atendimento_crud.py`](../src/etapa1/atendimento_crud.py) e [`../sql/queries/`](../sql/queries/))*

### 4. Consultas analíticas (2 pts)
- [x] Ranking de residentes por atendimentos — `::ranking_residentes` + `../sql/queries/ranking_residentes_atendimentos.sql`
- [x] Preceptores com +5 atendimentos no mês — `::preceptores_mais_atendimentos_mes` + `../sql/queries/preceptores_mais_atendimentos_mes.sql`
- [x] Plantões por unidade/residente no mês corrente — `::plantoes_por_unidade_mes` + `../sql/queries/plantoes_por_unidade_residente_mes.sql`
- [x] Pacientes sem procedimento de risco ALTO — `::pacientes_sem_procedimento_risco_alto` + `../sql/queries/pacientes_sem_procedimento_risco_alto.sql`

### 5. Documentação e apresentação (1 pt extra)
- [x] `../README.md` (instalação, Docker, seeds, testes, CLI)
- [x] Apresentação de 10 minutos demonstrando as funcionalidades.
- [x] Revisão cruzada do modelo entre integrantes.

**Status Etapa 1: 100% fechada.** Tag `v1.0-etapa1` marca o corte.

---

## 2. Checklist — Etapa 2 (avançado)

### 1. Stored Procedures (1,5 pt) — feito
- [x] `sp_registrar_atendimento_completo` (atendimento + lista de procedimentos via JSONB, transação única, rollback verificado) → `../sql/procedures/sp_registrar_atendimento_completo.sql`
- [x] `sp_calcular_tempo_medio_espera` (chegada → 1º procedimento, por unidade) → `../sql/procedures/sp_calcular_tempo_medio_espera.sql`
- [x] `sp_reajustar_escala` (move escalas de um residente, aborta em conflito) → `../sql/procedures/sp_reajustar_escala.sql`

### 2. Triggers (1,5 pt) — feito
- [x] `trg_check_sobreposicao_escala` (BEFORE INSERT/UPDATE em ESCALA — barra mesmo residente em 2 unidades no mesmo dia/turno) → `../sql/triggers/trg_check_sobreposicao_escala.sql`
- [x] `trg_audita_atendimento` + tabela `AUDITORIA_ATENDIMENTO` → `../sql/triggers/trg_audita_atendimento.sql`
- [x] `trg_atualiza_media_procedimentos` (coluna `media_tempo_procedimento` em PROCEDIMENTO) → `../sql/triggers/trg_atualiza_media_procedimentos.sql`

### 3. Views (1,0 pt) — feito
- [x] `vw_pacientes_internados` — entidade `INTERNACAO` criada (DDL 14) para sustentá-la → `../sql/views/vw_pacientes_internados.sql`
- [x] `vw_residentes_sem_supervisor` → `../sql/views/vw_residentes_sem_supervisor.sql`
- [x] `vw_estatisticas_atendimentos_mensal` → `../sql/views/vw_estatisticas_atendimentos_mensal.sql`

### 4. ORM (2,0 pts) — feito, exceto Alembic
- [x] Modelos SQLAlchemy 2.0 (`src/etapa2/models.py`) — Pessoa/Paciente/Profissional/Preceptor/Residente, Unidade, Atendimento, Procedimento, ProcedimentoRealizado, Faturamento, Escala
- [ ] Alembic para migrations — **não implementado**. O schema é recriado do zero (DDL completo ou `DROP SCHEMA` no `conftest.py`); não há migração incremental. Uma base criada só com o DDL da Etapa 1 quebra as procedures/triggers da Etapa 2 até rodar o DDL completo à mão.
- [x] Reimplementar as operações da Etapa 1 usando sessões/transações da ORM (`src/etapa2/crud_orm.py`) — self-check: `python -m src.etapa2.crud_orm`
- [x] Demonstrar lazy vs eager loading em pelo menos uma relação — `selectinload` em `listar_atendimentos_paciente` vs lazy default em `ProcedimentoRealizado.procedimento`
- **Bugs conhecidos do modelo** (não bloqueiam nota, registrados para correção futura): `Faturamento.id_atendimento`/`id_procedimento` declarados sem `ForeignKey` (o schema tem `ON DELETE RESTRICT`, o modelo não reflete); `data_hora`/`data_hora_inicio` anotados `Mapped[str]` mas a coluna é `DateTime` (o driver devolve `datetime`, não `str`).

### 5. Consultas avançadas com ORM (1,0 pt) — feito
- [x] Preceptores que supervisionaram residentes que atenderam pacientes flamenguistas
- [x] Último atendimento de cada paciente (data, residente, preceptor, procedimentos)
- [x] % de procedimentos de alto risco por residente
- Implementado em `../src/etapa2/consultas_avancadas.py`, documentado em [`05-aplicacao/05-consultas_avancadas.md`](05-aplicacao/05-consultas_avancadas.md).

### 6. Concorrência e transações (1,0 pt) — feito
- [x] Cenário de duas transações concorrentes (threads) escalando o mesmo residente no mesmo dia/turno/unidade, com lock pessimista (`SELECT ... FOR UPDATE`) — uma sucede, a outra é rejeitada com `ConflitoEscalaError`.
- Implementado em `../src/etapa2/concorrencia.py` (rodar com `python -m src.etapa2.concorrencia`), documentado em [`05-aplicacao/06-concorrencia.md`](05-aplicacao/06-concorrencia.md) com log real de execução.

### 7. Entrega final (1 pt extra)
- [x] Tag `v1.0-etapa1` (retroativa, commit `39a1a2d` que fecha a Etapa 1)
- [ ] Tag `v1.0-etapa2`
- [ ] Vídeo de até 8 minutos
- [ ] Relatório de 2 páginas (`relatorio_etapa2.md`) — decisões de trigger vs procedure, escolha da ORM

**Status Etapa 2: itens 1–6 fechados e verificados contra o Postgres real.** Falta só o item 7 (entrega final, fora do escopo de código).

---

## 3. Webapp (opcional, fora da pontuação da Etapa 1/2)

O enunciado permite CLI, web ou desktop como front-end. Foi construída uma API REST em
Flask (`webapp/api/app.py`) sobre o mesmo Postgres da CLI/ORM, e um painel estático em
HTML/CSS/JS puro (`webapp/frontend/`), sem framework.

- [x] API Flask com rotas de dashboard, CRUD de pacientes/atendimentos, listagens de apoio
  (unidades/procedimentos/escalas/profissionais) e os 5 indicadores analíticos da Etapa 1.
- [x] Painel web consumindo a API, com correção de XSS armazenado (helper `esc()` escapando
  toda saída derivada da API antes de ir para o DOM).
- [x] Persistência ponta a ponta verificada: `POST /api/pacientes` e `POST /api/atendimentos`
  gravam no Postgres e sobrevivem a restart da API.
- Documentação completa (rotas, como rodar, decisões de segurança): [`05-aplicacao/04-webapp.md`](05-aplicacao/04-webapp.md).

---

## Estratégia GitHub — main (Etapa 1 + Etapa 2 + webapp) + stage (planejamento)

O requisito ("commits separados por Etapa 1 e Etapa 2") é resolvido com **uma tag**, não com
branches long-lived paralelas — é o recurso nativo pra marcar um corte no histórico sem
duplicar/esconder código:

1. Tag `v1.0-etapa1` **já criada** no commit `39a1a2d` (fim da Etapa 1).
2. `main` é a linha canônica unificada (Etapa 1 + Etapa 2 + webapp), com PRs mergeados via
   `main-parte2`; o corte da Etapa 1 é demarcado pela tag, não por uma branch separada.
3. `stage` guarda este plano/checklist e o histórico intermediário de decisões da Etapa 2.
4. `main-parte2` e `docs/checklist-etapa1` são linhas antigas já absorvidas pela `main` —
   mantidas por histórico, não devem receber commits novos.
5. Para ver o que é da Etapa 2: `git log v1.0-etapa1..main` ou comparar as branches.

**Atenção:** este arquivo pode divergir entre `main` e `stage` até o próximo merge — antes
de confiar no status aqui, cheque `docs/02-checklist.md` na branch mais avançada
(normalmente `main`, verificar com `git log --all` qual tem o commit mais recente).

---

## 7. Stack (referência rápida)

PostgreSQL 16 (Docker) · Python 3.12 · `psycopg2` (Etapa 1) · SQLAlchemy 2.x (Etapa 2;
Alembic ainda não instalado) · Flask + flask-cors (webapp) · `pytest` · Mermaid para o DER.
