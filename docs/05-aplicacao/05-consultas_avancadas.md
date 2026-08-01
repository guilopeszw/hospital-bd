# Consultas avançadas via ORM (Etapa 2 — item 5)

**Localização:** [`../../src/etapa2/consultas_avancadas.py`](../../src/etapa2/consultas_avancadas.py)

As três consultas exigidas no enunciado, além do que já existia em
`crud_orm.py` (reimplementação da Etapa 1). Tudo em DSL do SQLAlchemy.

```bash
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" \
  python -m src.etapa2.consultas_avancadas      # self-check: roda as 3 consultas
```

## 1. Preceptores que supervisionaram residentes que atenderam flamenguistas

`preceptores_supervisionaram_flamenguistas()` — junta ATENDIMENTO → PRECEPTOR
→ PESSOA (preceptor) e ATENDIMENTO → PACIENTE → PESSOA (paciente), filtrando
`is_flamengo = TRUE`. Como PESSOA entra duas vezes na mesma consulta (uma
para o preceptor, outra para o paciente), o lado do preceptor usa
`aliased(Pessoa)` — sem isso o SQLAlchemy não teria como diferenciar os dois
JOINs na mesma tabela.

## 2. Último atendimento de cada paciente

`ultimo_atendimento_por_paciente()` — uma subquery agrega
`MAX(data_hora)` por `id_paciente`; o SELECT principal junta ATENDIMENTO de
volta pela combinação `(id_paciente, data_hora)`. Dá o mesmo resultado de
uma window function (`ROW_NUMBER() OVER (PARTITION BY ...)`), só que mais
direto de ler na DSL. Retorna paciente, data/hora, residente, preceptor e a
lista de procedimentos, com `selectinload` em cascata para evitar N+1 ao
percorrer `residente → profissional → pessoa` (idem preceptor) e
`atendimento → procedimentos → procedimento`.

Caso de borda documentado no código: se um paciente tiver dois atendimentos
com exatamente o mesmo `data_hora`, os dois aparecem — raro o bastante para
não justificar a complexidade extra de uma window function aqui.

## 3. Percentual de procedimentos de alto risco por residente

`percentual_procedimentos_alto_risco_por_residente()` — soma
`quantidade` de PROCEDIMENTO_REALIZADO por residente (via ATENDIMENTO) e,
com `case()`, soma só a parte cujo PROCEDIMENTO tem `nivel_risco = 'ALTO'`.
Usa `outerjoin` em toda a cadeia (mesmo padrão de
`tempo_medio_por_residente` no `crud_orm.py`) para que um residente sem
nenhum procedimento realizado ainda apareça no relatório, com 0/0%. A
divisão fica em Python para não depender do comportamento de divisão por
zero de um dialeto específico de SQL.