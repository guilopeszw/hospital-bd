from flask import Blueprint, jsonify

from db import query

bp = Blueprint("health", __name__)


@bp.route("/api/health")
def health():
    try:
        query("SELECT 1", one=True)
        return jsonify({"status": "ok", "db": "conectado"})
    except Exception as e:
        return jsonify({"status": "erro", "detalhe": str(e)}), 500
