-- inserindo pessoas
INSERT INTO PESSOA (id_pessoa, nome, cpf, data_nascimento, is_flamengo, telefone) VALUES
('b1111111-1111-1111-1111-111111111111', 'Dr. Jorge Jesus', '66677788899', '1954-07-24', TRUE, '83988881111'),
('b2222222-2222-2222-2222-222222222222', 'Dra. Yuska Maritan', '77788899900', '1985-05-12', TRUE, '83988882222'),
('b3333333-3333-3333-3333-333333333333', 'Dr. Dorival Junior', '88899900011', '1962-04-25', FALSE, '83988883333'),
('b4444444-4444-4444-4444-444444444444', 'Dr. Filipe Luis', '99900011122', '1985-08-09', TRUE, '83988884444'),
('b5555555-5555-5555-5555-555555555555', 'Dra. Tite Silva', '00011122233', '1961-05-25', FALSE, '83988885555');

-- inserindo profissionais e vinculando eles à pessoas
INSERT INTO PROFISSIONAL (id_pessoa, crm, data_admissao, especialidade, papel_atual) VALUES
('b1111111-1111-1111-1111-111111111111', 'CRM/PB 1111', '2019-06-01', 'Cardiologia', 'preceptor'),
('b2222222-2222-2222-2222-222222222222', 'CRM/PB 2222', '2015-02-10', 'Infectologia', 'preceptor'),
('b3333333-3333-3333-3333-333333333333', 'CRM/PB 3333', '2022-03-15', 'Pediatria', 'preceptor'),
('b4444444-4444-4444-4444-444444444444', 'CRM/PB 4444', '2024-10-01', 'Ortopedia', 'preceptor'),
('b5555555-5555-5555-5555-555555555555', 'CRM/PB 5555', '2021-01-20', 'Neurologia', 'preceptor');

-- vinculando como preceptores
INSERT INTO PRECEPTOR (id_pessoa, titulacao) VALUES
('b1111111-1111-1111-1111-111111111111', 'Doutor'),
('b2222222-2222-2222-2222-222222222222', 'Doutor'),
('b3333333-3333-3333-3333-333333333333', 'Mestre'),
('b4444444-4444-4444-4444-444444444444', 'Especialista'),
('b5555555-5555-5555-5555-555555555555', 'Mestre');