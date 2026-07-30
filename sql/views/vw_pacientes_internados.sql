-- ============================================================
-- vw_pacientes_internados  (Etapa 2 — item 3)
--
-- Pacientes atualmente internados: a internação MAIS RECENTE de
-- cada paciente ainda não tem data_hora_saida (NULL = internado).
-- DISTINCT ON pega a internação mais recente por paciente; o
-- filtro externo mantém só as sem alta.
-- ============================================================

CREATE OR REPLACE VIEW vw_pacientes_internados AS
SELECT sub.id_paciente,
       p.nome            AS paciente,
       u.nome            AS unidade,
       sub.data_hora_entrada,
       sub.motivo
FROM (
    SELECT DISTINCT ON (i.id_paciente)
           i.id_paciente, i.id_unidade, i.data_hora_entrada,
           i.data_hora_saida, i.motivo
    FROM INTERNACAO i
    ORDER BY i.id_paciente, i.data_hora_entrada DESC
) sub
JOIN PESSOA  p ON p.id_pessoa  = sub.id_paciente
JOIN UNIDADE u ON u.id_unidade = sub.id_unidade
WHERE sub.data_hora_saida IS NULL
ORDER BY sub.data_hora_entrada;
