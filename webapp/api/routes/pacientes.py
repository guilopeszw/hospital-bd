import psycopg2
import psycopg2.extras
from flask import Blueprint, jsonify, request

from db import api_error, execute, get_connection, query

bp = Blueprint("pacientes", __name__)


@bp.route("/api/pacientes", methods=["GET"])
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


@bp.route("/api/pacientes", methods=["POST"])
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


@bp.route("/api/pacientes/<id_paciente>", methods=["PUT"])
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


@bp.route("/api/pacientes/<id_paciente>/atendimentos")
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
