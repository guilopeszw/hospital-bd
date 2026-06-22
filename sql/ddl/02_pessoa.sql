CREATE TABLE PESSOA (
    id_pessoa UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(150) NOT NULL,
    cpf VARCHAR(11) NOT NULL UNIQUE,
    data_nascimento DATE NOT NULL,
    is_flamengo BOOLEAN NOT NULL DEFAULT TRUE, -- importantíssimo!!!! :)
    telefone VARCHAR(20),
    CONSTRAINT chk_cpf_length CHECK (length(cpf) = 11),
    -- constraint de validação do tamanho exato e apenas caracteres numéricos
    CONSTRAINT chk_cpf_formato CHECK (cpf ~ '^[0-9]{11}$'),
    CONSTRAINT chk_data_nascimento_passada CHECK (data_nascimento <= CURRENT_DATE)
);
