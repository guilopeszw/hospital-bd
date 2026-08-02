from datetime import date

from flask import Blueprint, jsonify, request

from db import query

bp = Blueprint("analytics", __name__)


@bp.route("/api/analytics/ranking-residentes")
def analytics_ranking_residentes():
    sql = """
        SELECT p.nome AS residente, res.ano_residencia,
               COUNT(a.id_atendimento) AS total_atendimentos
        FROM RESIDENTE res
        JOIN PESSOA p ON p.id_pessoa = res.id_pessoa
        LEFT JOIN ATENDIMENTO a ON a.id_residente = res.id_pessoa
        GROUP BY res.id_pessoa, p.nome, res.ano_residencia
        ORDER BY total_atendimentos DESC, p.nome
    """
    return jsonify(query(sql))


@bp.route("/api/analytics/preceptores-mais-atendimentos")
def analytics_preceptores_mes():
    hoje = date.today()
    ano = request.args.get("ano", hoje.year, type=int)
    mes = request.args.get("mes", hoje.month, type=int)
    minimo = request.args.get("minimo", 0, type=int)
    sql = """
        SELECT p.nome AS preceptor, COUNT(a.id_atendimento) AS total_atendimentos
        FROM ATENDIMENTO a
        JOIN PRECEPTOR pre ON a.id_preceptor = pre.id_pessoa
        JOIN PESSOA p ON pre.id_pessoa = p.id_pessoa
        WHERE EXTRACT(YEAR FROM a.data_hora) = %s AND EXTRACT(MONTH FROM a.data_hora) = %s
        GROUP BY p.nome
        HAVING COUNT(a.id_atendimento) > %s
        ORDER BY total_atendimentos DESC
    """
    return jsonify(query(sql, (ano, mes, minimo)))


@bp.route("/api/analytics/plantoes-mes")
def analytics_plantoes_mes():
    sql = """
        WITH dias_mes AS (
            SELECT dia::date AS dia
            FROM generate_series(
                date_trunc('month', CURRENT_DATE),
                date_trunc('month', CURRENT_DATE) + interval '1 month' - interval '1 day',
                interval '1 day'
            ) AS dia
        ),
        mapa_dia AS (
            SELECT dia, (CASE EXTRACT(DOW FROM dia)
                WHEN 0 THEN 'domingo' WHEN 1 THEN 'segunda' WHEN 2 THEN 'terca'
                WHEN 3 THEN 'quarta'  WHEN 4 THEN 'quinta'  WHEN 5 THEN 'sexta'
                WHEN 6 THEN 'sabado' END)::dia_semana_enum AS dia_semana
            FROM dias_mes
        )
        SELECT u.nome AS unidade, p.nome AS residente, COUNT(*) AS total_plantoes_no_mes
        FROM ESCALA e
        JOIN mapa_dia m ON m.dia_semana = e.dia_semana
        JOIN UNIDADE u ON u.id_unidade = e.id_unidade
        JOIN RESIDENTE res ON res.id_pessoa = e.id_residente
        JOIN PESSOA p ON p.id_pessoa = res.id_pessoa
        GROUP BY u.nome, p.nome
        ORDER BY u.nome, total_plantoes_no_mes DESC
    """
    return jsonify(query(sql))


@bp.route("/api/analytics/pacientes-sem-risco-alto")
def analytics_pacientes_sem_risco_alto():
    sql = """
        SELECT p.nome AS paciente, pac.num_convenio
        FROM PACIENTE pac
        JOIN PESSOA p ON p.id_pessoa = pac.id_pessoa
        WHERE NOT EXISTS (
            SELECT 1 FROM ATENDIMENTO a
            JOIN PROCEDIMENTO_REALIZADO pr ON pr.id_atendimento = a.id_atendimento
            JOIN PROCEDIMENTO proc ON proc.id_procedimento = pr.id_procedimento
            WHERE a.id_paciente = pac.id_pessoa AND proc.nivel_risco = 'ALTO'
        )
        ORDER BY p.nome
    """
    return jsonify(query(sql))


@bp.route("/api/analytics/tempo-medio-espera")
def analytics_tempo_medio_espera():
    """Chama a stored procedure sp_calcular_tempo_medio_espera (Etapa 2 —
    item 1): tempo médio entre chegada e 1º procedimento, por unidade."""
    return jsonify(query("SELECT * FROM sp_calcular_tempo_medio_espera()"))


@bp.route("/api/analytics/tempo-medio-residente")
def analytics_tempo_medio_residente():
    sql = """
        SELECT res.id_pessoa AS id_residente, p.nome AS residente, prof.especialidade,
               res.ano_residencia, COUNT(a.id_atendimento) AS total_atendimentos,
               ROUND(AVG(a.duracao_minutos), 2) AS tempo_medio_minutos
        FROM RESIDENTE res
        JOIN PESSOA p ON p.id_pessoa = res.id_pessoa
        JOIN PROFISSIONAL prof ON prof.id_pessoa = res.id_pessoa
        LEFT JOIN ATENDIMENTO a ON a.id_residente = res.id_pessoa
        GROUP BY res.id_pessoa, p.nome, prof.especialidade, res.ano_residencia
        ORDER BY tempo_medio_minutos DESC NULLS LAST, p.nome
    """
    return jsonify(query(sql))
