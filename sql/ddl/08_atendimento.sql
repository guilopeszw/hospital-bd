-- ============================================================
-- TABELA: ATENDIMENTO
-- Domínio: Pessoa B
-- Dependências: PACIENTE, RESIDENTE, PRECEPTOR (Pessoa A)
--
-- ATENÇÃO: A Pessoa A usa UUID como PK em todas as tabelas,
-- e a coluna se chama "id_pessoa" tanto em RESIDENTE quanto
-- em PRECEPTOR (não "id_profissional" como estava antes).
-- ============================================================

CREATE TABLE ATENDIMENTO (
    id_atendimento  UUID      PRIMARY KEY DEFAULT uuid_generate_v4(),
    data_hora       TIMESTAMP NOT NULL,
    duracao_minutos INT       NOT NULL CHECK (duracao_minutos > 0),
    id_paciente     UUID      NOT NULL,
    id_residente    UUID      NOT NULL,
    id_preceptor    UUID      NOT NULL,

    CONSTRAINT fk_atend_paciente
        FOREIGN KEY (id_paciente)  REFERENCES PACIENTE(id_pessoa)   ON DELETE RESTRICT,

    CONSTRAINT fk_atend_residente
        FOREIGN KEY (id_residente) REFERENCES RESIDENTE(id_pessoa)  ON DELETE RESTRICT,

    CONSTRAINT fk_atend_preceptor
        FOREIGN KEY (id_preceptor) REFERENCES PRECEPTOR(id_pessoa)  ON DELETE RESTRICT
);
