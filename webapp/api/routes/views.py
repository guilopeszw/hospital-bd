from flask import Blueprint, jsonify

from db import query

bp = Blueprint("views", __name__)


@bp.route("/api/views/pacientes-internados")
def views_pacientes_internados():
    return jsonify(query("SELECT * FROM vw_pacientes_internados"))


@bp.route("/api/views/residentes-sem-supervisor")
def views_residentes_sem_supervisor():
    return jsonify(query("SELECT * FROM vw_residentes_sem_supervisor"))


@bp.route("/api/views/estatisticas-mensais")
def views_estatisticas_mensais():
    return jsonify(query("SELECT * FROM vw_estatisticas_atendimentos_mensal"))
