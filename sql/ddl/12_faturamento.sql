-- ============================================================
-- TABELA: FATURAMENTO
-- Dependências: PROCEDIMENTO_REALIZADO
--
-- Um procedimento realizado pode ter, no máximo, um faturamento
-- (UNIQUE na FK composta). A FK usa ON DELETE RESTRICT: o banco
-- recusa apagar um PROCEDIMENTO_REALIZADO que já tenha
-- faturamento associado — é a regra do item 3 do enunciado
-- garantida no nível do schema, não só na aplicação.
-- ============================================================

CREATE TABLE FATURAMENTO (
    id_faturamento  UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_atendimento  UUID          NOT NULL,
    id_procedimento UUID          NOT NULL,
    valor           NUMERIC(10,2) NOT NULL CHECK (valor > 0),
    data_emissao    DATE          NOT NULL DEFAULT CURRENT_DATE,

    CONSTRAINT fk_fat_procedimento_realizado
        FOREIGN KEY (id_atendimento, id_procedimento)
        REFERENCES PROCEDIMENTO_REALIZADO(id_atendimento, id_procedimento)
        ON DELETE RESTRICT,

    CONSTRAINT uq_fat_procedimento_realizado UNIQUE (id_atendimento, id_procedimento)
);
