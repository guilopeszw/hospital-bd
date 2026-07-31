-- ============================================================
-- sp_registrar_atendimento_completo  (Etapa 2 — item 1)
--
-- Insere um atendimento + sua lista de procedimentos numa única
-- transação. A lista chega como JSONB:
--   [{"id_procedimento":"...", "quantidade":1,
--     "tempo_real_minutos":15, "data_hora_inicio":"2025-07-01 10:10:00",
--     "observacao":"..."}, ...]
-- Se qualquer item falhar (FK inválida, CHECK, etc.), a função
-- inteira reverte — nada é gravado. Retorna o id do atendimento.
--
-- É FUNCTION (não PROCEDURE) para devolver o UUID via RETURNS; o
-- corpo roda na transação do chamador, então um RAISE em qualquer
-- ponto aborta tudo.
-- ============================================================

CREATE OR REPLACE FUNCTION sp_registrar_atendimento_completo(
    p_data_hora       TIMESTAMP,
    p_duracao_minutos INT,
    p_id_paciente     UUID,
    p_id_residente    UUID,
    p_id_preceptor    UUID,
    p_id_unidade      UUID,
    p_procedimentos   JSONB
) RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_atendimento UUID;
    v_item           JSONB;
BEGIN
    INSERT INTO ATENDIMENTO (data_hora, duracao_minutos, id_paciente,
                             id_residente, id_preceptor, id_unidade)
    VALUES (p_data_hora, p_duracao_minutos, p_id_paciente,
            p_id_residente, p_id_preceptor, p_id_unidade)
    RETURNING id_atendimento INTO v_id_atendimento;

    FOR v_item IN
        SELECT * FROM jsonb_array_elements(COALESCE(p_procedimentos, '[]'::jsonb))
    LOOP
        INSERT INTO PROCEDIMENTO_REALIZADO (
            id_atendimento, id_procedimento, quantidade,
            tempo_real_minutos, data_hora_inicio, observacao)
        VALUES (
            v_id_atendimento,
            (v_item->>'id_procedimento')::UUID,
            COALESCE((v_item->>'quantidade')::INT, 1),
            (v_item->>'tempo_real_minutos')::INT,
            COALESCE((v_item->>'data_hora_inicio')::TIMESTAMP, p_data_hora),
            v_item->>'observacao');
    END LOOP;

    RETURN v_id_atendimento;
END;
$$;
