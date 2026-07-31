# Views — Etapa 2

Views analíticas que encapsulam consultas recorrentes.

**Localização:** [`../../sql/views/`](../../sql/views/)

---

| View | O que lista |
|---|---|
| `vw_pacientes_internados` | Pacientes atualmente internados |
| `vw_residentes_sem_supervisor` | Residentes escalados sob preceptor não-doutor |
| `vw_estatisticas_atendimentos_mensal` | Total, duração média e procedimento mais comum por mês/unidade |

---

## `vw_pacientes_internados`

Um paciente está internado quando sua internação **mais recente** ainda não tem
`data_hora_saida`. Usa `DISTINCT ON (id_paciente)` ordenado por
`data_hora_entrada DESC` para pegar a última internação, e filtra as sem alta.

```sql
SELECT * FROM vw_pacientes_internados;
--  id_paciente | paciente | unidade | data_hora_entrada | motivo
```

Depende da entidade `INTERNACAO` (Etapa 2).

## `vw_residentes_sem_supervisor`

Residentes escalados em algum plantão cujo preceptor **não** tem titulação de
doutor. O enunciado trata supervisão adequada como supervisão por doutor. A
comparação normaliza a titulação (`lower(trim(...))`) para casar `Doutor`,
`doutora`, `DOUTOR` etc.

```sql
SELECT DISTINCT residente, titulacao FROM vw_residentes_sem_supervisor;
```

## `vw_estatisticas_atendimentos_mensal`

Agregação por mês e unidade: total de atendimentos, duração média e procedimento
mais comum (`mode() WITHIN GROUP`).

```sql
SELECT mes, unidade, total_atendimentos, duracao_media_minutos, procedimento_mais_comum
FROM vw_estatisticas_atendimentos_mensal;
```

**Nota de projeto:** o total/duração e o procedimento mais comum são calculados em
duas agregações separadas (CTEs `estat` e `proc_comum`). Se fossem um único JOIN,
a duração de um atendimento com N procedimentos entraria N vezes na média,
enviesando o resultado.
