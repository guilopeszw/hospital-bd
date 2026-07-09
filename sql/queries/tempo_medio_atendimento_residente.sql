-- ============================================================
-- CRUD: Calcular tempo médio de duração dos atendimentos
-- agrupado por residente, do maior para o menor.
-- ============================================================


SELECT
    res.id_pessoa                          AS id_residente,
    p.nome                                  AS residente,
    prof.especialidade,
    res.ano_residencia,
    COUNT(a.id_atendimento)                 AS total_atendimentos,
    ROUND(AVG(a.duracao_minutos), 2)        AS tempo_medio_minutos
FROM RESIDENTE res
JOIN PESSOA       p    ON res.id_pessoa = p.id_pessoa
JOIN PROFISSIONAL prof ON res.id_pessoa = prof.id_pessoa
JOIN ATENDIMENTO  a    ON a.id_residente = res.id_pessoa
GROUP BY res.id_pessoa, p.nome, prof.especialidade, res.ano_residencia
ORDER BY tempo_medio_minutos DESC;
 
