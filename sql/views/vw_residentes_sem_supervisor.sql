-- ============================================================
-- vw_residentes_sem_supervisor  (Etapa 2 — item 3)
--
-- Residentes escalados em algum plantão cujo preceptor NÃO tem
-- titulação de doutor. O enunciado trata "supervisão adequada"
-- como supervisão por doutor; quem só tem preceptor não-doutor
-- é considerado sem supervisor qualificado.
--
-- Normaliza a titulação (lower/trim) para casar 'Doutor',
-- 'doutora', 'DOUTOR' etc. Uma escala conta como "sem supervisor"
-- quando o preceptor daquele plantão não é doutor.
-- ============================================================

CREATE OR REPLACE VIEW vw_residentes_sem_supervisor AS
SELECT DISTINCT
       r.id_pessoa       AS id_residente,
       pr_pessoa.nome    AS residente,
       r.ano_residencia,
       u.nome            AS unidade,
       e.dia_semana,
       e.turno,
       pp.nome           AS preceptor,
       prc.titulacao
FROM ESCALA e
JOIN RESIDENTE  r   ON r.id_pessoa   = e.id_residente
JOIN PESSOA pr_pessoa ON pr_pessoa.id_pessoa = r.id_pessoa
JOIN PRECEPTOR  prc ON prc.id_pessoa = e.id_preceptor
JOIN PESSOA     pp  ON pp.id_pessoa  = prc.id_pessoa
JOIN UNIDADE    u   ON u.id_unidade  = e.id_unidade
WHERE lower(trim(prc.titulacao)) NOT IN ('doutor', 'doutora')
ORDER BY residente, e.dia_semana, e.turno;
