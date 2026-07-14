-- ============================================================
-- CRUD: Listar procedimentos realizados em um atendimento
-- com nome, quantidade, tempo real gasto e situação de faturamento.
--
-- Substitua o UUID abaixo pelo id do atendimento desejado.
-- ============================================================

SELECT
    pr.id_atendimento,
    proc.nome              AS procedimento,
    proc.nivel_risco,
    pr.quantidade,
    pr.tempo_real_minutos,
    pr.observacao,
    (f.id_faturamento IS NOT NULL) AS faturado,
    f.valor                AS valor_faturado
FROM PROCEDIMENTO_REALIZADO pr
JOIN PROCEDIMENTO proc ON pr.id_procedimento = proc.id_procedimento
LEFT JOIN FATURAMENTO f
       ON f.id_atendimento  = pr.id_atendimento
      AND f.id_procedimento = pr.id_procedimento
WHERE pr.id_atendimento = 'e1111111-1111-1111-1111-111111111111'  -- substituir pelo UUID real
ORDER BY proc.nome;
