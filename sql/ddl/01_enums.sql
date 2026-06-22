CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- extensão para gerar UUID

-- criação dos enums de controle global
CREATE TYPE papel_profissional_enum AS ENUM ('residente', 'preceptor');
CREATE TYPE ano_residencia_enum AS ENUM ('R1', 'R2', 'R3');