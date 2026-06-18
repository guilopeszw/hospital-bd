-- Inserir procedimentos
INSERT INTO procedimento (codigo, nome, tempo_medio_minutos) VALUES
('SUT-001', 'Sutura simples', 20),
('COL-101', 'Coleta de sangue', 10),
('MED-205', 'Aplicação de medicação intravenosa', 15),
('RAIO-X', 'Radiografia de tórax', 25),
('ELETRO', 'Eletrocardiograma', 12),
('CURATIVO', 'Troca de curativo', 18),
('PUNCAO', 'Punção venosa', 8),
('NEBULIZACAO', 'Nebulização', 22),
('SUT-002', 'Sutura complexa', 40),
('DRENAGEM', 'Drenagem de abscesso', 35);

-- Inserir atendimentos (exemplo com IDs que devem existir)
-- Supondo que: paciente 1, residente 101, preceptor 201 já foram inseridos
-- (isso será responsabilidade da Pessoa A, mas vamos assumir que já estão no banco)

INSERT INTO atendimento (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor) VALUES
('2025-06-10 08:00:00', 45, 1, 101, 201),
('2025-06-10 09:00:00', 30, 2, 102, 201),
('2025-06-10 10:30:00', 60, 3, 103, 202),
('2025-06-11 07:45:00', 40, 1, 104, 203),
('2025-06-11 11:00:00', 25, 4, 101, 202),
('2025-06-11 13:30:00', 50, 5, 105, 201),
('2025-06-12 09:15:00', 35, 2, 102, 203),
('2025-06-12 14:00:00', 70, 3, 103, 201),
('2025-06-13 08:30:00', 40, 4, 104, 202),
('2025-06-13 16:00:00', 55, 5, 105, 203);

-- Inserir procedimentos realizados
INSERT INTO procedimento_realizado (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, observacao, faturado) VALUES
(1, 1, 1, 18, 'Paciente estável após sutura', FALSE),
(1, 2, 1, 12, 'Coleta realizada com sucesso', FALSE),
(2, 2, 1, 10, 'Coleta em veia periférica', FALSE),
(2, 3, 1, 16, 'Medicação aplicada sem intercorrências', FALSE),
(3, 4, 1, 26, 'Radiografia com leve alteração', FALSE),
(4, 1, 1, 22, 'Sutura com pontos separados', FALSE),
(5, 5, 1, 14, 'Eletro normal', FALSE),
(6, 6, 1, 20, 'Curativo com gaze estéril', FALSE),
(7, 7, 1, 9, 'Punção bem-sucedida', FALSE),
(8, 8, 1, 24, 'Nebulização com salbutamol', FALSE);


SELECT * FROM procedimento;

-- Verificar se os atendimentos foram gerados
SELECT * FROM atendimento;

-- Verificar se os procedimentos vinculados estão corretos
SELECT * FROM procedimento;