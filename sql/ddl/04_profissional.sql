-- ============================================================
-- TABELA: PROFISSIONAL
-- Dependências: PESSOA
--
-- uq_prof_papel serve de alvo para a FK composta de PRECEPTOR
-- e RESIDENTE. É o que garante, sem trigger, que um profissional
-- exerce um único papel por vez (ver 05_preceptor e 06_residente).
-- ============================================================

CREATE TABLE PROFISSIONAL (
    id_pessoa UUID PRIMARY KEY REFERENCES PESSOA(id_pessoa) ON DELETE CASCADE,
    crm VARCHAR(20) NOT NULL UNIQUE,
    data_admissao DATE NOT NULL,
    especialidade VARCHAR(100) NOT NULL,
    papel_atual papel_profissional_enum NOT NULL,

    CONSTRAINT uq_prof_papel UNIQUE (id_pessoa, papel_atual)
);
