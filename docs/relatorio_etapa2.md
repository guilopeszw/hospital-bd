# Relatório — Etapa 2: Funcionalidades Avançadas

Sistema de Gestão Hospitalar · PostgreSQL 16 + SQLAlchemy 2.0

## 1. Triggers vs Procedures — critério de escolha

A decisão não foi por preferência, mas por **quem inicia a ação**:

- **Procedure** (`sp_...`) quando a operação é **chamada explicitamente** por quem
  consome o banco (API, CLI, ORM) e representa um caso de uso completo com múltiplos
  passos que precisam ser atômicos. `sp_registrar_atendimento_completo` insere um
  atendimento e sua lista de procedimentos (JSONB) numa única transação — se qualquer
  item falhar, tudo reverte. `sp_reajustar_escala` move várias escalas de um residente
  validando conflito antes de mover. Nos dois casos, o chamador *decide* disparar a
  operação e *recebe* um retorno (UUID, contagem de linhas).

- **Trigger** (`trg_...`) quando a regra precisa valer **sempre**, independente de
  quem grava — inclusive alguém rodando `INSERT` direto via `psql`, sem passar pela
  API. `trg_check_sobreposicao_escala` barra o mesmo residente em duas unidades no
  mesmo dia/turno (BEFORE, cancela a operação); `trg_audita_atendimento` grava
  histórico automático em `AUDITORIA_ATENDIMENTO`; `trg_atualiza_media_procedimentos`
  mantém uma coluna derivada (`PROCEDIMENTO.media_tempo_procedimento`) sempre
  sincronizada. Nenhuma dessas é uma ação que o chamador pede — é consequência
  automática de outra ação.

**Regra aplicada:** se a lógica precisa de um retorno específico e é invocada sob
demanda → procedure. Se é uma invariante do domínio que não pode depender de
disciplina do código cliente, ou um efeito colateral que sempre deve acontecer →
trigger. `sp_reajustar_escala` e `trg_check_sobreposicao_escala` checam conflito de
escala por caminhos diferentes de propósito: a procedure valida o caso feliz do
reajuste em lote, e a trigger é a segunda barreira que pega qualquer `UPDATE`/`INSERT`
em `ESCALA`, mesmo os que não passaram pela procedure.

`BEFORE` vs `AFTER` seguiu a mesma lógica em miniatura: `BEFORE` quando a trigger pode
**impedir** a gravação (`trg_check_sobreposicao_escala` usa `RAISE EXCEPTION`);
`AFTER` quando é **reação** a algo que já foi gravado (auditoria, recálculo de média).

## 2. Escolha da ORM — SQLAlchemy 2.0

Optamos por SQLAlchemy sobre alternativas (Django ORM, Peewee, SQL cru só com
psycopg2) por três motivos concretos ao domínio do projeto:

1. **Suporte nativo a hierarquia de tabelas.** O modelo tem Pessoa como supertipo de
   Paciente/Profissional, e Profissional como supertipo de Preceptor/Residente — um
   padrão de herança por tabela (table-per-subclass) que o SQLAlchemy mapeia
   diretamente via `ForeignKey` na PK da subclasse + `relationship()`, sem exigir um
   framework web inteiro (descartando Django) nem reimplementar navegação de
   relacionamento à mão (descartando SQL cru puro para essa camada).

2. **FK composta de primeira classe.** `FATURAMENTO` referencia a PK composta de
   `PROCEDIMENTO_REALIZADO` (`id_atendimento, id_procedimento`). SQLAlchemy suporta
   isso nativamente via `ForeignKeyConstraint` — Peewee e a maioria das ORMs mais
   simples não modelam FK composta sem gambiarra.

3. **DSL expressiva o bastante para consultas analíticas** (`case()`, `func.avg`,
   `outerjoin`, subqueries, `aliased()` para tabela repetida na mesma query) sem sair
   para SQL cru — as 3 consultas avançadas do item 5 (preceptores de flamenguistas,
   último atendimento por paciente, % de risco alto por residente) usam só a DSL.

## 3. Concorrência — pessimista e otimista lado a lado

Implementamos as duas famílias para o mesmo cenário de disputa (duas transações
escalando o mesmo residente no mesmo slot), não porque o enunciado pedisse as duas,
mas para comparar o trade-off na prática: lock pessimista (`SELECT ... FOR UPDATE`)
serializa antes do conflito, pagando o custo do lock mesmo quando não haveria disputa;
controle otimista deixa as duas transações correrem em paralelo e usa a `UNIQUE` do
banco como detector na escrita, pagando o custo (retrabalho) só em quem perde a
corrida. Ver `docs/05-aplicacao/06-concorrencia.md` para os logs reais das duas
execuções.

## 4. Webapp — por que a Etapa 2 não fica só na CLI/ORM

O painel Flask não reimplementa as regras de negócio em Python: as rotas chamam as
mesmas procedures, views e triggers do banco (`sp_registrar_atendimento_completo`,
`sp_reajustar_escala`, `sp_calcular_tempo_medio_espera`, as 3 views). Isso evita
duplicar lógica de negócio em duas camadas (SQL e API) que poderiam divergir com o
tempo — a fonte de verdade das regras continua sendo o banco, a API é só uma segunda
porta de entrada para elas.
