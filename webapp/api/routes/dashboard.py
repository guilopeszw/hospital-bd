from datetime import date

from flask import Blueprint, jsonify

from db import query

bp = Blueprint("dashboard", __name__)

DIA_SEMANA_PT = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]


@bp.route("/api/dashboard/summary")
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
