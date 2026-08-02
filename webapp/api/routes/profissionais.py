import psycopg2
import psycopg2.extras
from flask import Blueprint, jsonify, request

from db import api_error, get_connection, query

bp = Blueprint("profissionais", __name__)


@bp.route("/api/profissionais")
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


@bp.route("/api/profissionais", methods=["POST"])
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
