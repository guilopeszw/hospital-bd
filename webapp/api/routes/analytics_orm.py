"""Expõe as 3 consultas avançadas via ORM (Etapa 2 — item 5,
src/etapa2/consultas_avancadas.py) pro frontend. Só leitura — nenhuma
lógica de negócio nova aqui, é fina camada HTTP sobre a DSL do SQLAlchemy."""
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from flask import Blueprint, jsonify
from src.etapa2 import consultas_avancadas as ca

bp = Blueprint("analytics_orm", __name__)

@bp.route("/api/orm/preceptores-supervisionaram-flamenguistas")
def preceptores_flamenguistas():
    return jsonify(ca.preceptores_supervisionaram_flamenguistas())

@bp.route("/api/orm/ultimo-atendimento-por-paciente")
def ultimo_atendimento_por_paciente():
    return jsonify(ca.ultimo_atendimento_por_paciente())

@bp.route("/api/orm/percentual-alto-risco-por-residente")
def percentual_alto_risco_por_residente():
    return jsonify(ca.percentual_procedimentos_alto_risco_por_residente())
