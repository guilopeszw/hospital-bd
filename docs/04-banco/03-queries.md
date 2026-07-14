# Queries SQL — CRUD e Consultas Analíticas

## Visão Geral

10 arquivos SQL divididos em **6 operações CRUD** e **4 consultas analíticas**. Cada operação tem implementação correspondente em Python em `src/etapa1/`.

**Localização:** [`../../sql/queries/`](../../sql/queries/)

---

## CRUD (Operações Básicas)

Mapeamento direto para os requisitos da Etapa 1, seção 3:

### 1. Inserir Atendimento
- **Arquivo:** [`inserir_atendimentos.sql`](../../sql/queries/inserir_atendimentos.sql)
- **Descrição:** Insere atendimento com validação de existência do paciente, residente e preceptor.
- **Técnica SQL:** `INSERT ... VALUES` com subconsultas `EXISTS` ou verificações prévias.

### 2. Listar Atendimentos de um Paciente
- **Arquivo:** [`listar_atendimentos_paciente.sql`](../../sql/queries/listar_atendimentos_paciente.sql)
- **Descrição:** Retorna todos os atendimentos de um paciente, ordenados por data decrescente.
- **Técnica SQL:** Múltiplos `JOIN` (Paciente → Pessoa, Residente → Profissional → Pessoa, Preceptor → Profissional → Pessoa).
- **Requisito:** Etapa 1 §3, item 2.

### 3. Listar Procedimentos de um Atendimento
- **Arquivo:** [`listar_procedimentos_atendimento.sql`](../../sql/queries/listar_procedimentos_atendimento.sql)
- **Descrição:** Lista procedimentos com nome, nível de risco, quantidade, tempo real e situação de faturamento.
- **Técnica SQL:** `JOIN` + `LEFT JOIN` com `FATURAMENTO`. Usa `(f.id_faturamento IS NOT NULL) AS faturado`.
- **Requisito:** Etapa 1 §3, item 3.

### 4. Atualizar Paciente
- **Arquivo:** [`atualizar_paciente.sql`](../../sql/queries/atualizar_paciente.sql)
- **Descrição:** Atualiza convênio e/ou alergias de um paciente.
- **Técnica SQL:** `UPDATE` dinâmico por paciente.
- **Requisito:** Etapa 1 §3, item 4.

### 5. Remover Procedimento Realizado
- **Arquivo:** [`remover_procedimento_realizado.sql`](../../sql/queries/remover_procedimento_realizado.sql)
- **Descrição:** Remove apenas se não houver faturamento associado. Dupla proteção: `NOT EXISTS` no SQL + FK `ON DELETE RESTRICT`.
- **Técnica SQL:** `DELETE` com `NOT EXISTS (SELECT 1 FROM FATURAMENTO ...)`.
- **Requisito:** Etapa 1 §3, item 5.

### 6. Tempo Médio por Residente
- **Arquivo:** [`tempo_medio_atendimento_residente.sql`](../../sql/queries/tempo_medio_atendimento_residente.sql)
- **Descrição:** Média de duração dos atendimentos agrupada por residente.
- **Técnica SQL:** `AVG()`, `LEFT JOIN` (residente sem atendimento aparece com NULL), `GROUP BY`, `ORDER BY`.
- **Requisito:** Etapa 1 §3, item 6.

---

## Analíticas

Mapeamento para os requisitos da Etapa 1, seção 4:

### 7. Ranking de Residentes
- **Arquivo:** [`ranking_residentes_atendimentos.sql`](../../sql/queries/ranking_residentes_atendimentos.sql)
- **Descrição:** Ranking dos residentes por número de atendimentos realizados.
- **Técnica SQL:** `COUNT()` com `LEFT JOIN`, `GROUP BY`, `ORDER BY DESC`.
- **Requisito:** Etapa 1 §4, item 1.

### 8. Preceptores com +5 Atendimentos no Mês
- **Arquivo:** [`preceptores_mais_atendimentos_mes.sql`](../../sql/queries/preceptores_mais_atendimentos_mes.sql)
- **Descrição:** Preceptores que supervisionaram mais de 5 atendimentos em um mês específico.
- **Técnica SQL:** `EXTRACT(YEAR/MONTH FROM data_hora)`, `HAVING COUNT(...) > 5`.
- **Requisito:** Etapa 1 §4, item 2.

### 9. Plantões por Unidade no Mês Corrente
- **Arquivo:** [`plantoes_por_unidade_residente_mes.sql`](../../sql/queries/plantoes_por_unidade_residente_mes.sql)
- **Descrição:** Quantidade de plantões por unidade/residente no mês corrente.
- **Técnica SQL:** `generate_series` para mapear `dia_semana` categórico da escala aos dias reais do calendário. CTE `dias_mes` + CTE `mapa_dia` + `JOIN` com `ESCALA`.
- **Requisito:** Etapa 1 §4, item 3.
- **Nota:** A escala guarda plantão recorrente semanal (não data concreta). `generate_series` resolve a contagem de ocorrências reais no mês.

### 10. Pacientes sem Procedimento de Alto Risco
- **Arquivo:** [`pacientes_sem_procedimento_risco_alto.sql`](../../sql/queries/pacientes_sem_procedimento_risco_alto.sql)
- **Descrição:** Pacientes que nunca realizaram procedimento com `nivel_risco = 'ALTO'`.
- **Técnica SQL:** `NOT EXISTS` com subconsulta correlacionada ligando `ATENDIMENTO` → `PROCEDIMENTO_REALIZADO` → `PROCEDIMENTO`.
- **Requisito:** Etapa 1 §4, item 4.
