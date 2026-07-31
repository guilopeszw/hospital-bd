# Plano de Trabalho — Sistema de Gestão Hospitalar

Este documento substitui o planejamento genérico anterior (sprints fixos, divisão de papéis por pessoa, etc. — não estava sendo seguido e não ajudava a saber "onde estamos"). A partir de agora ele é só isto: **um checklist operacional** ligado aos arquivos reais do repo, mais decisões de organização e estratégia de entrega. A fonte de verdade dos requisitos continua sendo [`00-especificacao.md`](./00-especificacao.md).

---

## 1. Checklist — Etapa 1 (SQL puro)

### 1. Modelagem (2 pts)
- [x] DER completo — [`03-modelagem/01-der.md`](03-modelagem/01-der.md) (Mermaid)
- [ ] Exportar o DER para PDF (hoje só existe em Mermaid — é um requisito explícito da entrega)
- [x] Modelo relacional completo — [`03-modelagem/02-normalizacao.md`](03-modelagem/02-normalizacao.md) (seções 1 e 3)
- [x] Normalização até 3FN justificada — `03-modelagem/02-normalizacao.md` (seções 2 e 4, todas as tabelas)

### 2. Implementação do BD (3 pts)
- [x] DDL completo com PK/FK/CHECK/UNIQUE/NOT NULL — [`../sql/ddl/`](../sql/ddl/)
- [x] Seeds mínimos exigidos (5 pacientes, 5 residentes, 5 preceptores, 3 unidades, 10 atendimentos, 10 procedimentos realizados) — [`../sql/dml/`](../sql/dml/)

### 3. CRUD e consultas básicas (3 pts)
| Operação | Python | SQL puro |
|---|---|---|
- [x] Inserir atendimento (valida paciente/residente/preceptor) | `atendimento_crud.py::inserir_atendimento` | `../sql/queries/inserir_atendimentos.sql` |
- [x] Listar atendimentos de um paciente (por data) | `::listar_atendimentos_paciente` | `../sql/queries/listar_atendimentos_paciente.sql` |
- [x] Listar procedimentos de um atendimento | `::listar_procedimentos_atendimento` | `../sql/queries/listar_procedimentos_atendimento.sql` |
- [x] Atualizar dados de paciente | `::atualizar_paciente` | `../sql/queries/atualizar_paciente.sql` |
- [x] Remover procedimento realizado (bloqueado se `faturado`) | `::remover_procedimento_realizado` | `../sql/queries/remover_procedimento_realizado.sql` |
- [x] Tempo médio de atendimento por residente | `::tempo_medio_por_residente` | `../sql/queries/tempo_medio_atendimento_residente.sql` |
- [x] CLI cobrindo as 6 operações acima — `python -m src.etapa1.atendimento_crud <comando>` (argparse, stdlib)

*(tabela informal — todos os arquivos ficam em [`../src/etapa1/atendimento_crud.py`](../src/etapa1/atendimento_crud.py) e [`../sql/queries/`](../sql/queries/))*

### 4. Consultas analíticas (2 pts)
- [x] Ranking de residentes por atendimentos — `::ranking_residentes` + `../sql/queries/ranking_residentes_atendimentos.sql`
- [x] Preceptores com +5 atendimentos no mês — `::preceptores_mais_atendimentos_mes` + `../sql/queries/preceptores_mais_atendimentos_mes.sql`
- [x] Plantões por unidade/residente no mês corrente — `::plantoes_por_unidade_mes` + `../sql/queries/plantoes_por_unidade_residente_mes.sql`
- [x] Pacientes sem procedimento de risco ALTO — `::pacientes_sem_procedimento_risco_alto` + `../sql/queries/pacientes_sem_procedimento_risco_alto.sql`

### 5. Documentação e apresentação (1 pt extra)
- [x] `../README.md` (instalação, Docker, seeds, testes, CLI)
- [ ] Apresentação de 10 minutos (fora do escopo de código — combinar com o time)
- [ ] Revisão cruzada do modelo entre integrantes (recomendado, não bloqueia nota)

**Status Etapa 1: praticamente fechada.** Só falta o que não é código (PDF do DER, apresentação, revisão cruzada).

---

## 2. Checklist — Etapa 2 (avançado)

### 1. Stored Procedures (1,5 pt)
- [x] `sp_registrar_atendimento_completo` (atendimento + lista de procedimentos via JSONB, transação única, rollback verificado) → `../sql/procedures/sp_registrar_atendimento_completo.sql`
- [x] `sp_calcular_tempo_medio_espera` (chegada → 1º procedimento, por unidade) → `../sql/procedures/sp_calcular_tempo_medio_espera.sql`
- [x] `sp_reajustar_escala` (move escalas de um residente, aborta em conflito) → `../sql/procedures/sp_reajustar_escala.sql`

### 2. Triggers (1,5 pt)
- [x] `trg_check_sobreposicao_escala` (BEFORE INSERT/UPDATE em ESCALA — barra mesmo residente em 2 unidades no mesmo dia/turno) → `../sql/triggers/trg_check_sobreposicao_escala.sql`
- [x] `trg_audita_atendimento` + tabela `AUDITORIA_ATENDIMENTO` → `../sql/triggers/trg_audita_atendimento.sql`
- [x] `trg_atualiza_media_procedimentos` (coluna `media_tempo_procedimento` em PROCEDIMENTO) → `../sql/triggers/trg_atualiza_media_procedimentos.sql`

### 3. Views (1,0 pt)
- [x] `vw_pacientes_internados` — entidade `INTERNACAO` criada (DDL 14) para sustentá-la → `../sql/views/vw_pacientes_internados.sql`
- [x] `vw_residentes_sem_supervisor` → `../sql/views/vw_residentes_sem_supervisor.sql`
- [x] `vw_estatisticas_atendimentos_mensal` → `../sql/views/vw_estatisticas_atendimentos_mensal.sql`

### 4. ORM (2,0 pts)
- [x] Modelos SQLAlchemy 2.0 (`src/etapa2/models.py`) — Pessoa/Paciente/Profissional/Preceptor/Residente, Unidade, Atendimento, Procedimento, ProcedimentoRealizado, Faturamento, Escala
- [ ] Alembic para migrations — **não implementado**. O schema é recriado do zero (`DROP SCHEMA` no `conftest.py` ou manual). Exatamente por isso uma base criada na Etapa 1 quebra na Etapa 2 (coluna `media_tempo_procedimento` ausente) — ver seção "Lições aprendidas".
- [x] Reimplementar as operações da Etapa 1 usando sessões/transações da ORM (`src/etapa2/crud_orm.py`) — self-check: `python -m src.etapa2.crud_orm`
- [x] Demonstrar lazy vs eager loading em pelo menos uma relação — `selectinload` em `listar_atendimentos_paciente` vs lazy default em `ProcedimentoRealizado.procedimento`

### 5. Consultas avançadas com ORM (1,0 pt) — **em aberto**
- [ ] Preceptores que supervisionaram residentes que atenderam pacientes flamenguistas
- [ ] Último atendimento de cada paciente (data, residente, preceptor, procedimentos)
- [ ] % de procedimentos de alto risco por residente

### 6. Concorrência e transações (1,0 pt) — **em aberto**
- [ ] Cenário de duas transações concorrentes escalando o mesmo residente no mesmo dia/turno/unidade, com lock otimista ou pessimista + logs

### 7. Entrega final (1 pt extra)
- [x] Tag `v1.0-etapa1` (retroativa, commit `39a1a2d` que fecha a Etapa 1)
- [ ] Tag `v1.0-etapa2`
- [ ] Vídeo de até 8 minutos
- [ ] Relatório de 2 páginas (`relatorio_etapa2.md`) — decisões de trigger vs procedure, escolha da ORM

---

## Estratégia GitHub — main (Etapa 1) + stage (Etapa 2)

O requisito ("commits separados por Etapa 1 e Etapa 2") é resolvido com **uma tag + duas branches**:

1. Tag `v1.0-etapa1` **já criada** no commit `39a1a2d` (fim da Etapa 1).
2. `main` é a linha canônica unificada (Etapa 1 + Etapa 2 + webapp); o corte da Etapa 1 é demarcado pela tag.
3. `stage` é a branch da Etapa 2 (este plano/checklist vive nela). Trabalho novo da Etapa 2 entra por PR para a `stage`, e de lá é mergeado na `main` quando fechar.
4. `main-parte2` e `docs/checklist-etapa1` são linhas antigas já absorvidas pela `main` — mantidas por histórico, não devem receber commits novos.
5. Para ver o que é da Etapa 2: `git log v1.0-etapa1..main` ou comparar as branches.

---

## 7. Stack (referência rápida)

PostgreSQL 16 (Docker) · Python 3.12 · `psycopg2` (Etapa 1) · SQLAlchemy 2.x (Etapa 2; Alembic ainda não instalado) · Flask (webapp) · `pytest` · Mermaid para o DER.
