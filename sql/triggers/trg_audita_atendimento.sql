-- ============================================================
-- TRIGGER: trg_audita_atendimento
-- AFTER INSERT/UPDATE/DELETE em ATENDIMENTO -> grava uma linha
-- em AUDITORIA_ATENDIMENTO com o estado antes/depois em JSONB.
-- Depende de sql/ddl/13_auditoria_atendimento.sql já criado.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_audita_atendimento()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO AUDITORIA_ATENDIMENTO (id_atendimento, operacao, dados_antigos, dados_novos)
        VALUES (NEW.id_atendimento, 'INSERT', NULL, to_jsonb(NEW));
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO AUDITORIA_ATENDIMENTO (id_atendimento, operacao, dados_antigos, dados_novos)
        VALUES (NEW.id_atendimento, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO AUDITORIA_ATENDIMENTO (id_atendimento, operacao, dados_antigos, dados_novos)
        VALUES (OLD.id_atendimento, 'DELETE', to_jsonb(OLD), NULL);
        RETURN OLD;
    END IF;
END;
$$;

DROP TRIGGER IF EXISTS trg_audita_atendimento ON ATENDIMENTO;

CREATE TRIGGER trg_audita_atendimento
    AFTER INSERT OR UPDATE OR DELETE ON ATENDIMENTO
    FOR EACH ROW
    EXECUTE FUNCTION fn_audita_atendimento();

-- ----------------------------------------------------------------
-- Teste manual:
-- UPDATE ATENDIMENTO SET duracao_minutos = duracao_minutos + 5
-- WHERE id_atendimento = '<algum id>';
--
-- SELECT * FROM AUDITORIA_ATENDIMENTO ORDER BY alterado_em DESC LIMIT 1;
-- -> deve mostrar operacao='UPDATE', dados_antigos com duracao antiga,
--    dados_novos com duracao nova.
-- ----------------------------------------------------------------
