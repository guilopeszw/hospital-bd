-- Active: 1781647783645@@localhost@5433@hospital_db
-- Calcular tempo médio de duração dos atendimentos por residente
SELECT 
    r.nome AS residente,
    AVG(a.duracao_minutos) AS tempo_medio_minutos
FROM atendimento a
JOIN residente res ON a.id_residente = res.id_profissional
JOIN pessoa r ON res.id_profissional = r.id_pessoa
GROUP BY r.nome
ORDER BY tempo_medio_minutos DESC;
