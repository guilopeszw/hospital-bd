-- inserindo pessoas
INSERT INTO PESSOA (id_pessoa, nome, cpf, data_nascimento, is_flamengo, telefone) VALUES
('c1111111-1111-1111-1111-111111111111', 'Residente Gerson', '12312312311', '1997-05-20', TRUE, '83977771111'),
('c2222222-2222-2222-2222-222222222222', 'Residente Léo Ortiz', '23423423422', '1996-01-03', TRUE, '83977772222'),
('c3333333-3333-3333-3333-333333333333', 'Residente Ayrton Lucas', '34534534533', '1997-06-19', TRUE, '83977773333'),
('c4444444-4444-4444-4444-444444444444', 'Residente Gonzalo Plata', '45645645644', '2000-11-01', TRUE, '83977774444'),
('c5555555-5555-5555-5555-555555555555', 'Residente Michael Delgado', '56756756755', '1996-03-12', TRUE, '83977775555');

-- inserindo profissionais e vinculando eles à pessoas
INSERT INTO PROFISSIONAL (id_pessoa, crm, data_admissao, especialidade, papel_atual) VALUES
('c1111111-1111-1111-1111-111111111111', 'CRM/PB 6666', '2025-02-01', 'Cardiologia', 'residente'),
('c2222222-2222-2222-2222-222222222222', 'CRM/PB 7777', '2025-02-01', 'Infectologia', 'residente'),
('c3333333-3333-3333-3333-333333333333', 'CRM/PB 8888', '2024-02-01', 'Pediatria', 'residente'),
('c4444444-4444-4444-4444-444444444444', 'CRM/PB 9999', '2023-02-01', 'Ortopedia', 'residente'),
('c5555555-5555-5555-5555-555555555555', 'CRM/PB 0000', '2025-02-01', 'Neurologia', 'residente');

-- vinculando como residentes
INSERT INTO RESIDENTE (id_pessoa, ano_residencia) VALUES
('c1111111-1111-1111-1111-111111111111', 'R1'),
('c2222222-2222-2222-2222-222222222222', 'R1'),
('c3333333-3333-3333-3333-333333333333', 'R2'),
('c4444444-4444-4444-4444-444444444444', 'R3'),
('c5555555-5555-5555-5555-555555555555', 'R1');