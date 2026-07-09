-- ============================================================
-- CRUD: Listar todos os atendimentos de um paciente específico
-- ordenados por data decrescente.
--
-- Substitua o UUID abaixo pelo id do paciente desejado.
-- ============================================================

SELECT
    a.id_atendimento,
    a.data_hora,
    a.duracao_minutos,
    pp.nome  AS paciente,
    rp.nome  AS residente,
    prp.nome AS preceptor
FROM ATENDIMENTO a
JOIN PACIENTE     pac ON a.id_paciente  = pac.id_pessoa
JOIN PESSOA       pp  ON pac.id_pessoa  = pp.id_pessoa
JOIN RESIDENTE    res ON a.id_residente = res.id_pessoa
JOIN PROFISSIONAL rpf ON res.id_pessoa  = rpf.id_pessoa
JOIN PESSOA       rp  ON rpf.id_pessoa  = rp.id_pessoa
JOIN PRECEPTOR    pre ON a.id_preceptor = pre.id_pessoa
JOIN PROFISSIONAL ppf ON pre.id_pessoa  = ppf.id_pessoa
JOIN PESSOA       prp ON ppf.id_pessoa  = prp.id_pessoa
WHERE a.id_paciente = 'a1111111-1111-1111-1111-111111111111'  -- substituir pelo UUID real
ORDER BY a.data_hora DESC;
