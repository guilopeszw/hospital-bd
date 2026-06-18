-- Listar procedimentos realizados em um atendimento (ex: id_atendimento = 1)
SELECT 
    pr.id_atendimento,
    proc.nome AS procedimento,
    pr.quantidade,
    pr.tempo_real_minutos,
    pr.observacao
FROM procedimento_realizado pr
JOIN procedimento proc ON pr.id_procedimento = proc.id_procedimento
WHERE pr.id_atendimento = 1;
