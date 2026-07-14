-- ============================================================
-- TABELA: RESIDENTE
-- Dependências: PROFISSIONAL
--
-- Mesma mecânica de exclusividade de papel descrita em
-- 05_preceptor.sql, travando "papel" em 'residente'.
-- ============================================================

CREATE TABLE RESIDENTE (
    id_pessoa      UUID PRIMARY KEY,
    papel          papel_profissional_enum NOT NULL DEFAULT 'residente',
    ano_residencia ano_residencia_enum NOT NULL,

    CONSTRAINT chk_residente_papel CHECK (papel = 'residente'),

    CONSTRAINT fk_residente_profissional
        FOREIGN KEY (id_pessoa, papel)
        REFERENCES PROFISSIONAL(id_pessoa, papel_atual)
        ON DELETE CASCADE ON UPDATE CASCADE
);
