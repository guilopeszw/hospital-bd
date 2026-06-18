-- Listar todos os atendimentos de um paciente específico (ex: id_paciente = 1)
SELECT 
    a.id_atendimento,
    a.data_hora,
    a.duracao_minutos,
    p.nome AS paciente,
    r.nome AS residente,
    pr.nome AS preceptor
FROM atendimento a
JOIN paciente pa ON a.id_paciente = pa.id_pessoa
JOIN pessoa p ON pa.id_pessoa = p.id_pessoa
JOIN residente res ON a.id_residente = res.id_profissional
JOIN pessoa r ON res.id_profissional = r.id_pessoa
JOIN preceptor pre ON a.id_preceptor = pre.id_profissional
JOIN pessoa pr ON pre.id_profissional = pr.id_pessoa
WHERE a.id_paciente = 1
ORDER BY a.data_hora DESC;
