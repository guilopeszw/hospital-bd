-- ----------------------------------------
-- FATURAMENTO
-- Três procedimentos realizados já faturados. Servem para
-- demonstrar a regra "só remove procedimento realizado que NÃO
-- tenha faturamento associado" (a FK ON DELETE RESTRICT barra
-- a exclusão destes três).
-- ----------------------------------------
INSERT INTO FATURAMENTO (id_atendimento, id_procedimento, valor, data_emissao) VALUES
('e2222222-2222-2222-2222-222222222222', 'd2222222-2222-2222-2222-222222222222', 120.00, '2025-06-15'),
('e3333333-3333-3333-3333-333333333333', 'd4444444-4444-4444-4444-444444444444', 250.00, '2025-06-16'),
('eccccccc-cccc-cccc-cccc-cccccccccccc', 'd9999999-9999-9999-9999-999999999999', 800.00, '2025-06-22');
