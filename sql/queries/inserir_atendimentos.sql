-- ============================================================
-- CRUD: Inserir atendimento (SQL puro)
-- Só insere se paciente, residente e preceptor existirem.
-- ============================================================

INSERT INTO ATENDIMENTO (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor)
SELECT '2025-06-14 10:00:00'::timestamp, 30,
       'a1111111-1111-1111-1111-111111111111',
       'c1111111-1111-1111-1111-111111111111',
       'b1111111-1111-1111-1111-111111111111'
WHERE EXISTS (SELECT 1 FROM PACIENTE  WHERE id_pessoa = 'a1111111-1111-1111-1111-111111111111')
  AND EXISTS (SELECT 1 FROM RESIDENTE WHERE id_pessoa = 'c1111111-1111-1111-1111-111111111111')
  AND EXISTS (SELECT 1 FROM PRECEPTOR WHERE id_pessoa = 'b1111111-1111-1111-1111-111111111111')
RETURNING id_atendimento;
