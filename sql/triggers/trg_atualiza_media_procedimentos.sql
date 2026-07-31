-- ============================================================
-- TRIGGER: trg_atualiza_media_procedimentos
-- AFTER INSERT/UPDATE/DELETE em PROCEDIMENTO_REALIZADO -> recalcula
-- PROCEDIMENTO.media_tempo_procedimento = AVG(tempo_real_minutos)
-- de todas as execuções daquele id_procedimento.
-- Depende da coluna media_tempo_procedimento (sql/ddl/07_procedimento.sql).
--
-- UPDATE pode trocar o id_procedimento da linha (raro, mas o
-- schema permite) — por isso recalcula tanto o procedimento novo
-- (NEW) quanto o antigo (OLD) quando eles são diferentes.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_atualiza_media_procedimentos()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
    DECLARE
        v_id_procedimento UUID;
BEGIN
    FOR v_id_procedimento IN
        SELECT DISTINCT id_procedimento
        FROM (
            SELECT OLD.id_procedimento AS id_procedimento WHERE TG_OP IN ('UPDATE', 'DELETE')
            UNION
            SELECT NEW.id_procedimento WHERE TG_OP IN ('UPDATE', 'INSERT')
        ) afetados
        WHERE id_procedimento IS NOT NULL
    LOOP
        UPDATE PROCEDIMENTO
        SET media_tempo_procedimento = (
            SELECT AVG(tempo_real_minutos)
            FROM PROCEDIMENTO_REALIZADO
            WHERE id_procedimento = v_id_procedimento
        )
        WHERE id_procedimento = v_id_procedimento;
    END LOOP;

    RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS trg_atualiza_media_procedimentos ON PROCEDIMENTO_REALIZADO;

CREATE TRIGGER trg_atualiza_media_procedimentos
    AFTER INSERT OR UPDATE OR DELETE ON PROCEDIMENTO_REALIZADO
    FOR EACH ROW
    EXECUTE FUNCTION fn_atualiza_media_procedimentos();

-- ----------------------------------------------------------------
-- Teste manual:
-- SELECT media_tempo_procedimento FROM PROCEDIMENTO WHERE id_procedimento = '<id>';
-- INSERT INTO PROCEDIMENTO_REALIZADO (...) VALUES (..., '<id>', ...);
-- SELECT media_tempo_procedimento FROM PROCEDIMENTO WHERE id_procedimento = '<id>';
-- -> deve ter mudado, batendo com a nova média manual.
-- ----------------------------------------------------------------
