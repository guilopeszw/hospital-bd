-- ============================================================
-- vw_estatisticas_atendimentos_mensal  (Etapa 2 — item 3)
--
-- Agregação por mês e por unidade:
--   - total de atendimentos
--   - duração média dos atendimentos
--   - procedimento mais comum
--
-- Duas agregações separadas para não enviesar a média: a de
-- atendimentos (total + duração) roda só sobre ATENDIMENTO; a do
-- procedimento mais comum roda sobre PROCEDIMENTO_REALIZADO. Se as
-- juntasse num JOIN só, a duração de um atendimento com N
-- procedimentos entraria N vezes na média.
-- ============================================================

CREATE OR REPLACE VIEW vw_estatisticas_atendimentos_mensal AS
WITH estat AS (
    SELECT date_trunc('month', a.data_hora)::date AS mes,
           a.id_unidade,
           COUNT(*)                          AS total_atendimentos,
           ROUND(AVG(a.duracao_minutos), 2)  AS duracao_media_minutos
    FROM ATENDIMENTO a
    GROUP BY date_trunc('month', a.data_hora), a.id_unidade
),
proc_comum AS (
    SELECT date_trunc('month', a.data_hora)::date AS mes,
           a.id_unidade,
           mode() WITHIN GROUP (ORDER BY p.nome) AS procedimento_mais_comum
    FROM ATENDIMENTO a
    JOIN PROCEDIMENTO_REALIZADO pr ON pr.id_atendimento = a.id_atendimento
    JOIN PROCEDIMENTO p            ON p.id_procedimento = pr.id_procedimento
    GROUP BY date_trunc('month', a.data_hora), a.id_unidade
)
SELECT e.mes,
       u.nome AS unidade,
       e.total_atendimentos,
       e.duracao_media_minutos,
       pc.procedimento_mais_comum
FROM estat e
JOIN UNIDADE u ON u.id_unidade = e.id_unidade
LEFT JOIN proc_comum pc ON pc.mes = e.mes AND pc.id_unidade = e.id_unidade
ORDER BY e.mes, u.nome;
