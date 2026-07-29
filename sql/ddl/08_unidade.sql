-- ============================================================
-- TABELA: UNIDADE
-- Dependências: nenhuma (tabela independente)
-- ============================================================

CREATE TABLE UNIDADE (
    id_unidade        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome              VARCHAR(100) NOT NULL,
    tipo              VARCHAR(30)  NOT NULL,
    capacidade_leitos INT          NOT NULL CHECK (capacidade_leitos > 0),

    CONSTRAINT chk_unidade_tipo_valido CHECK (
        tipo IN ('Enfermaria', 'UTI', 'Pronto-Socorro', 'Ambulatorio')
    )
);
