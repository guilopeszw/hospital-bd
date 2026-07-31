-- ============================================================
-- TABELA: INTERNACAO  (Etapa 2)
-- Dependências: PACIENTE, UNIDADE
--
-- O contexto do projeto cita "internações" no domínio, mas a
-- Etapa 1 não a modelou. É a entidade que sustenta a view
-- vw_pacientes_internados: um paciente está internado quando sua
-- internação mais recente ainda não tem data_hora_saida
-- (NULL = ainda internado).
-- ============================================================

CREATE TABLE INTERNACAO (
    id_internacao     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_paciente       UUID NOT NULL REFERENCES PACIENTE(id_pessoa) ON DELETE RESTRICT,
    id_unidade        UUID NOT NULL REFERENCES UNIDADE(id_unidade) ON DELETE RESTRICT,
    data_hora_entrada TIMESTAMP NOT NULL,
    data_hora_saida   TIMESTAMP,
    motivo            TEXT,

    CONSTRAINT chk_internacao_saida_apos_entrada
        CHECK (data_hora_saida IS NULL OR data_hora_saida >= data_hora_entrada)
);
