-- ============================================================
-- TRIGGER: trg_check_sobreposicao_escala
-- BEFORE INSERT/UPDATE em ESCALA.
--
-- A UNIQUE (id_unidade, dia_semana, turno, id_residente) já
-- barra duplicata EXATA (mesma unidade/dia/turno/residente).
-- O que ela NÃO barra: o mesmo residente escalado em DUAS
-- unidades diferentes no mesmo dia/turno — fisicamente
-- impossível (a pessoa só pode estar num lugar por vez).
-- Esse é o buraco que esse trigger fecha.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_check_sobreposicao_escala()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_conflito INT;
BEGIN
    SELECT COUNT(*) INTO v_conflito
    FROM ESCALA
    WHERE id_residente = NEW.id_residente
      AND dia_semana    = NEW.dia_semana
      AND turno         = NEW.turno
      AND id_unidade   <> NEW.id_unidade
      AND id_escala    <> NEW.id_escala;

    IF v_conflito > 0 THEN
        RAISE EXCEPTION
            'Sobreposição de escala: residente % já está escalado em outra unidade em %/%.',
            NEW.id_residente, NEW.dia_semana, NEW.turno;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_check_sobreposicao_escala ON ESCALA;

CREATE TRIGGER trg_check_sobreposicao_escala
    BEFORE INSERT OR UPDATE ON ESCALA
    FOR EACH ROW
    EXECUTE FUNCTION fn_check_sobreposicao_escala();

-- ----------------------------------------------------------------
-- Teste manual:
-- INSERT INTO ESCALA (id_unidade, dia_semana, turno, id_residente, id_preceptor)
-- VALUES ('<unidade_A>', 'segunda', 'manha', '<residente_X>', '<preceptor>');
--
-- INSERT INTO ESCALA (id_unidade, dia_semana, turno, id_residente, id_preceptor)
-- VALUES ('<unidade_B>', 'segunda', 'manha', '<residente_X>', '<preceptor>');
-- -> deve disparar a exceção (mesmo residente, mesmo dia/turno, unidade diferente)
-- ----------------------------------------------------------------
