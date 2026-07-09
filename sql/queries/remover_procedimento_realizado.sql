
DELETE FROM PROCEDIMENTO_REALIZADO
WHERE id_atendimento  = 'e1111111-1111-1111-1111-111111111111'  -- :id_atendimento
  AND id_procedimento = 'd1111111-1111-1111-1111-111111111111'  -- :id_procedimento
  AND faturado = FALSE
RETURNING id_atendimento, id_procedimento;
