CREATE TABLE PROFISSIONAL (
    id_pessoa UUID PRIMARY KEY REFERENCES PESSOA(id_pessoa) ON DELETE CASCADE,
    crm VARCHAR(20) NOT NULL UNIQUE,
    data_admissao DATE NOT NULL,
    especialidade VARCHAR(100) NOT NULL,
    papel_atual papel_profissional_enum NOT NULL
);