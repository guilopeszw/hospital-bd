CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- extensão para gerar UUID

-- criação dos enums de controle global
CREATE TYPE papel_profissional_enum AS ENUM ('residente', 'preceptor');
CREATE TYPE ano_residencia_enum AS ENUM ('R1', 'R2', 'R3');

-- enums de negócio (unidade/escala/procedimento)
CREATE TYPE dia_semana_enum AS ENUM ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo');
CREATE TYPE turno_enum AS ENUM ('manha', 'tarde', 'noite');
CREATE TYPE nivel_risco_enum AS ENUM ('BAIXO', 'MEDIO', 'ALTO');