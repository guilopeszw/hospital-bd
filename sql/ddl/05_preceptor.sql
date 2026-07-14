-- ============================================================
-- TABELA: PRECEPTOR
-- Dependências: PROFISSIONAL
--
-- EXCLUSIVIDADE DE PAPEL (enunciado: "num dado momento, o
-- profissional exerce apenas um papel no sistema"):
-- a coluna "papel" é travada em 'preceptor' pelo CHECK e a FK
-- composta (id_pessoa, papel) -> PROFISSIONAL(id_pessoa, papel_atual)
-- exige que o profissional esteja com papel_atual = 'preceptor'.
-- Como RESIDENTE faz o mesmo com 'residente', é impossível a
-- mesma pessoa ter linha nas duas tabelas ao mesmo tempo — sem
-- precisar de trigger.
--
-- ON UPDATE CASCADE: se papel_atual virar 'residente', o cascade
-- tenta escrever 'residente' aqui e o CHECK barra. Trocar de papel
-- exige remover primeiro a linha do papel antigo.
-- ============================================================

CREATE TABLE PRECEPTOR (
    id_pessoa UUID PRIMARY KEY,
    papel     papel_profissional_enum NOT NULL DEFAULT 'preceptor',
    titulacao VARCHAR(50) NOT NULL,

    CONSTRAINT chk_preceptor_papel CHECK (papel = 'preceptor'),

    CONSTRAINT fk_preceptor_profissional
        FOREIGN KEY (id_pessoa, papel)
        REFERENCES PROFISSIONAL(id_pessoa, papel_atual)
        ON DELETE CASCADE ON UPDATE CASCADE
);
