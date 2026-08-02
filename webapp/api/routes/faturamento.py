import psycopg2
from flask import Blueprint, jsonify, request

from db import api_error, execute

bp = Blueprint("faturamento", __name__)


@bp.route("/api/faturamentos", methods=["POST"])
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
