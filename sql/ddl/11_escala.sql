-- ============================================================
-- TABELA: ESCALA
-- Dependências: UNIDADE, RESIDENTE, PRECEPTOR
--
-- Um residente só pode ter um preceptor supervisor por
-- unidade/dia/turno (garantido pela UNIQUE abaixo, que não
-- inclui id_preceptor). O mesmo preceptor pode supervisionar
-- vários residentes no mesmo plantão (permitido, pois
-- id_preceptor não faz parte da chave única).
-- ============================================================

CREATE TABLE ESCALA (
    id_escala    UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_unidade   UUID            NOT NULL,
    dia_semana   dia_semana_enum NOT NULL,
    turno        turno_enum      NOT NULL,
    id_residente UUID            NOT NULL,
    id_preceptor UUID            NOT NULL,

    CONSTRAINT fk_escala_unidade
        FOREIGN KEY (id_unidade)   REFERENCES UNIDADE(id_unidade)   ON DELETE RESTRICT,

    CONSTRAINT fk_escala_residente
        FOREIGN KEY (id_residente) REFERENCES RESIDENTE(id_pessoa)  ON DELETE RESTRICT,

    CONSTRAINT fk_escala_preceptor
        FOREIGN KEY (id_preceptor) REFERENCES PRECEPTOR(id_pessoa)  ON DELETE RESTRICT,

    CONSTRAINT uq_escala_unica UNIQUE (id_unidade, dia_semana, turno, id_residente)
);
