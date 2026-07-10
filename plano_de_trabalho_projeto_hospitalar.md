# Plano de Trabalho — Sistema de Gestão Hospitalar (Dra. Yuska Maritan Brito)

Grupo de 3 pessoas, domínio majoritário em Python. Este documento organiza stack, arquitetura, fluxo de Git/GitHub, divisão de papéis e cronograma em sprints para as duas etapas do projeto.

---

## 1. Stack de tecnologias

A combinação abaixo aproveita o domínio de Python do grupo e cobre todos os objetivos de aprendizagem (SQL puro, ORM, triggers, procedures, transações).

- **Banco de dados:** PostgreSQL (suporta JSON, triggers, procedures em PL/pgSQL, locks, e é o mais usado em produção — bom para currículo).
- **Linguagem:** Python 3.12.
- **Etapa 1 (SQL puro):** `psycopg2` ou `psycopg3` para executar os scripts SQL direto.
- **Etapa 2 (ORM):** SQLAlchemy 2.x (ORM + Core), já que é recomendado no enunciado e tem boa curva de aprendizado.
- **Migrações:** Alembic (integra com SQLAlchemy, ajuda a versionar o schema entre Etapa 1 e Etapa 2).
- **Frontend/Interface:** CLI com `Typer` ou `argparse` na Etapa 1; opcionalmente evoluir para uma API com `FastAPI` + interface simples (Streamlit ou só Swagger/Postman) na Etapa 2 — isso também ajuda a demonstrar a ORM de forma visual no vídeo final.
- **Ambiente:** Docker + docker-compose (um container Postgres + um container da app) — facilita rodar o projeto igual nas três máquinas e evita o clássico "na minha máquina funciona".
- **Testes:** `pytest` (principalmente Etapa 2, para os cenários de concorrência e triggers).
- **Modelagem do DER:** dbdiagram.io, drawSQL ou draw.io (exportar PDF — pedido explicitamente no enunciado).
- **Gestão do projeto:** GitHub Projects (Kanban) + Issues + Milestones.

---

## 2. Estrutura do repositório

```
hospital-db-project/
├── docs/
│   ├── der/                  # Diagramas (DER, modelo relacional)
│   ├── normalizacao.md       # Justificativas 3FN/BCNF
│   ├── decisoes/             # ADRs (Architecture Decision Records)
│   └── relatorio_etapa2.md
├── sql/
│   ├── ddl/                  # CREATE TABLE, constraints
│   ├── dml/                  # Dados de teste (seed)
│   ├── consultas/             # Consultas básicas e analíticas (.sql)
│   ├── procedures/            # Stored procedures
│   ├── triggers/
│   └── views/
├── src/
│   ├── etapa1/                # Scripts Python com psycopg (CRUD via SQL puro)
│   ├── etapa2/
│   │   ├── models/             # Classes ORM (SQLAlchemy)
│   │   ├── repositories/       # Camada de acesso a dados
│   │   ├── services/           # Regras de negócio
│   │   └── api/                # Endpoints FastAPI (opcional)
│   └── cli/
├── tests/
├── alembic/
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

A separação `sql/` vs `src/` deixa claro para o professor o que é "SQL puro" (Etapa 1) e o que é ORM (Etapa 2), além de facilitar a correção.

---

## 3. Fluxo de Git e GitHub

### Branches

- **`main`**: sempre estável, é o que pode ser apresentado/avaliado. Só recebe merge via Pull Request vindo de `develop`, normalmente ao fim de cada etapa ou sprint relevante.
- **`develop`**: branch de integração contínua. Todo trabalho em andamento converge para ela.
- **Branches de feature**: criadas a partir de `develop`, nomeadas com padrão `tipo/descricao-curta`:
  - `feat/ddl-tabelas-pessoa`
  - `feat/consulta-ranking-residentes`
  - `fix/constraint-escala-unica`
  - `docs/der-justificativas`
  - `chore/setup-docker`

### Fluxo de trabalho

1. Pegar uma Issue do board (GitHub Projects).
2. Criar branch a partir de `develop` atualizada: `git checkout develop && git pull && git checkout -b feat/nome-da-task`.
3. Comitar com mensagens no padrão **Conventional Commits**: `feat: adiciona DDL da tabela ATENDIMENTO`, `fix: corrige FK de PROCEDIMENTO_REALIZADO`, `docs: adiciona justificativa de normalização`.
4. Abrir Pull Request para `develop`, vinculando a Issue (`Closes #12`).
5. Pelo menos **1 outra pessoa do grupo revisa o PR** antes do merge — mesmo sendo um trabalho acadêmico, isso treina code review e evita que erros de SQL/lógica passem direto.
6. Ao final de cada sprint, abrir PR de `develop` para `main` com uma tag de versão (`v0.1-etapa1`, `v1.0-etapa1`, `v1.0-etapa2`, etc.) — isso também atende ao requisito de "commits separados por Etapa 1 e Etapa 2".

### Boas práticas adicionais

- Issues do GitHub para cada task da seção 5, com labels: `etapa-1`, `etapa-2`, `modelagem`, `sql`, `orm`, `triggers`, `docs`, `testes`.
- Milestones: "Etapa 1 — Modelagem", "Etapa 1 — Implementação", "Etapa 2 — Procedures/Triggers", "Etapa 2 — ORM".
- Template de PR simples com checklist (testou localmente? atualizou docs? rodou as migrations?).

---

## 4. Divisão da equipe

Em vez de dividir por "pessoa fixa = um arquivo só", o ideal é dividir por **domínio funcional**, com rotação de responsabilidades entre etapas — assim todo mundo passa por SQL puro, ORM e triggers/procedures (importante para a apresentação e para o aprendizado individual).

| Papel | Responsabilidade principal | Pessoa sugerida |
|---|---|---|
| **A — Modelagem & Dados Core** | DER, modelo relacional, DDL de PESSOA/PACIENTE/PROFISSIONAL/PRECEPTOR/RESIDENTE, normalização, seed de dados de pacientes/profissionais | Pessoa 1 |
| **B — Atendimentos & Procedimentos** | DDL de ATENDIMENTO/PROCEDIMENTO/PROCEDIMENTO_REALIZADO, CRUD e consultas relacionadas, seed de atendimentos/procedimentos | Pessoa 2 |
| **C — Unidades, Escalas & Infraestrutura** | DDL de UNIDADE/ESCALA, consultas analíticas, Docker/CI, setup do repositório | Pessoa 3 |

Na Etapa 2, cada pessoa migra "seu" domínio para ORM e implementa as triggers/procedures/views relacionadas a ele (ex.: quem fez ATENDIMENTO implementa `trg_audita_atendimento`; quem fez ESCALA implementa `trg_check_sobreposicao_escala` e `sp_reajustar_escala`). Documentação, testes e consultas avançadas finais são distribuídos de forma cruzada para garantir revisão por outra pessoa.

---

## 5. Cronograma em Sprints

Considerando 4-5 semanas por etapa, sugiro **sprints semanais** com reunião curta de planejamento no início e revisão/retrospectiva no fim de cada semana.

### Etapa 1 (5 semanas)

**Sprint 1 — Setup & Modelagem conceitual**
- Configurar repositório (estrutura de pastas, README inicial, .gitignore, docker-compose com Postgres).
- Configurar branches `main`/`develop`, board do GitHub Projects, Issues iniciais.
- Construir o DER completo (entidades, relacionamentos, cardinalidades, especialização Pessoa → Paciente/Profissional → Preceptor/Residente).
- Escrever justificativas de cardinalidade e de especialização em `docs/`.
- *Entregável:* DER em PDF + repositório configurado.

**Sprint 2 — Modelo relacional e normalização**
- Derivar o modelo relacional completo a partir do DER (tabelas, PKs, FKs).
- Documento de normalização (1FN, 2FN, 3FN) com justificativas por tabela.
- Revisão cruzada: cada pessoa revisa o modelo de outra (evita visão de túnel).
- *Entregável:* `docs/normalizacao.md` + diagrama do modelo relacional.

**Sprint 3 — DDL e seed de dados**
- Cada pessoa escreve o DDL (`CREATE TABLE`) do seu domínio com PK, FK, `CHECK`, `NOT NULL`, `UNIQUE`.
- Integrar os scripts em `sql/ddl/`, garantir que rodam em sequência sem erro de dependência.
- Escrever os `INSERT` de dados de teste (mínimo exigido: 5 pacientes, 5 residentes, 5 preceptores, 3 unidades, 10 atendimentos, 10 procedimentos realizados).
- *Entregável:* banco criado via Docker, populado com dados de teste.

**Sprint 4 — CRUD e consultas básicas**
- Implementar em Python (psycopg) as operações:
  - Inserir atendimento (validando existência de paciente/residente/preceptor).
  - Listar atendimentos de um paciente (ordenado por data).
  - Listar procedimentos realizados em um atendimento.
  - Atualizar dados de paciente.
  - Remover procedimento realizado com flag de faturamento.
  - Calcular tempo médio de atendimento por residente.
- Organizar como CLI simples (`src/cli`) para facilitar a demonstração.
- *Entregável:* CLI funcional cobrindo todas as operações de CRUD.

**Sprint 5 — Consultas analíticas, README e apresentação**
- Implementar as 4 consultas analíticas (ranking de residentes, preceptores com +5 atendimentos/mês, plantões por unidade no mês, pacientes sem procedimentos de risco ALTO).
- Finalizar README (como instalar, subir o Docker, rodar os scripts e a CLI).
- Preparar apresentação de 10 minutos (dividir partes entre os três: modelagem, implementação, consultas/demo).
- *Entregável:* PR final `develop → main` com tag `v1.0-etapa1`.

---

### Etapa 2 (4-5 semanas)

**Sprint 6 — Stored Procedures**
- `sp_registrar_atendimento_completo` (transação com rollback em caso de falha).
- `sp_calcular_tempo_medio_espera`.
- `sp_reajustar_escala` (com checagem de conflito).
- Testes manuais/automatizados de cada procedure.
- *Entregável:* procedures em `sql/procedures/`, demonstradas via script de teste.

**Sprint 7 — Triggers e Views**
- `trg_check_sobreposicao_escala`, `trg_audita_atendimento` (com tabela `AUDITORIA_ATENDIMENTO`), `trg_atualiza_media_procedimentos`.
- `vw_pacientes_internados`, `vw_residentes_sem_supervisor`, `vw_estatisticas_atendimentos_mensal`.
- Testes simples mostrando o gatilho disparando corretamente.
- *Entregável:* triggers e views funcionando, com prints/logs de evidência.

**Sprint 8 — Migração para ORM (SQLAlchemy)**
- Modelar todas as entidades como classes SQLAlchemy (incluindo herança Pessoa/Paciente/Profissional via Joined Table Inheritance).
- Configurar Alembic para gerar/aplicar migrations a partir desses models.
- Reimplementar as operações da Etapa 1 usando sessões/transações da ORM.
- Demonstrar lazy vs eager loading em pelo menos uma relação (ex.: `Atendimento.procedimentos`).
- *Entregável:* camada `src/etapa2/models` e `repositories` completas.

**Sprint 9 — Consultas avançadas com ORM + Concorrência**
- Implementar com a DSL da ORM:
  - Preceptores que supervisionaram residentes que atenderam pacientes flamenguistas.
  - Último atendimento de cada paciente (data, residente, preceptor, procedimentos).
  - Percentual de procedimentos de alto risco por residente.
- Cenário de concorrência: duas "transações" tentando escalar o mesmo residente no mesmo dia/turno/unidade, com lock otimista (versionamento) ou pessimista (`SELECT ... FOR UPDATE`), com logs comprovando o tratamento.
- *Entregável:* testes em `tests/` cobrindo consultas e concorrência.

**Sprint 10 — Documentação, relatório e vídeo final**
- Relatório de 2 páginas sobre decisões (triggers vs procedures, escolha da ORM, etc.) em `docs/relatorio_etapa2.md`.
- Revisão geral do README, organização dos commits por etapa, tags de release.
- Gravação do vídeo de até 8 minutos (cada um apresenta a parte que implementou).
- *Entregável:* PR final `develop → main` com tag `v1.0-etapa2`, repositório finalizado.

---

## 6. Boas práticas gerais

- **Reuniões curtas semanais** (15-20 min): o que foi feito, o que vai ser feito, impedimentos — formato simples de "daily/weekly" ajuda a evitar acúmulo de trabalho no fim.
- **Documentação viva**: atualizar `docs/` a cada sprint, não deixar tudo para o final — principalmente as justificativas de normalização e as ADRs (decisões como "por que Postgres", "por que SQLAlchemy", "por que essa estratégia de herança").
- **Padronização de código**: usar `black`/`ruff` para formatação Python e SQL formatado de forma consistente (indentação, maiúsculas para palavras-chave SQL).
- **Variáveis de ambiente**: nunca commitar credenciais; usar `.env` + `.env.example`.
- **Issues pequenas**: quebrar tasks grandes (ex.: "Sprint 4") em Issues de 1-2 dias cada, isso facilita acompanhamento no Kanban e distribuição de carga entre os três.

---

## 7. Status real e plano personalizado de fechamento da Etapa 1 (análise de 2026-07-10)

> Este documento (seções 1-6) foi o planejamento inicial gerado antes de o time começar a codar. Ele **não vem sendo seguido à risca**: o time convergiu para uma estrutura mais simples do que a sugerida (`sql/queries/` em vez de `sql/consultas/`, um único módulo `src/etapa1/atendimento_crud.py` em vez de `src/etapa1/models/repositories/services`). Esta seção documenta o estado real do repositório, os gaps encontrados contra `projeto_bd.md`, e o plano usado para fechar a Etapa 1. **Etapa 2 está fora de escopo por enquanto** — o foco é terminar a Etapa 1.

### 7.1 O que já estava pronto antes desta análise

- Schema core (`sql/ddl/01`-`06`): Pessoa → Paciente/Profissional → Preceptor/Residente, 100% UUID, CHECKs de CPF/grupo sanguíneo, enums de papel e ano de residência.
- Schema de negócio (`sql/ddl/07_procedimento.sql`, `08_atendimento.sql`, `09_procedimento_realizado.sql`): PROCEDIMENTO, ATENDIMENTO, PROCEDIMENTO_REALIZADO, todos em UUID, FKs corretas, PK composta em PROCEDIMENTO_REALIZADO, flag `faturado` já presente (mergeado via PR `feat/crud-atendimentos-procedimentos` durante esta própria análise).
- Seeds de negócio (`sql/dml/04_seed_atendimentos.sql`): 10 procedimentos, 10 atendimentos, 10 procedimento_realizado.
- CRUD em Python (`src/etapa1/atendimento_crud.py`): 7 das 8 operações pedidas, via psycopg2 puro.
- Queries de referência em `sql/queries/*.sql` (6 dos 7 arquivos preenchidos).
- Arquivos legados incompatíveis (schema paralelo em INT/SERIAL) já haviam sido removidos.

### 7.2 Gaps encontrados contra `projeto_bd.md` (Etapa 1)

1. Tabela `UNIDADE` — não existia.
2. Tabela `ESCALA` — não existia.
3. `PROCEDIMENTO` sem coluna de nível de risco (bloqueava a consulta analítica "pacientes sem procedimento ALTO").
4. `sql/queries/inserir_atendimentos.sql` existia mas estava vazio.
5. Só 1 das 4 consultas analíticas tinha arquivo `.sql` dedicado.
6. `tests/conftest.py` só aplicava DDL `01`-`06`; nada testava Atendimento/Procedimento/Escala/Unidade.
7. `docs/der/der_hospitalar.md` divergia do schema real: tabela de junção com nome/atributos errados (`ATENDIMENTO_PROCEDIMENTO` em vez de `PROCEDIMENTO_REALIZADO`), `UNIDADE_HOSPITALAR` com atributos errados, `ESCALA_PLANTAO` com FK genérico único em vez de residente+preceptor, e uma entidade `INTERNACAO` fora do escopo da Etapa 1.
8. `docs/normalizacao.md` só cobria as 5 tabelas core.
9. Não existia `README.md` na raiz.
10. `docs/checklist_etapa1.md` estava desatualizado (dizia "domínio operacional: 0%", o que já não era verdade).

### 7.3 Decisões de schema tomadas

- **`ESCALA`**: dois FKs distintos (`id_residente`, `id_preceptor`) em vez de um FK genérico — a regra "um só preceptor supervisor por residente/plantão" já fica garantida pela própria `UNIQUE(id_unidade, dia_semana, turno, id_residente)` (que não inclui `id_preceptor`), sem precisar de trigger. A regra "mesmo preceptor pode supervisionar vários residentes no mesmo plantão" também já é permitida automaticamente por essa mesma unique não incluir o preceptor.
- **`UNIDADE.tipo`**: `VARCHAR + CHECK IN (...)` (Enfermaria/UTI/Pronto-Socorro/Ambulatorio), mesmo padrão já usado para `grupo_sanguineo`.
- **`PROCEDIMENTO.nivel_risco`**: enum (`BAIXO`/`MEDIO`/`ALTO`) em vez de `VARCHAR+CHECK` — evita erro de digitação silencioso já que `'ALTO'` é comparado literalmente na consulta analítica.
- **Consulta "plantões por unidade no mês corrente"**: como `ESCALA` guarda um plantão recorrente semanal (`dia_semana`), não uma data concreta, a consulta usa `generate_series` nativo do Postgres para varrer os dias do mês e mapear para `dia_semana_enum` — sem precisar de coluna de data nova.

### 7.4 O que foi implementado nesta análise (10/07/2026)

- `sql/ddl/01_enums.sql`: + `dia_semana_enum`, `turno_enum`, `nivel_risco_enum`.
- `sql/ddl/07_procedimento.sql`: + coluna `nivel_risco`.
- `sql/ddl/10_unidade.sql`, `sql/ddl/11_escala.sql`: tabelas novas.
- `sql/dml/04_seed_atendimentos.sql`: + valores de `nivel_risco` nos procedimentos, 1 linha de `PROCEDIMENTO_REALIZADO` com `faturado = TRUE`.
- `sql/dml/05_seed_unidades.sql`, `sql/dml/06_seed_escalas.sql`: seeds novos (3 unidades, 8 escalas).
- `tests/conftest.py`: DDL `07`-`11` incluído no setup; reset de schema (`DROP SCHEMA public CASCADE`) adicionado para permitir rodar os testes mais de uma vez contra o mesmo volume Docker.
- `tests/unit/test_negocio.py` (novo): 6 testes cobrindo FK de Atendimento, UNIQUE de Escala, caso permitido (mesmo preceptor/residentes diferentes), bloqueio de remoção por `faturado`, enum de `nivel_risco` inválido, CHECK de `capacidade_leitos`.
- `sql/queries/inserir_atendimentos.sql`, `preceptores_mais_atendimentos_mes.sql`, `plantoes_por_unidade_residente_mes.sql`, `pacientes_sem_procedimento_risco_alto.sql`: preenchidos/criados.
- `src/etapa1/atendimento_crud.py`: conexão via `DATABASE_URL` (em vez de credenciais hardcoded), + `plantoes_por_unidade_mes()` e `pacientes_sem_procedimento_risco_alto()`, CLI via `argparse` (stdlib, sem dependência nova) substituindo a demo hardcoded do `__main__`.

### 7.5 Pendente (próximos passos)

- [ ] Rodar a suíte de testes contra o container Docker para validar as mudanças de schema (bloqueado nesta sessão por falta de `pg_config`/`psycopg2` no ambiente local — ver seção "Como rodar" abaixo).
- [ ] Corrigir `docs/der/der_hospitalar.md` (nomes/atributos da tabela de junção, `UNIDADE`, `ESCALA`, remover `INTERNACAO` do escopo da Etapa 1).
- [ ] Completar `docs/normalizacao.md` com as 5 tabelas de negócio.
- [ ] Criar `README.md` na raiz.
- [ ] Reescrever `docs/checklist_etapa1.md` para refletir o estado real.
