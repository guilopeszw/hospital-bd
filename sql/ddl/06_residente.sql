CREATE TABLE RESIDENTE (
    id_pessoa UUID PRIMARY KEY REFERENCES PROFISSIONAL(id_pessoa) ON DELETE CASCADE,
    ano_residencia ano_residencia_enum NOT NULL
);