-- ============================================================
-- CRUD: Calcular tempo médio de duração dos atendimentos
-- agrupado por residente, do maior para o menor.
--
-- LEFT JOIN em ATENDIMENTO: residente sem atendimento aparece
-- com total 0 e média NULL (em vez de sumir do relatório).
-- NULLS LAST mantém esses residentes no fim da lista.
-- ============================================================

SELECT
    res.id_pessoa                    AS id_residente,
    p.nome                           AS residente,
    prof.especialidade,
    res.ano_residencia,
    COUNT(a.id_atendimento)          AS total_atendimentos,
    ROUND(AVG(a.duracao_minutos), 2) AS tempo_medio_minutos
FROM RESIDENTE res
JOIN PESSOA       p    ON p.id_pessoa    = res.id_pessoa
JOIN PROFISSIONAL prof ON prof.id_pessoa = res.id_pessoa
LEFT JOIN ATENDIMENTO a ON a.id_residente = res.id_pessoa
GROUP BY res.id_pessoa, p.nome, prof.especialidade, res.ano_residencia
ORDER BY tempo_medio_minutos DESC NULLS LAST, p.nome;
