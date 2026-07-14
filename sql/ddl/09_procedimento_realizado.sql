-- ============================================================
-- TABELA: PROCEDIMENTO_REALIZADO
-- Domínio: Pessoa B
-- Dependências: ATENDIMENTO, PROCEDIMENTO
--
-- Tabela associativa do N:M entre ATENDIMENTO e PROCEDIMENTO,
-- com os atributos próprios da execução (quantidade, tempo real
-- e observações sobre complicações).
--
-- O faturamento NÃO fica aqui: quem registra é a tabela
-- FATURAMENTO (12_faturamento.sql), que referencia esta PK
-- composta. A regra "só remove procedimento sem faturamento
-- associado" é garantida pela FK com ON DELETE RESTRICT lá.
-- ============================================================

CREATE TABLE PROCEDIMENTO_REALIZADO (
    id_atendimento      UUID    NOT NULL,
    id_procedimento     UUID    NOT NULL,
    quantidade          INT     NOT NULL CHECK (quantidade > 0),
    tempo_real_minutos  INT     NOT NULL CHECK (tempo_real_minutos > 0),
    observacao          TEXT,

    PRIMARY KEY (id_atendimento, id_procedimento),

    CONSTRAINT fk_pr_atendimento
        FOREIGN KEY (id_atendimento)  REFERENCES ATENDIMENTO(id_atendimento)   ON DELETE CASCADE,

    CONSTRAINT fk_pr_procedimento
        FOREIGN KEY (id_procedimento) REFERENCES PROCEDIMENTO(id_procedimento) ON DELETE RESTRICT
);
