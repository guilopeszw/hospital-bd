-- ============================================================
-- CONSULTA ANALÍTICA 2: Preceptores com mais de 5 atendimentos
-- supervisionados em um determinado mês.
-- ============================================================

SELECT
    p.nome                  AS preceptor,
    COUNT(a.id_atendimento) AS total_atendimentos
FROM ATENDIMENTO a
JOIN PRECEPTOR    pre ON a.id_preceptor = pre.id_pessoa
JOIN PROFISSIONAL pf  ON pre.id_pessoa  = pf.id_pessoa
JOIN PESSOA       p   ON pf.id_pessoa   = p.id_pessoa
WHERE EXTRACT(YEAR  FROM a.data_hora) = 2025
  AND EXTRACT(MONTH FROM a.data_hora) = 6
GROUP BY p.nome
HAVING COUNT(a.id_atendimento) > 5
ORDER BY total_atendimentos DESC;
