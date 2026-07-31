-- ----------------------------------------
-- INTERNACOES (Etapa 2)
-- Duas ativas (data_hora_saida NULL = internado) e uma com alta,
-- para vw_pacientes_internados retornar exatamente 2 pacientes.
-- ----------------------------------------
INSERT INTO INTERNACAO (id_paciente, id_unidade, data_hora_entrada, data_hora_saida, motivo) VALUES
('a1111111-1111-1111-1111-111111111111', 'f2222222-2222-2222-2222-222222222222', '2025-06-10 12:00:00', NULL,                  'Observação pós-sutura'),
('a3333333-3333-3333-3333-333333333333', 'f1111111-1111-1111-1111-111111111111', '2025-06-12 15:00:00', NULL,                  'Pneumonia'),
('a2222222-2222-2222-2222-222222222222', 'f3333333-3333-3333-3333-333333333333', '2025-06-10 09:30:00', '2025-06-10 18:00:00', 'Alta no mesmo dia');
