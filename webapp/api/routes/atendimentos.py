import json

import psycopg2
from flask import Blueprint, jsonify, request

from db import api_error, execute, get_connection, query

bp = Blueprint("atendimentos", __name__)


@bp.route("/api/atendimentos", methods=["GET"])
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


@bp.route("/api/atendimentos", methods=["POST"])
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


@bp.route("/api/atendimentos/<id_atendimento>/procedimentos", methods=["GET"])
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


@bp.route("/api/atendimentos/<id_atendimento>/procedimentos", methods=["POST"])
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


@bp.route("/api/atendimentos/<id_atendimento>/procedimentos/<id_procedimento>", methods=["DELETE"])
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
