-- ============================================================
-- TABELA: AUDITORIA_ATENDIMENTO
-- Dependências: nenhuma FK — guarda o id_atendimento cru, sem
-- FOREIGN KEY para ATENDIMENTO. Log de auditoria não pode sumir
-- se o atendimento original for apagado; existir sem FK impede
-- estourar erro numa hipotética exclusão só por causa do log.
-- Populada por trg_audita_atendimento (11_escala.sql em diante).
-- ============================================================

CREATE TABLE AUDITORIA_ATENDIMENTO (
    id_auditoria   UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_atendimento UUID        NOT NULL,
    operacao       VARCHAR(10) NOT NULL CHECK (operacao IN ('INSERT', 'UPDATE', 'DELETE')),
    dados_antigos  JSONB,
    dados_novos    JSONB,
    alterado_em    TIMESTAMP   NOT NULL DEFAULT now()
);
