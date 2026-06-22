CREATE TABLE PACIENTE (
    id_pessoa UUID PRIMARY KEY REFERENCES PESSOA(id_pessoa) ON DELETE CASCADE,
    num_convenio VARCHAR(50),
    alergias TEXT,
    grupo_sanguineo VARCHAR(3),
    CONSTRAINT chk_grupo_sanguineo_valido CHECK (grupo_sanguineo IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'))
);