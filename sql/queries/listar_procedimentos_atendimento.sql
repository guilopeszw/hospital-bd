-- ============================================================
-- CRUD: Listar procedimentos realizados em um atendimento
-- com nome, quantidade e tempo real gasto.
--
-- Substitua o UUID abaixo pelo id do atendimento desejado.
-- ============================================================

SELECT
    pr.id_atendimento,
    proc.nome              AS procedimento,
    pr.quantidade,
    pr.tempo_real_minutos,
    pr.observacao,
    pr.faturado
FROM PROCEDIMENTO_REALIZADO pr
JOIN PROCEDIMENTO proc ON pr.id_procedimento = proc.id_procedimento
WHERE pr.id_atendimento = 'e1111111-1111-1111-1111-111111111111'  -- substituir pelo UUID real
ORDER BY proc.nome;
