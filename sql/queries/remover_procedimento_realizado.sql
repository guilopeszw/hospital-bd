-- ============================================================
-- CRUD: Remover um procedimento realizado, apenas se NÃO houver
-- faturamento associado.
--
-- Dupla proteção:
--   1) o NOT EXISTS abaixo faz o DELETE simplesmente não casar
--      nenhuma linha (rowcount = 0) quando existe faturamento;
--   2) mesmo sem o NOT EXISTS, a FK de FATURAMENTO com
--      ON DELETE RESTRICT abortaria a transação.
-- ============================================================

DELETE FROM PROCEDIMENTO_REALIZADO pr
WHERE pr.id_atendimento  = 'e1111111-1111-1111-1111-111111111111'  -- :id_atendimento
  AND pr.id_procedimento = 'd1111111-1111-1111-1111-111111111111'  -- :id_procedimento
  AND NOT EXISTS (
      SELECT 1
      FROM FATURAMENTO f
      WHERE f.id_atendimento  = pr.id_atendimento
        AND f.id_procedimento = pr.id_procedimento
  )
RETURNING pr.id_atendimento, pr.id_procedimento;
