-- ============================================================
-- TABELA: PROCEDIMENTO_REALIZADO
-- Domínio: Pessoa B
-- Dependências: ATENDIMENTO, PROCEDIMENTO
--
-- A coluna "faturado" é a flag usada para impedir a exclusão
-- de procedimentos que já foram faturados (regra de negócio
-- exigida no item 3 do enunciado).
-- ============================================================

CREATE TABLE PROCEDIMENTO_REALIZADO (
    id_atendimento      UUID    NOT NULL,
    id_procedimento     UUID    NOT NULL,
    quantidade          INT     NOT NULL CHECK (quantidade > 0),
    tempo_real_minutos  INT     NOT NULL CHECK (tempo_real_minutos > 0),
    observacao          TEXT,
    faturado            BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (id_atendimento, id_procedimento),

    CONSTRAINT fk_pr_atendimento
        FOREIGN KEY (id_atendimento)  REFERENCES ATENDIMENTO(id_atendimento)   ON DELETE CASCADE,

    CONSTRAINT fk_pr_procedimento
        FOREIGN KEY (id_procedimento) REFERENCES PROCEDIMENTO(id_procedimento) ON DELETE RESTRICT
);
