-- ============================================================
-- sp_reajustar_escala  (Etapa 2 — item 1)
--
-- Move TODAS as escalas de um residente que estejam num
-- (dia_semana, turno) de origem para um (dia_semana, turno) de
-- destino — desde que não gere conflito com a UNIQUE
-- (id_unidade, dia_semana, turno, id_residente).
--
-- Retorna quantas escalas foram movidas. Se qualquer movimento
-- colidir, levanta exceção e nada é alterado (tudo numa
-- transação). Observação: o trigger trg_check_sobreposicao_escala
-- é a segunda barreira — mesmo que a checagem daqui falhasse, o
-- BEFORE UPDATE ainda barraria sobreposição entre unidades.
-- ============================================================

CREATE OR REPLACE FUNCTION sp_reajustar_escala(
    p_id_residente  UUID,
    p_dia_origem    dia_semana_enum,
    p_turno_origem  turno_enum,
    p_dia_destino   dia_semana_enum,
    p_turno_destino turno_enum
) RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    v_conflitos INT;
    v_movidas   INT;
BEGIN
    -- Uma escala de origem colide se já existir, para o mesmo
    -- residente, uma escala na MESMA unidade no destino.
    SELECT COUNT(*) INTO v_conflitos
    FROM ESCALA e_orig
    JOIN ESCALA e_dest
      ON e_dest.id_unidade   = e_orig.id_unidade
     AND e_dest.id_residente = e_orig.id_residente
     AND e_dest.dia_semana   = p_dia_destino
     AND e_dest.turno        = p_turno_destino
    WHERE e_orig.id_residente = p_id_residente
      AND e_orig.dia_semana   = p_dia_origem
      AND e_orig.turno        = p_turno_origem;

    IF v_conflitos > 0 THEN
        RAISE EXCEPTION
            'Reajuste gera conflito: residente % já escalado em %/% em alguma unidade',
            p_id_residente, p_dia_destino, p_turno_destino;
    END IF;

    UPDATE ESCALA
       SET dia_semana = p_dia_destino,
           turno      = p_turno_destino
     WHERE id_residente = p_id_residente
       AND dia_semana   = p_dia_origem
       AND turno        = p_turno_origem;

    GET DIAGNOSTICS v_movidas = ROW_COUNT;
    RETURN v_movidas;
END;
$$;
