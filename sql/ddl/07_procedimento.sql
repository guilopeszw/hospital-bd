-- ============================================================
-- TABELA: PROCEDIMENTO
-- Domínio: Pessoa B
-- Dependências: nenhuma (tabela independente)
-- ============================================================

CREATE TABLE PROCEDIMENTO (
    id_procedimento UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo          VARCHAR(20)  NOT NULL UNIQUE,
    nome            VARCHAR(100) NOT NULL,
    tempo_medio_minutos INT      NOT NULL CHECK (tempo_medio_minutos > 0),
    nivel_risco     nivel_risco_enum NOT NULL DEFAULT 'BAIXO'
);
