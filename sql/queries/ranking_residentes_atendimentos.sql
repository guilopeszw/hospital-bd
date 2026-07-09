-- ============================================================
-- CONSULTA ANALÍTICA 1: Ranking de residentes por atendimentos
-- Mostra nome do residente e total de atendimentos realizados,
-- do mais ativo para o menos ativo.
-- ============================================================

SELECT
    p.nome                      AS residente,
    COUNT(a.id_atendimento)     AS total_atendimentos
FROM ATENDIMENTO a
JOIN RESIDENTE  res ON a.id_residente = res.id_pessoa
JOIN PROFISSIONAL pf ON res.id_pessoa  = pf.id_pessoa
JOIN PESSOA      p  ON pf.id_pessoa   = p.id_pessoa
GROUP BY p.nome
ORDER BY total_atendimentos DESC;
