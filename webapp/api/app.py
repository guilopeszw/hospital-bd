"""
Como rodar:
    cd webapp/api
    pip install -r requirements.txt
    python app.py
    # API sobe em http://localhost:5055
    # (porta 5055 e não 5000: no macOS o AirPlay ocupa a 5000)
"""

import json
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

    # Os dois campos abaixo vêm das views da Etapa 2 (vw_pacientes_internados,
    # vw_residentes_sem_supervisor) em vez de reimplementar a consulta aqui.
    pacientes_internados = query("SELECT COUNT(*) AS n FROM vw_pacientes_internados", one=True)["n"]
    residentes_sem_supervisor = query(
        "SELECT COUNT(DISTINCT id_residente) AS n FROM vw_residentes_sem_supervisor", one=True
    )["n"]

    return jsonify({
        "total_pacientes": total_pacientes,
        "total_profissionais": total_profissionais,
        "atendimentos_mes": atendimentos_mes,
        "plantoes_hoje": plantoes_hoje,
        "faturamento_mes": float(faturamento_mes),
        "pacientes_sem_risco_alto": pacientes_risco_alto_pendente,
        "pacientes_internados": pacientes_internados,
        "residentes_sem_supervisor": residentes_sem_supervisor,
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


@app.route("/api/pacientes/<id_paciente>", methods=["PUT"])
def atualizar_paciente(id_paciente):
    dados = request.get_json(force=True)
    if not query("SELECT 1 FROM PACIENTE WHERE id_pessoa = %s", (id_paciente,), one=True):
        return api_error("Paciente não encontrado.", 404)
    try:
        resultado = execute(
            """
            UPDATE PACIENTE
               SET num_convenio    = COALESCE(%s, num_convenio),
                   alergias        = COALESCE(%s, alergias),
                   grupo_sanguineo = COALESCE(%s, grupo_sanguineo)
             WHERE id_pessoa = %s
            RETURNING id_pessoa
            """,
            (dados.get("num_convenio"), dados.get("alergias"), dados.get("grupo_sanguineo"), id_paciente),
            returning=True,
        )
        return jsonify(resultado)
    except psycopg2.Error as e:
        return api_error(f"Erro ao atualizar paciente: {e.pgerror or str(e)}", 400)


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


@app.route("/api/profissionais", methods=["POST"])
def cadastrar_profissional():
    dados = request.get_json(force=True)
    tipo = dados.get("tipo")
    if tipo not in ("residente", "preceptor"):
        return api_error("Campo 'tipo' deve ser 'residente' ou 'preceptor'.")
    obrigatorios = ["nome", "cpf", "data_nascimento", "crm", "data_admissao", "especialidade"]
    if tipo == "residente":
        obrigatorios.append("ano_residencia")
    else:
        obrigatorios.append("titulacao")
    faltando = [c for c in obrigatorios if not dados.get(c)]
    if faltando:
        return api_error(f"Campos obrigatórios ausentes: {', '.join(faltando)}")

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO PESSOA (nome, cpf, data_nascimento) VALUES (%s, %s, %s) RETURNING id_pessoa",
                (dados["nome"], dados["cpf"], dados["data_nascimento"]),
            )
            id_pessoa = cur.fetchone()["id_pessoa"]
            cur.execute(
                """INSERT INTO PROFISSIONAL (id_pessoa, crm, data_admissao, especialidade, papel_atual)
                   VALUES (%s, %s, %s, %s, %s)""",
                (id_pessoa, dados["crm"], dados["data_admissao"], dados["especialidade"], tipo),
            )
            if tipo == "residente":
                cur.execute(
                    "INSERT INTO RESIDENTE (id_pessoa, ano_residencia) VALUES (%s, %s)",
                    (id_pessoa, dados["ano_residencia"]),
                )
            else:
                cur.execute(
                    "INSERT INTO PRECEPTOR (id_pessoa, titulacao) VALUES (%s, %s)",
                    (id_pessoa, dados["titulacao"]),
                )
            conn.commit()
            return jsonify({"id_pessoa": id_pessoa}), 201
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return api_error("Já existe um profissional cadastrado com esse CPF.", 409)
    except psycopg2.Error as e:
        conn.rollback()
        return api_error(f"Erro ao cadastrar profissional: {e.pgerror or str(e)}", 400)
    finally:
        conn.close()


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
    """Registra um atendimento. Se o body trouxer `procedimentos` (lista),
    delega para a stored procedure `sp_registrar_atendimento_completo`
    (Etapa 2 — item 1): atendimento + procedimentos numa transação só,
    com rollback automático se qualquer item falhar. Sem `procedimentos`,
    cai no INSERT direto de sempre (atendimento sozinho)."""
    dados = request.get_json(force=True)
    obrigatorios = ["data_hora", "duracao_minutos", "id_paciente", "id_residente", "id_preceptor", "id_unidade"]
    faltando = [c for c in obrigatorios if not dados.get(c)]
    if faltando:
        return api_error(f"Campos obrigatórios ausentes: {', '.join(faltando)}")

    for tabela, campo in [("PACIENTE", "id_paciente"), ("RESIDENTE", "id_residente"), ("PRECEPTOR", "id_preceptor")]:
        existe = query(f"SELECT 1 FROM {tabela} WHERE id_pessoa = %s", (dados[campo],), one=True)
        if not existe:
            return api_error(f"{tabela.capitalize()} não encontrado.", 404)
    if not query("SELECT 1 FROM UNIDADE WHERE id_unidade = %s", (dados["id_unidade"],), one=True):
        return api_error("Unidade não encontrada.", 404)

    procedimentos = dados.get("procedimentos")
    try:
        if procedimentos:
            # execute(), não query(): a function faz INSERT por dentro
            # (atendimento + procedimentos), query() nunca comita e o
            # efeito seria descartado ao fechar a conexão.
            resultado = execute(
                "SELECT sp_registrar_atendimento_completo(%s, %s, %s, %s, %s, %s, %s::jsonb) AS id_atendimento",
                (dados["data_hora"], dados["duracao_minutos"], dados["id_paciente"],
                 dados["id_residente"], dados["id_preceptor"], dados["id_unidade"],
                 json.dumps(procedimentos)),
                returning=True,
            )
        else:
            resultado = execute(
                """
                INSERT INTO ATENDIMENTO (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor, id_unidade)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id_atendimento
                """,
                (dados["data_hora"], dados["duracao_minutos"], dados["id_paciente"],
                 dados["id_residente"], dados["id_preceptor"], dados["id_unidade"]),
                returning=True,
            )
        return jsonify(resultado), 201
    except psycopg2.Error as e:
        return api_error(f"Erro ao registrar atendimento: {e.pgerror or str(e)}", 400)


@app.route("/api/atendimentos/<id_atendimento>/procedimentos", methods=["GET"])
def listar_procedimentos_atendimento(id_atendimento):
    sql = """
        SELECT pr.id_procedimento, p.nome AS procedimento, p.nivel_risco,
               pr.quantidade, pr.tempo_real_minutos, pr.data_hora_inicio, pr.observacao,
               EXISTS (
                   SELECT 1 FROM FATURAMENTO f
                   WHERE f.id_atendimento = pr.id_atendimento AND f.id_procedimento = pr.id_procedimento
               ) AS faturado
        FROM PROCEDIMENTO_REALIZADO pr
        JOIN PROCEDIMENTO p ON p.id_procedimento = pr.id_procedimento
        WHERE pr.id_atendimento = %s
        ORDER BY pr.data_hora_inicio
    """
    return jsonify(query(sql, (id_atendimento,)))


@app.route("/api/atendimentos/<id_atendimento>/procedimentos", methods=["POST"])
def registrar_procedimento(id_atendimento):
    """INSERT em PROCEDIMENTO_REALIZADO — dispara automaticamente o
    trigger trg_atualiza_media_procedimentos (Etapa 2 — item 2), que
    recalcula PROCEDIMENTO.media_tempo_procedimento."""
    dados = request.get_json(force=True)
    obrigatorios = ["id_procedimento", "tempo_real_minutos", "data_hora_inicio"]
    faltando = [c for c in obrigatorios if not dados.get(c)]
    if faltando:
        return api_error(f"Campos obrigatórios ausentes: {', '.join(faltando)}")

    if not query("SELECT 1 FROM ATENDIMENTO WHERE id_atendimento = %s", (id_atendimento,), one=True):
        return api_error("Atendimento não encontrado.", 404)
    if not query("SELECT 1 FROM PROCEDIMENTO WHERE id_procedimento = %s", (dados["id_procedimento"],), one=True):
        return api_error("Procedimento não encontrado.", 404)

    try:
        execute(
            """
            INSERT INTO PROCEDIMENTO_REALIZADO
                (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio, observacao)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (id_atendimento, dados["id_procedimento"], dados.get("quantidade", 1),
             dados["tempo_real_minutos"], dados["data_hora_inicio"], dados.get("observacao")),
        )
        return jsonify({"id_atendimento": id_atendimento, "id_procedimento": dados["id_procedimento"]}), 201
    except psycopg2.errors.UniqueViolation:
        return api_error("Esse procedimento já foi registrado nesse atendimento.", 409)
    except psycopg2.Error as e:
        return api_error(f"Erro ao registrar procedimento: {e.pgerror or str(e)}", 400)


@app.route("/api/atendimentos/<id_atendimento>/procedimentos/<id_procedimento>", methods=["DELETE"])
def remover_procedimento_realizado(id_atendimento, id_procedimento):
    """Bloqueado se já houver faturamento associado — mesma regra da CLI
    (Etapa 1, item 3) e do ORM (crud_orm.remover_procedimento_realizado)."""
    tem_faturamento = query(
        "SELECT 1 FROM FATURAMENTO WHERE id_atendimento = %s AND id_procedimento = %s",
        (id_atendimento, id_procedimento), one=True,
    )
    if tem_faturamento:
        return api_error("Procedimento já faturado — remoção bloqueada.", 409)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM PROCEDIMENTO_REALIZADO WHERE id_atendimento = %s AND id_procedimento = %s",
                (id_atendimento, id_procedimento),
            )
            apagadas = cur.rowcount
            conn.commit()
    finally:
        conn.close()

    if apagadas == 0:
        return api_error("Procedimento realizado não encontrado.", 404)
    return "", 204


# Faturamento


@app.route("/api/faturamentos", methods=["POST"])
def criar_faturamento():
    dados = request.get_json(force=True)
    obrigatorios = ["id_atendimento", "id_procedimento", "valor"]
    faltando = [c for c in obrigatorios if not dados.get(c)]
    if faltando:
        return api_error(f"Campos obrigatórios ausentes: {', '.join(faltando)}")

    try:
        resultado = execute(
            """
            INSERT INTO FATURAMENTO (id_atendimento, id_procedimento, valor)
            VALUES (%s, %s, %s)
            RETURNING id_faturamento
            """,
            (dados["id_atendimento"], dados["id_procedimento"], dados["valor"]),
            returning=True,
        )
        return jsonify(resultado), 201
    except psycopg2.errors.UniqueViolation:
        return api_error("Esse procedimento realizado já foi faturado.", 409)
    except psycopg2.errors.ForeignKeyViolation:
        return api_error("Atendimento/procedimento realizado não encontrado.", 404)
    except psycopg2.Error as e:
        return api_error(f"Erro ao faturar: {e.pgerror or str(e)}", 400)

# Unidades, procedimentos e escalas

@app.route("/api/unidades")
def listar_unidades():
    return jsonify(query("SELECT * FROM UNIDADE ORDER BY nome"))


@app.route("/api/unidades", methods=["POST"])
def cadastrar_unidade():
    dados = request.get_json(force=True)
    obrigatorios = ["nome", "tipo", "capacidade_leitos"]
    faltando = [c for c in obrigatorios if dados.get(c) is None]
    if faltando:
        return api_error(f"Campos obrigatórios ausentes: {', '.join(faltando)}")
    try:
        resultado = execute(
            "INSERT INTO UNIDADE (nome, tipo, capacidade_leitos) VALUES (%s, %s, %s) RETURNING id_unidade",
            (dados["nome"], dados["tipo"], dados["capacidade_leitos"]),
            returning=True,
        )
        return jsonify(resultado), 201
    except psycopg2.Error as e:
        return api_error(f"Erro ao cadastrar unidade: {e.pgerror or str(e)}", 400)


@app.route("/api/procedimentos")
def listar_procedimentos():
    return jsonify(query("SELECT * FROM PROCEDIMENTO ORDER BY nome"))


@app.route("/api/escalas", methods=["POST"])
def cadastrar_escala():
    """INSERT em ESCALA — dispara trg_check_sobreposicao_escala (Etapa 2 —
    item 2): barra o mesmo residente em duas unidades no mesmo dia/turno."""
    dados = request.get_json(force=True)
    obrigatorios = ["id_unidade", "dia_semana", "turno", "id_residente", "id_preceptor"]
    faltando = [c for c in obrigatorios if not dados.get(c)]
    if faltando:
        return api_error(f"Campos obrigatórios ausentes: {', '.join(faltando)}")
    try:
        resultado = execute(
            """INSERT INTO ESCALA (id_unidade, dia_semana, turno, id_residente, id_preceptor)
               VALUES (%s, %s, %s, %s, %s) RETURNING id_escala""",
            (dados["id_unidade"], dados["dia_semana"], dados["turno"],
             dados["id_residente"], dados["id_preceptor"]),
            returning=True,
        )
        return jsonify(resultado), 201
    except psycopg2.errors.UniqueViolation:
        return api_error("Esse residente já está escalado nesse dia/turno/unidade.", 409)
    except psycopg2.errors.RaiseException as e:
        # Levantado pelo trigger trg_check_sobreposicao_escala. diag.message_primary
        # é só a mensagem do RAISE, sem o CONTEXT/traceback do PL/pgSQL.
        return api_error(e.diag.message_primary or str(e).splitlines()[0], 409)
    except psycopg2.Error as e:
        return api_error(f"Erro ao cadastrar escala: {e.pgerror or str(e)}", 400)


@app.route("/api/escalas/reajustar", methods=["POST"])
def reajustar_escala():
    """Chama a stored procedure sp_reajustar_escala (Etapa 2 — item 1):
    move todas as escalas de um residente de um slot pra outro numa
    transação só, com rollback se colidir."""
    dados = request.get_json(force=True)
    obrigatorios = ["id_residente", "dia_origem", "turno_origem", "dia_destino", "turno_destino"]
    faltando = [c for c in obrigatorios if not dados.get(c)]
    if faltando:
        return api_error(f"Campos obrigatórios ausentes: {', '.join(faltando)}")
    try:
        # execute(), não query(): a function faz UPDATE por dentro; query()
        # nunca comita e o reajuste seria descartado ao fechar a conexão.
        resultado = execute(
            """SELECT sp_reajustar_escala(
                   %s, %s::dia_semana_enum, %s::turno_enum,
                   %s::dia_semana_enum, %s::turno_enum
               ) AS escalas_movidas""",
            (dados["id_residente"], dados["dia_origem"], dados["turno_origem"],
             dados["dia_destino"], dados["turno_destino"]),
            returning=True,
        )
        return jsonify(resultado)
    except psycopg2.errors.RaiseException as e:
        # Pode vir da própria sp_reajustar_escala (conflito na unidade de
        # destino) ou do trigger trg_check_sobreposicao_escala (conflito
        # entre unidades diferentes) — message_primary cobre os dois.
        return api_error(e.diag.message_primary or str(e).splitlines()[0], 409)
    except psycopg2.Error as e:
        return api_error(f"Erro ao reajustar escala: {e.pgerror or str(e)}", 400)


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


@app.route("/api/analytics/tempo-medio-espera")
def analytics_tempo_medio_espera():
    """Chama a stored procedure sp_calcular_tempo_medio_espera (Etapa 2 —
    item 1): tempo médio entre chegada e 1º procedimento, por unidade."""
    return jsonify(query("SELECT * FROM sp_calcular_tempo_medio_espera()"))


# Views (Etapa 2 — item 3)

@app.route("/api/views/pacientes-internados")
def views_pacientes_internados():
    return jsonify(query("SELECT * FROM vw_pacientes_internados"))


@app.route("/api/views/residentes-sem-supervisor")
def views_residentes_sem_supervisor():
    return jsonify(query("SELECT * FROM vw_residentes_sem_supervisor"))


@app.route("/api/views/estatisticas-mensais")
def views_estatisticas_mensais():
    return jsonify(query("SELECT * FROM vw_estatisticas_atendimentos_mensal"))


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
    # Porta 8000 (não 5000): no macOS o AirPlay/Control Center ocupa a
    # 5000 e responde 403, impedindo o front-end de alcançar a API.
    # Sobrescreva com a env PORT se precisar.
    app.run(debug=True, port=int(os.getenv("PORT", "5055")))
