-- ============================================================
-- sp_calcular_tempo_medio_espera  (Etapa 2 — item 1)
--
-- Para cada unidade, tempo médio (minutos) entre a chegada do
-- paciente (ATENDIMENTO.data_hora) e o início do PRIMEIRO
-- procedimento daquele atendimento (MIN(data_hora_inicio)).
--
-- FUNCTION que retorna tabela — dá pra usar como
--   SELECT * FROM sp_calcular_tempo_medio_espera();
-- ============================================================

CREATE OR REPLACE FUNCTION sp_calcular_tempo_medio_espera()
RETURNS TABLE (
    id_unidade           UUID,
    unidade              VARCHAR,
    atendimentos_medidos BIGINT,
    espera_media_minutos NUMERIC
)
LANGUAGE sql
AS $$
    WITH primeiro_proc AS (
        SELECT a.id_atendimento,
               a.id_unidade,
               a.data_hora,
               MIN(pr.data_hora_inicio) AS inicio_primeiro
        FROM ATENDIMENTO a
        JOIN PROCEDIMENTO_REALIZADO pr ON pr.id_atendimento = a.id_atendimento
        GROUP BY a.id_atendimento, a.id_unidade, a.data_hora
    )
    SELECT u.id_unidade,
           u.nome,
           COUNT(*),
           ROUND(AVG(EXTRACT(EPOCH FROM (pp.inicio_primeiro - pp.data_hora)) / 60.0), 2)
    FROM primeiro_proc pp
    JOIN UNIDADE u ON u.id_unidade = pp.id_unidade
    GROUP BY u.id_unidade, u.nome
    ORDER BY u.nome;
$$;
