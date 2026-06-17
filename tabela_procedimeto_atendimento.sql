-- Active: 1781647783645@@localhost@5433@hospital_db
-- Criação da tabela PROCEDIMENTO
CREATE TABLE PROCEDIMENTO (
    id_procedimento SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    tempo_medio_minutos INT NOT NULL CHECK (tempo_medio_minutos > 0)
);

-- Criação da tabela ATENDIMENTO
CREATE TABLE ATENDIMENTO (
    id_atendimento SERIAL PRIMARY KEY,
    data_hora TIMESTAMP NOT NULL,
    duracao_minutos INT NOT NULL CHECK (duracao_minutos > 0),
    id_paciente INT NOT NULL,
    id_residente INT NOT NULL,
    id_preceptor INT NOT NULL,
    
    -- Chaves estrangeiras apontando para as tabelas do Aluno A
    CONSTRAINT fk_paciente FOREIGN KEY (id_paciente) REFERENCES PACIENTE (id_pessoa) ON DELETE RESTRICT,
    CONSTRAINT fk_residente FOREIGN KEY (id_residente) REFERENCES RESIDENTE (id_profissional) ON DELETE RESTRICT,
    CONSTRAINT fk_preceptor FOREIGN KEY (id_preceptor) REFERENCES PRECEPTOR (id_profissional) ON DELETE RESTRICT
);

-- Criação da tabela PROCEDIMENTO_REALIZADO
CREATE TABLE PROCEDIMENTO_REALIZADO (
    id_atendimento INT NOT NULL,
    id_procedimento INT NOT NULL,
    quantidade INT NOT NULL CHECK (quantidade > 0),
    tempo_real_minutos INT NOT NULL CHECK (tempo_real_minutos > 0),
    observacao TEXT,
    faturado BOOLEAN DEFAULT FALSE, -- Flag solicitada para regra de exclusão
    
    -- Chave primária composta
    PRIMARY KEY (id_atendimento, id_procedimento),
    
    CONSTRAINT fk_atendimento FOREIGN KEY (id_atendimento) REFERENCES ATENDIMENTO (id_atendimento) ON DELETE CASCADE,
    CONSTRAINT fk_procedimento FOREIGN KEY (id_procedimento) REFERENCES PROCEDIMENTO (id_procedimento) ON DELETE RESTRICT
);

SELECT * FROM PROCEDIMENTO;