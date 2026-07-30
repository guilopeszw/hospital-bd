"""
Como rodar:
    cd webapp/api
    pip install -r requirements.txt
    python app.py
    # API sobe em http://localhost:5000
"""

import os
from datetime import datetime, date, timedelta

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request
from flask_cors import CORS

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "dbname=hospital_db user=postgres password=password host=localhost port=5433",
)

DIA_SEMANA_PT = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]

app = Flask(__name__)
CORS(app)


def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def query(sql, params=None, one=False):
    """Executa um SELECT e devolve lista de dicts (ou um dict se one=True)."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            rows = [dict(r) for r in rows]
            return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def execute(sql, params=None, returning=False):
    """Executa um INSERT/UPDATE/DELETE. Se returning=True, devolve a linha retornada."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            result = dict(cur.fetchone()) if returning and cur.description else None
            conn.commit()
            return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def api_error(message, status=400):
    return jsonify({"erro": message}), status

# Dashboard


@app.route("/api/dashboard/summary")
def dashboard_summary():
    hoje = date.today()
    dia_semana_hoje = DIA_SEMANA_PT[hoje.weekday()]

    total_pacientes = query("SELECT COUNT(*) AS n FROM PACIENTE", one=True)["n"]
    total_profissionais = query("SELECT COUNT(*) AS n FROM PROFISSIONAL", one=True)["n"]

    atendimentos_mes = query(
        """
        SELECT COUNT(*) AS n FROM ATENDIMENTO
        WHERE date_trunc('month', data_hora) = date_trunc('month', CURRENT_DATE)
        """,
        one=True,
    )["n"]

    plantoes_hoje = query(
        "SELECT COUNT(*) AS n FROM ESCALA WHERE dia_semana = %s",
        (dia_semana_hoje,),
        one=True,
    )["n"]

    faturamento_mes = query(
        """
        SELECT COALESCE(SUM(valor), 0) AS total FROM FATURAMENTO
        WHERE date_trunc('month', data_emissao) = date_trunc('month', CURRENT_DATE)
        """,
        one=True,
    )["total"]

    pacientes_risco_alto_pendente = query(
        """
        SELECT COUNT(*) AS n
        FROM PACIENTE pac
        WHERE NOT EXISTS (
            SELECT 1 FROM ATENDIMENTO a
            JOIN PROCEDIMENTO_REALIZADO pr ON pr.id_atendimento = a.id_atendimento
            JOIN PROCEDIMENTO proc ON proc.id_procedimento = pr.id_procedimento
            WHERE a.id_paciente = pac.id_pessoa AND proc.nivel_risco = 'ALTO'
        )
        """,
        one=True,
    )["n"]

    return jsonify({
        "total_pacientes": total_pacientes,
        "total_profissionais": total_profissionais,
        "atendimentos_mes": atendimentos_mes,
        "plantoes_hoje": plantoes_hoje,
        "faturamento_mes": float(faturamento_mes),
        "pacientes_sem_risco_alto": pacientes_risco_alto_pendente,
    })



# Pacientes


@app.route("/api/pacientes", methods=["GET"])
def listar_pacientes():
    busca = request.args.get("busca", "").strip()
    sql = """
        SELECT p.id_pessoa, p.nome, p.cpf, p.data_nascimento, p.telefone,
               pac.num_convenio, pac.alergias, pac.grupo_sanguineo
        FROM PACIENTE pac
        JOIN PESSOA p ON p.id_pessoa = pac.id_pessoa
    """
    params = ()
    if busca:
        sql += " WHERE p.nome ILIKE %s OR p.cpf ILIKE %s"
        params = (f"%{busca}%", f"%{busca}%")
    sql += " ORDER BY p.nome"
    return jsonify(query(sql, params))


@app.route("/api/pacientes", methods=["POST"])
def criar_paciente():
    dados = request.get_json(force=True)
    obrigatorios = ["nome", "cpf", "data_nascimento"]
    faltando = [c for c in obrigatorios if not dados.get(c)]
    if faltando:
        return api_error(f"Campos obrigatórios ausentes: {', '.join(faltando)}")

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO PESSOA (nome, cpf, data_nascimento, telefone)
                VALUES (%s, %s, %s, %s)
                RETURNING id_pessoa
                """,
                (dados["nome"], dados["cpf"], dados["data_nascimento"], dados.get("telefone")),
            )
            id_pessoa = cur.fetchone()["id_pessoa"]

            cur.execute(
                """
                INSERT INTO PACIENTE (id_pessoa, num_convenio, alergias, grupo_sanguineo)
                VALUES (%s, %s, %s, %s)
                """,
                (id_pessoa, dados.get("num_convenio"), dados.get("alergias"), dados.get("grupo_sanguineo")),
            )
            conn.commit()
            return jsonify({"id_pessoa": id_pessoa}), 201
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return api_error("Já existe um paciente cadastrado com esse CPF.", 409)
    except psycopg2.Error as e:
        conn.rollback()
        return api_error(f"Erro ao cadastrar paciente: {e.pgerror or str(e)}", 400)
    finally:
        conn.close()


@app.route("/api/pacientes/<id_paciente>/atendimentos")
def atendimentos_do_paciente(id_paciente):
    sql = """
        SELECT a.id_atendimento, a.data_hora, a.duracao_minutos,
               rp.nome AS residente, prp.nome AS preceptor
        FROM ATENDIMENTO a
        JOIN RESIDENTE    res ON a.id_residente = res.id_pessoa
        JOIN PESSOA       rp  ON res.id_pessoa   = rp.id_pessoa
        JOIN PRECEPTOR    pre ON a.id_preceptor  = pre.id_pessoa
        JOIN PESSOA       prp ON pre.id_pessoa   = prp.id_pessoa
        WHERE a.id_paciente = %s
        ORDER BY a.data_hora DESC
    """
    return jsonify(query(sql, (id_paciente,)))


# Profissionais (residentes + preceptores)

@app.route("/api/profissionais")
def listar_profissionais():
    sql = """
        SELECT p.id_pessoa, p.nome, p.cpf, prof.crm, prof.especialidade,
               prof.papel_atual, prof.data_admissao,
               res.ano_residencia, pre.titulacao
        FROM PROFISSIONAL prof
        JOIN PESSOA p ON p.id_pessoa = prof.id_pessoa
        LEFT JOIN RESIDENTE res ON res.id_pessoa = prof.id_pessoa
        LEFT JOIN PRECEPTOR pre ON pre.id_pessoa = prof.id_pessoa
        ORDER BY p.nome
    """
    return jsonify(query(sql))


# Atendimentos

@app.route("/api/atendimentos", methods=["GET"])
def listar_atendimentos():
    limite = request.args.get("limite", 50, type=int)
    sql = """
        SELECT a.id_atendimento, a.data_hora, a.duracao_minutos,
               pp.nome AS paciente, rp.nome AS residente, prp.nome AS preceptor
        FROM ATENDIMENTO a
        JOIN PACIENTE     pac ON a.id_paciente  = pac.id_pessoa
        JOIN PESSOA       pp  ON pac.id_pessoa  = pp.id_pessoa
        JOIN RESIDENTE    res ON a.id_residente = res.id_pessoa
        JOIN PESSOA       rp  ON res.id_pessoa  = rp.id_pessoa
        JOIN PRECEPTOR    pre ON a.id_preceptor = pre.id_pessoa
        JOIN PESSOA       prp ON pre.id_pessoa  = prp.id_pessoa
        ORDER BY a.data_hora DESC
        LIMIT %s
    """
    return jsonify(query(sql, (limite,)))


@app.route("/api/atendimentos", methods=["POST"])
def criar_atendimento():
    dados = request.get_json(force=True)
    obrigatorios = ["data_hora", "duracao_minutos", "id_paciente", "id_residente", "id_preceptor"]
    faltando = [c for c in obrigatorios if not dados.get(c)]
    if faltando:
        return api_error(f"Campos obrigatórios ausentes: {', '.join(faltando)}")

    for tabela, campo in [("PACIENTE", "id_paciente"), ("RESIDENTE", "id_residente"), ("PRECEPTOR", "id_preceptor")]:
        existe = query(f"SELECT 1 FROM {tabela} WHERE id_pessoa = %s", (dados[campo],), one=True)
        if not existe:
            return api_error(f"{tabela.capitalize()} não encontrado.", 404)

    try:
        resultado = execute(
            """
            INSERT INTO ATENDIMENTO (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_atendimento
            """,
            (dados["data_hora"], dados["duracao_minutos"], dados["id_paciente"], dados["id_residente"], dados["id_preceptor"]),
            returning=True,
        )
        return jsonify(resultado), 201
    except psycopg2.Error as e:
        return api_error(f"Erro ao registrar atendimento: {e.pgerror or str(e)}", 400)

# Unidades, procedimentos e escalas

@app.route("/api/unidades")
def listar_unidades():
    return jsonify(query("SELECT * FROM UNIDADE ORDER BY nome"))


@app.route("/api/procedimentos")
def listar_procedimentos():
    return jsonify(query("SELECT * FROM PROCEDIMENTO ORDER BY nome"))


@app.route("/api/escalas")
def listar_escalas():
    sql = """
        SELECT e.id_escala, u.nome AS unidade, e.dia_semana, e.turno,
               rp.nome AS residente, prp.nome AS preceptor
        FROM ESCALA e
        JOIN UNIDADE u ON e.id_unidade = u.id_unidade
        JOIN RESIDENTE res ON e.id_residente = res.id_pessoa
        JOIN PESSOA rp ON res.id_pessoa = rp.id_pessoa
        JOIN PRECEPTOR pre ON e.id_preceptor = pre.id_pessoa
        JOIN PESSOA prp ON pre.id_pessoa = prp.id_pessoa
        ORDER BY u.nome,
                 array_position(ARRAY['segunda','terca','quarta','quinta','sexta','sabado','domingo'], e.dia_semana::text),
                 array_position(ARRAY['manha','tarde','noite'], e.turno::text)
    """
    return jsonify(query(sql))



# Indicadores analíticos

@app.route("/api/analytics/ranking-residentes")
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


@app.route("/api/analytics/preceptores-mais-atendimentos")
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


@app.route("/api/analytics/plantoes-mes")
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


@app.route("/api/analytics/pacientes-sem-risco-alto")
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


@app.route("/api/analytics/tempo-medio-residente")
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


@app.route("/api/health")
def health():
    try:
        query("SELECT 1", one=True)
        return jsonify({"status": "ok", "db": "conectado"})
    except Exception as e:
        return jsonify({"status": "erro", "detalhe": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
