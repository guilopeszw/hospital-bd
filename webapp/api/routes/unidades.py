import psycopg2
from flask import Blueprint, jsonify, request

from db import api_error, execute, query

bp = Blueprint("unidades", __name__)


@bp.route("/api/unidades")
def listar_unidades():
    return jsonify(query("SELECT * FROM UNIDADE ORDER BY nome"))


@bp.route("/api/unidades", methods=["POST"])
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


@bp.route("/api/procedimentos")
def listar_procedimentos():
    return jsonify(query("SELECT * FROM PROCEDIMENTO ORDER BY nome"))
