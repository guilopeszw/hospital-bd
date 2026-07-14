-- ============================================================
-- CONSULTA ANALÍTICA 1: Ranking de residentes por atendimentos
-- Mostra nome do residente e total de atendimentos realizados,
-- do mais ativo para o menos ativo.
--
-- LEFT JOIN a partir de RESIDENTE: um residente sem nenhum
-- atendimento aparece no ranking com total 0 (com INNER JOIN
-- ele sumiria da lista).
-- GROUP BY pelo id (não pelo nome): dois residentes homônimos
-- continuam sendo linhas distintas.
-- ============================================================

SELECT
    p.nome                  AS residente,
    res.ano_residencia,
    COUNT(a.id_atendimento) AS total_atendimentos
FROM RESIDENTE res
JOIN PROFISSIONAL pf ON pf.id_pessoa = res.id_pessoa
JOIN PESSOA       p  ON p.id_pessoa  = res.id_pessoa
LEFT JOIN ATENDIMENTO a ON a.id_residente = res.id_pessoa
GROUP BY res.id_pessoa, p.nome, res.ano_residencia
ORDER BY total_atendimentos DESC, p.nome;
