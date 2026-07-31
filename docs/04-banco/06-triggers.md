# Triggers — Etapa 2

Regras que o schema declarativo (PK/FK/CHECK/UNIQUE) não consegue expressar
sozinho.

**Localização:** [`../../sql/triggers/`](../../sql/triggers/)

---

| Trigger | Evento | O que garante |
|---|---|---|
| `trg_check_sobreposicao_escala` | `BEFORE INSERT/UPDATE` em `ESCALA` | Um residente não pode estar em duas unidades no mesmo dia/turno |
| `trg_audita_atendimento` | `AFTER INSERT/UPDATE/DELETE` em `ATENDIMENTO` | Registra o antes/depois em `AUDITORIA_ATENDIMENTO` |
| `trg_atualiza_media_procedimentos` | `AFTER INSERT/UPDATE/DELETE` em `PROCEDIMENTO_REALIZADO` | Recalcula `PROCEDIMENTO.media_tempo_procedimento` |

---

## `trg_check_sobreposicao_escala`

A `UNIQUE (id_unidade, dia_semana, turno, id_residente)` já barra duplicata
exata, mas **não** impede o mesmo residente escalado em duas unidades diferentes
no mesmo dia/turno — fisicamente impossível. Este trigger fecha esse buraco:
antes de inserir/atualizar, conta escalas do mesmo residente/dia/turno em outra
unidade e faz `RAISE` se houver.

## `trg_audita_atendimento`

Grava uma linha em `AUDITORIA_ATENDIMENTO` a cada operação sobre `ATENDIMENTO`,
com `dados_antigos`/`dados_novos` em `JSONB` (`to_jsonb(OLD)` / `to_jsonb(NEW)`).
A tabela de auditoria **não** tem FK para `ATENDIMENTO` de propósito: o log deve
sobreviver à exclusão do atendimento original.

## `trg_atualiza_media_procedimentos`

Mantém `PROCEDIMENTO.media_tempo_procedimento` como a média de
`tempo_real_minutos` de todas as execuções daquele procedimento. Um `UPDATE` pode
trocar o `id_procedimento` da linha, então recalcula tanto o procedimento novo
(`NEW`) quanto o antigo (`OLD`) quando diferem.

---

## Triggers vs. Procedures (decisão de projeto)

- **Trigger** para invariantes que devem valer **sempre**, independentemente de
  quem escreve (sobreposição de escala, auditoria, média derivada). São reativos
  e não podem ser esquecidos por um caminho de escrita.
- **Procedure** para operações compostas que a aplicação **invoca**
  explicitamente (registrar atendimento completo, reajustar escala). São
  transações de negócio, não invariantes.
