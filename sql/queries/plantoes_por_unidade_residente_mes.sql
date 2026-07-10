-- ============================================================
-- CONSULTA ANALÍTICA 3: Para cada unidade, quantidade de
-- plantões escalados por residente no mês corrente.
--
-- ESCALA guarda um plantão recorrente semanal (dia_semana),
-- não uma data concreta. Para responder "no mês corrente",
-- geramos todos os dias do mês com generate_series e contamos
-- quantas vezes cada dia_semana ocorre, multiplicando pelas
-- escalas cadastradas para aquele dia/turno.
-- ============================================================

WITH dias_mes AS (
    SELECT dia::date AS dia
    FROM generate_series(
        date_trunc('month', CURRENT_DATE),
        date_trunc('month', CURRENT_DATE) + interval '1 month' - interval '1 day',
        interval '1 day'
    ) AS dia
),
mapa_dia AS (
    SELECT dia, (CASE EXTRACT(DOW FROM dia)
        WHEN 0 THEN 'domingo' WHEN 1 THEN 'segunda' WHEN 2 THEN 'terca'
        WHEN 3 THEN 'quarta'  WHEN 4 THEN 'quinta'  WHEN 5 THEN 'sexta'
        WHEN 6 THEN 'sabado' END)::dia_semana_enum AS dia_semana
    FROM dias_mes
)
SELECT
    u.nome                  AS unidade,
    p.nome                  AS residente,
    COUNT(*)                AS total_plantoes_no_mes
FROM ESCALA e
JOIN mapa_dia m       ON m.dia_semana = e.dia_semana
JOIN UNIDADE u        ON u.id_unidade = e.id_unidade
JOIN RESIDENTE res    ON res.id_pessoa = e.id_residente
JOIN PROFISSIONAL pf  ON pf.id_pessoa = res.id_pessoa
JOIN PESSOA p         ON p.id_pessoa = pf.id_pessoa
GROUP BY u.nome, p.nome
ORDER BY u.nome, total_plantoes_no_mes DESC;
