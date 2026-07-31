# Stored Procedures — Etapa 2

Regras de negócio transacionais em PL/pgSQL. Implementadas como `FUNCTION`
(e não `PROCEDURE`) para poderem devolver valor via `RETURNS`; o corpo roda na
transação do chamador, então um `RAISE` em qualquer ponto reverte tudo.

**Localização:** [`../../sql/procedures/`](../../sql/procedures/)

---

## Visão geral

| Procedure | Retorna | O que faz |
|---|---|---|
| `sp_registrar_atendimento_completo` | `UUID` | Insere atendimento + lista de procedimentos numa transação única |
| `sp_calcular_tempo_medio_espera` | tabela | Tempo médio chegada → 1º procedimento, por unidade |
| `sp_reajustar_escala` | `INT` | Move as escalas de um residente de um dia/turno para outro |

---

## `sp_registrar_atendimento_completo`

Recebe os dados do atendimento + uma lista de procedimentos como `JSONB` e grava
tudo atomicamente. Se qualquer item da lista violar uma constraint (FK, CHECK),
a função inteira reverte — nada é gravado.

```sql
SELECT sp_registrar_atendimento_completo(
    '2025-07-01 10:00:00', 30,
    '<id_paciente>', '<id_residente>', '<id_preceptor>', '<id_unidade>',
    '[{"id_procedimento":"<id>","tempo_real_minutos":11,"data_hora_inicio":"2025-07-01 10:05:00"},
      {"id_procedimento":"<id>","tempo_real_minutos":13,"data_hora_inicio":"2025-07-01 10:20:00"}]'::jsonb
);
```

- Cada item aceita `id_procedimento`, `quantidade` (default 1), `tempo_real_minutos`, `data_hora_inicio` (default = data_hora do atendimento) e `observacao`.
- **Rollback verificado:** com um `id_procedimento` inexistente, a FK `fk_pr_procedimento` estoura e nenhum atendimento novo é criado.

## `sp_calcular_tempo_medio_espera`

Para cada unidade, calcula a média (minutos) entre a chegada do paciente
(`ATENDIMENTO.data_hora`) e o início do **primeiro** procedimento do atendimento
(`MIN(data_hora_inicio)`).

```sql
SELECT * FROM sp_calcular_tempo_medio_espera();
--  id_unidade | unidade | atendimentos_medidos | espera_media_minutos
```

Atendimentos sem procedimento com início registrado não entram na média.

## `sp_reajustar_escala`

Move **todas** as escalas de um residente que estejam num `(dia, turno)` de
origem para um `(dia, turno)` de destino, desde que não gere conflito na mesma
unidade. Retorna quantas escalas foram movidas; se houver conflito, `RAISE` e
nada muda.

```sql
SELECT sp_reajustar_escala('<id_residente>', 'segunda', 'manha', 'quinta', 'manha');
-- movidas
```

O trigger `trg_check_sobreposicao_escala` é a segunda barreira: mesmo que a
checagem interna falhasse, o `BEFORE UPDATE` ainda impediria sobreposição de um
residente em duas unidades no mesmo dia/turno.
