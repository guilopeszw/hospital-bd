import psycopg2
from flask import Blueprint, jsonify, request

from db import api_error, execute, query

bp = Blueprint("escalas", __name__)


@bp.route("/api/escalas", methods=["POST"])
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


@bp.route("/api/escalas/reajustar", methods=["POST"])
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


@bp.route("/api/escalas")
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
