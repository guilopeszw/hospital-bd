# Checklist de Progresso — Etapa 1: Sistema de Gestão Hospitalar (SQL Puro)

---

## Estado Geral

- **Progresso estimado Etapa 1**: ~95% — todo o schema, seeds, CRUD, CLI e as 4 consultas analíticas estão implementados e testados.
- Falta apenas: apresentação de 10 minutos (fora do escopo de código) e revisão cruzada do time.

---

## 1. Modelagem

- [x] DER completo em Mermaid (`docs/der/der_hospitalar.md`), cobrindo Pessoa/Paciente/Profissional/Preceptor/Residente, Unidade, Atendimento, Procedimento, Procedimento_Realizado e Escala — nomes e atributos alinhados ao DDL real.
- [x] Modelo relacional completo (`docs/normalizacao.md`, seções 1 e 3).
- [x] Normalização até 3FN justificada para todas as tabelas, incluindo a prova não-trivial de 2FN de `PROCEDIMENTO_REALIZADO` (chave composta).
- [ ] Exportar DER para PDF (hoje só Mermaid — pendência de entrega, não de modelagem).

## 2. Implementação do BD

- [x] DDL completo em `sql/ddl/01`–`11`: Pessoa, Paciente, Profissional, Preceptor, Residente, Procedimento, Atendimento, Procedimento_Realizado, Unidade, Escala — todos UUID, com PK/FK/CHECK/UNIQUE/NOT NULL.
- [x] Seeds mínimos exigidos: 5 pacientes, 5 preceptores, 5 residentes (`sql/dml/01`–`03`), 10 procedimentos + 10 atendimentos + 10 procedimento_realizado (`04`), 3 unidades (`05`), 8 escalas (`06`).

## 3. CRUD e consultas básicas (SQL puro)

- [x] Inserir atendimento (validando paciente/residente/preceptor) — `src/etapa1/atendimento_crud.py::inserir_atendimento` + `sql/queries/inserir_atendimentos.sql`.
- [x] Listar atendimentos de um paciente (ordenado por data) — `listar_atendimentos_paciente` + `.sql` equivalente.
- [x] Listar procedimentos realizados em um atendimento — `listar_procedimentos_atendimento` + `.sql` equivalente.
- [x] Atualizar dados de paciente (convênio/alergias) — `atualizar_paciente` + `.sql` equivalente.
- [x] Remover procedimento realizado (bloqueado se `faturado = TRUE`) — `remover_procedimento_realizado` + `.sql` equivalente; testado em `tests/unit/test_negocio.py`.
- [x] Tempo médio de duração de atendimentos por residente — `tempo_medio_por_residente` + `.sql` equivalente.
- [x] CLI via `argparse` (stdlib) em `src/etapa1/atendimento_crud.py` cobrindo todas as operações acima.

## 4. Consultas analíticas

- [x] Ranking de residentes por número de atendimentos — `ranking_residentes` + `sql/queries/ranking_residentes_atendimentos.sql`.
- [x] Preceptores com +5 atendimentos num mês — `preceptores_mais_atendimentos_mes` + `sql/queries/preceptores_mais_atendimentos_mes.sql`.
- [x] Plantões por unidade/residente no mês corrente — `plantoes_por_unidade_mes` + `sql/queries/plantoes_por_unidade_residente_mes.sql` (usa `generate_series` para mapear `dia_semana` recorrente aos dias reais do mês).
- [x] Pacientes sem procedimento de risco ALTO — `pacientes_sem_procedimento_risco_alto` + `sql/queries/pacientes_sem_procedimento_risco_alto.sql` (depende da coluna `nivel_risco` adicionada em `PROCEDIMENTO`).

## 5. Documentação e apresentação

- [x] `README.md` com instruções de instalação, Docker, seeds, testes e uso da CLI.
- [ ] Apresentação de 10 minutos demonstrando as funcionalidades (a cargo do time, fora do escopo de código).
- [ ] Revisão cruzada do modelo (cada pessoa revisa o domínio de outra) — recomendado antes da entrega final.

---

## Testes automatizados

- `tests/conftest.py` recria o schema do zero a cada sessão de teste (`DROP SCHEMA public CASCADE`) e aplica todo o DDL `01`–`11`.
- `tests/unit/test_core_entities.py`: 5 testes sobre Pessoa/Paciente (CPF único, regex, grupo sanguíneo, default `is_flamengo`).
- `tests/unit/test_negocio.py`: 6 testes sobre as tabelas de negócio (FK de Atendimento, UNIQUE de Escala, permissão de mesmo preceptor com residentes diferentes, bloqueio de remoção por `faturado`, enum de `nivel_risco`, CHECK de `capacidade_leitos`).

## Decisões de modelagem registradas

- `ESCALA` guarda um plantão **recorrente semanal** (`dia_semana` categórico + `turno`), não uma data concreta — por isso a consulta "plantões no mês corrente" usa `generate_series` para contar ocorrências reais no calendário.
- `nivel_risco` (enum `BAIXO`/`MEDIO`/`ALTO`) foi adicionado em `PROCEDIMENTO` (não em `PROCEDIMENTO_REALIZADO`) — é uma classificação do procedimento em si, não da execução específica.
- `ESCALA` usa dois FKs distintos (`id_residente`, `id_preceptor`) em vez de um FK genérico — a regra "um só preceptor por residente/plantão" fica garantida pela própria `UNIQUE(id_unidade, dia_semana, turno, id_residente)`, sem precisar de trigger (isso é suficiente para a Etapa 1; a Etapa 2 pode adicionar `trg_check_sobreposicao_escala` para impedir sobreposição de um mesmo residente/preceptor em unidades diferentes no mesmo dia/turno).
