# Checklist de Progresso — Etapa 1: Sistema de Gestão Hospitalar (SQL Puro)

---

## Estado Geral

- **Progresso Etapa 1**: schema, seeds, CRUD, CLI, consultas analíticas e PDF do DER prontos e **verificados contra o Postgres real** (16 testes passando).
- Falta apenas: apresentação de 10 minutos (fora do escopo de código) e revisão cruzada do time.

---

## 1. Modelagem

- [x] DER completo em Mermaid (`docs/der/der_hospitalar.md`), cobrindo Pessoa/Paciente/Profissional/Preceptor/Residente, Unidade, Atendimento, Procedimento, Procedimento_Realizado, Faturamento e Escala.
- [ ] **PDF de entrega do DER**, com a justificativa de cardinalidade (mínimo, máximo e participação) de cada relacionamento e de cada especialização — pendência de entrega, a cargo do time.
- [x] Modelo relacional completo (`docs/normalizacao.md`, seções 1 e 3).
- [x] Normalização até 3FN justificada para todas as tabelas, incluindo a prova não-trivial de 2FN de `PROCEDIMENTO_REALIZADO` (chave composta).

## 2. Implementação do BD

- [x] DDL completo em `sql/ddl/01`–`12`, todos UUID, com PK/FK/CHECK/UNIQUE/NOT NULL.
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

- [x] `README.md` com instalação, Docker, seeds, testes, CLI, geração do PDF e tabela das regras de negócio garantidas pelo schema.
- [ ] Apresentação de 10 minutos demonstrando as funcionalidades (a cargo do time).
- [ ] Revisão cruzada do modelo (cada pessoa revisa o domínio de outra) — recomendado antes da entrega.

---

## Testes automatizados — 16 passando

- `tests/conftest.py` recria o schema do zero a cada sessão (`DROP SCHEMA public CASCADE` + DDL `01`–`12`). Como isso apaga os seeds, refaça o passo 2 do README antes de demonstrar a CLI.
- `tests/unit/test_core_entities.py` (5): CPF único, regex de CPF, grupo sanguíneo, default de `is_flamengo`.
- `tests/unit/test_negocio.py` (11): FK de Atendimento, UNIQUE de Escala, mesmo preceptor com residentes diferentes, enum de `nivel_risco`, CHECK de `capacidade_leitos`, os 4 casos de faturamento (bloqueia delete, FK RESTRICT, permite delete sem faturamento, não fatura duas vezes) e os 2 de exclusividade de papel.

## Decisões de modelagem registradas

- **Faturamento é entidade, não flag.** O enunciado condiciona a remoção a "não haver faturamento associado" — *associado* implica entidade. `FATURAMENTO` guarda valor e data de emissão, e a FK com `ON DELETE RESTRICT` faz o próprio banco recusar a remoção. A flag booleana `faturado` foi removida: guardava metade do fato e viraria redundância assim que o faturamento ganhasse atributos.
- **Exclusividade de papel sem trigger.** `UNIQUE(id_pessoa, papel_atual)` em PROFISSIONAL + coluna `papel` travada por `CHECK` em PRECEPTOR/RESIDENTE + FK composta `(id_pessoa, papel)`. Um profissional marcado como residente não consegue ganhar linha em PRECEPTOR. A Etapa 1 fica 100% declarativa; triggers ficam para a Etapa 2.
- **`ESCALA` é plantão recorrente semanal** (`dia_semana` categórico + `turno`), não uma data concreta — por isso a consulta "plantões no mês corrente" usa `generate_series` para contar as ocorrências reais no calendário.
- **`nivel_risco`** fica em `PROCEDIMENTO` (classificação do procedimento em si), não em `PROCEDIMENTO_REALIZADO` (que descreve a execução).
- **O DER marca (0,N) de ATENDIMENTO para PROCEDIMENTO_REALIZADO**, e não (1,N): um mínimo obrigatório de um filho não é expressável por FK (exigiria trigger). O diagrama reflete o que o schema garante de fato — a justificativa está na seção 4 do PDF.
