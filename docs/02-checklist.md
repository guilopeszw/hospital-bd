# Checklist de Progresso — Etapa 1: Sistema de Gestão Hospitalar (SQL Puro)

---

## Estado Geral

- **Progresso Etapa 1**: schema, seeds, CRUD, CLI, consultas analíticas e DER prontos e **verificados contra o Postgres real** (16 testes passando). Entrega do DER em [`03-modelagem/04-diagrama.png`](03-modelagem/04-diagrama.png) + [`03-justificativa_cardinalidades.md`](03-modelagem/03-justificativa_cardinalidades.md) + `DER_e_cardinalidades_atualizado.docx`.
- **Progresso Etapa 2**: items 1–4 (procedures, triggers, views, ORM) implementados e verificados contra o Postgres real. Em aberto: item 5 (consultas avançadas ORM), item 6 (concorrência), item 7 (vídeo + relatório).
- Falta apenas: apresentação de 10 minutos (fora do escopo de código), revisão cruzada do time, e os itens em aberto da Etapa 2.

---

## 1. Modelagem

- [x] DER completo em Mermaid (`03-modelagem/01-der.md`), cobrindo Pessoa/Paciente/Profissional/Preceptor/Residente, Unidade, Atendimento, Procedimento, Procedimento_Realizado, Faturamento e Escala.
- [x] **Entrega do DER**, com a justificativa de cardinalidade (mínimo, máximo e participação) de cada relacionamento e de cada especialização — [`03-modelagem/03-justificativa_cardinalidades.md`](03-modelagem/03-justificativa_cardinalidades.md) + [`04-diagrama.png`](03-modelagem/04-diagrama.png) + `DER_e_cardinalidades_atualizado.docx` (untracked — ainda não commitado).
- [x] Modelo relacional completo (`03-modelagem/02-normalizacao.md`, seções 1 e 3).
- [x] Normalização até 3FN justificada para todas as tabelas, incluindo a prova não-trivial de 2FN de `PROCEDIMENTO_REALIZADO` (chave composta).

## 2. Implementação do BD

- [x] DDL completo em `../sql/ddl/01`–`12`, todos UUID, com PK/FK/CHECK/UNIQUE/NOT NULL.
- [x] Seeds acima do mínimo exigido: 5 pacientes, 5 preceptores, 5 residentes, 3 unidades, 10 procedimentos, **16 atendimentos**, **18 procedimentos realizados**, 8 escalas, 3 faturamentos.
- [x] Volume de seed **calibrado para as consultas analíticas não voltarem vazias**: Dr. Jorge Jesus tem 8 atendimentos em junho/2025 (aparece no `HAVING > 5`) e Dra. Yuska tem exatamente 5 (não aparece — mostra o limite funcionando).

## 3. CRUD e consultas básicas (SQL puro)

- [x] Inserir atendimento (validando paciente/residente/preceptor).
- [x] Listar atendimentos de um paciente (ordenado por data).
- [x] Listar procedimentos realizados em um atendimento (com nível de risco e situação de faturamento).
- [x] Atualizar dados de paciente (convênio/alergias).
- [x] Remover procedimento realizado **apenas se não houver faturamento associado**.
- [x] Tempo médio de duração de atendimentos por residente (`LEFT JOIN`: residente sem atendimento aparece com total 0, em vez de sumir do relatório).
- [x] CLI via `argparse` cobrindo todas as operações acima.

## 4. Consultas analíticas

Todas rodadas contra o banco populado; resultados conferidos:

- [x] Ranking de residentes por número de atendimentos — 5 residentes, líder com 4.
- [x] Preceptores com +5 atendimentos num mês — retorna Dr. Jorge Jesus (8) em 6/2025.
- [x] Plantões por unidade/residente no mês corrente — usa `generate_series` para mapear o `dia_semana` recorrente aos dias reais do calendário.
- [x] Pacientes sem procedimento de risco ALTO — retorna Gabigol, Arrascaeta e Pedro.

## 5. Documentação e apresentação

- [x] `../README.md` com instalação, Docker, seeds, testes, CLI, geração do PDF e tabela das regras de negócio garantidas pelo schema.
- [ ] Apresentação de 10 minutos demonstrando as funcionalidades (a cargo do time).
- [ ] Revisão cruzada do modelo (cada pessoa revisa o domínio de outra) — recomendado antes da entrega.

---

## Testes automatizados — 16 passando

- `../tests/conftest.py` recria o schema do zero a cada sessão (`DROP SCHEMA public CASCADE` + DDL `01`–`14`). Como isso apaga os seeds, refaça o passo 2 do README antes de demonstrar a CLI.
- **Atenção**: o conftest NÃO carrega triggers, procedures e views — cobre só DDL/constraints da Etapa 1. As funções da Etapa 2 (sp_*/fn_*) são validadas manualmente contra o banco (ver seção Etapa 2). Vale adicionar testes automatizados para elas (rollback da `sp_registrar_atendimento_completo`, RAISE da `trg_check_sobreposicao_escala`, `media_tempo_procedimento` recalculada).
- `../tests/unit/test_core_entities.py` (5): CPF único, regex de CPF, grupo sanguíneo, default de `is_flamengo`.
- `../tests/unit/test_negocio.py` (11): FK de Atendimento, UNIQUE de Escala, mesmo preceptor com residentes diferentes, enum de `nivel_risco`, CHECK de `capacidade_leitos`, os 4 casos de faturamento (bloqueia delete, FK RESTRICT, permite delete sem faturamento, não fatura duas vezes) e os 2 de exclusividade de papel.

## Decisões de modelagem registradas

- **Faturamento é entidade, não flag.** O enunciado condiciona a remoção a "não haver faturamento associado" — *associado* implica entidade. `FATURAMENTO` guarda valor e data de emissão, e a FK com `ON DELETE RESTRICT` faz o próprio banco recusar a remoção. A flag booleana `faturado` foi removida: guardava metade do fato e viraria redundância assim que o faturamento ganhasse atributos.
- **Exclusividade de papel sem trigger.** `UNIQUE(id_pessoa, papel_atual)` em PROFISSIONAL + coluna `papel` travada por `CHECK` em PRECEPTOR/RESIDENTE + FK composta `(id_pessoa, papel)`. Um profissional marcado como residente não consegue ganhar linha em PRECEPTOR. A Etapa 1 fica 100% declarativa; triggers ficam para a Etapa 2.
- **`ESCALA` é plantão recorrente semanal** (`dia_semana` categórico + `turno`), não uma data concreta — por isso a consulta "plantões no mês corrente" usa `generate_series` para contar as ocorrências reais no calendário.
- **`nivel_risco`** fica em `PROCEDIMENTO` (classificação do procedimento em si), não em `PROCEDIMENTO_REALIZADO` (que descreve a execução).
- **O DER marca (0,N) de ATENDIMENTO para PROCEDIMENTO_REALIZADO**, e não (1,N): um mínimo obrigatório de um filho não é expressável por FK (exigiria trigger). O diagrama reflete o que o schema garante de fato — a justificativa está na seção 4 do PDF.

---

## Etapa 2 — Funcionalidades Avançadas

Progresso: itens 1–4 implementados e **verificados contra o Postgres real**.

### 1. Stored Procedures — feito
- [x] `sp_registrar_atendimento_completo` (atendimento + procedimentos em JSONB, transação única; rollback verificado).
- [x] `sp_calcular_tempo_medio_espera` (chegada → 1º procedimento, por unidade).
- [x] `sp_reajustar_escala` (move escalas de um residente, aborta em conflito).
- Documentação: [`04-banco/04-procedures.md`](04-banco/04-procedures.md).

### 2. Triggers — feito
- [x] `trg_check_sobreposicao_escala`, `trg_audita_atendimento`, `trg_atualiza_media_procedimentos`.
- Tabela nova `AUDITORIA_ATENDIMENTO` e coluna `PROCEDIMENTO.media_tempo_procedimento`.
- Documentação: [`04-banco/06-triggers.md`](04-banco/06-triggers.md).

### 3. Views — feito
- [x] `vw_pacientes_internados`, `vw_residentes_sem_supervisor`, `vw_estatisticas_atendimentos_mensal`.
- Entidade nova `INTERNACAO` (base da 1ª view).
- Documentação: [`04-banco/05-views.md`](04-banco/05-views.md).

### 4. ORM (SQLAlchemy) — feito
- [x] Operações da Etapa 1 reimplementadas via DSL em `src/etapa2/` (models + crud_orm), com sessões/transações e eager vs lazy loading.
- [ ] **Alembic para migrations — não implementado.** Consequência real observada: base criada na Etapa 1 (sem `PROCEDIMENTO.media_tempo_procedimento`) quebra os triggers/procedures da Etapa 2 até a coluna ser adicionada à mão. Recomendação: adicionar Alembic OU documentar um script de `ALTER TABLE` de migração.
- Documentação: [`05-aplicacao/03-orm.md`](05-aplicacao/03-orm.md).

### Ainda em aberto
- [ ] Item 5 — consultas avançadas via ORM (flamenguistas, último atendimento, % alto risco).
- [ ] Item 6 — concorrência e locks.
- [ ] Item 7 — tag `v1.0-etapa2`, vídeo de até 8 min + relatório de 2 páginas.
- [ ] Commit do `DER_e_cardinalidades_atualizado.docx` (entrega da Etapa 1 ainda untracked).

### Lições aprendidas / bugs pegos na verificação
- **Migração de schema sem Alembic é bug em potencial.** O `conftest.py` recria o schema do zero a cada sessão de teste, então os testes sempre veem o DDL novo. Mas uma base já existente (criada na Etapa 1) NÃO ganha `media_tempo_procedimento` nem `AUDITORIA_ATENDIMENTO`/`INTERNACAO` sozinha — a coluna nova precisa de `ALTER TABLE` manual (ou recriação). Foi exatamente o que aconteceu ao validar as procedures na base real.
- **`src/etapa2/models.py`: `Faturamento.id_atendimento`/`id_procedimento` sem `ForeignKey`** — o schema tem `ON DELETE RESTRICT`, mas o modelo não declara a FK. Não quebra as operações atuais (não há delete via ORM), mas a ORM não reflete o relacionamento. Adicionar `ForeignKey("atendimento.id_atendimento")`/`ForeignKey("procedimento.id_procedimento")` quando o modelo ganhar o relacionamento.
- **`models.py`: `data_hora` anotado como `Mapped[str]` mas coluna `DateTime`** — o driver devolve `datetime`, não `str`. Anotação enganosa; usar `Mapped[datetime]` ou converter na leitura.

### Ajustes de schema da Etapa 2 (aditivos)
- `ATENDIMENTO.id_unidade` — unidade onde o atendimento ocorreu (alimenta a view mensal).
- `PROCEDIMENTO_REALIZADO.data_hora_inicio` — início real do procedimento (base do tempo de espera).
- `PROCEDIMENTO.media_tempo_procedimento` — mantida pelo trigger de média.
- DER atualizado em [`03-modelagem/01-der.md`](03-modelagem/01-der.md).
