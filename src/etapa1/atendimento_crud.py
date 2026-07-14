
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "dbname=hospital_db user=postgres password=password host=localhost port=5433",
)


def get_connection():
    return psycopg2.connect(DATABASE_URL)



def inserir_atendimento(data_hora: datetime, duracao: int,
                        id_paciente: str, id_residente: str, id_preceptor: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Validações de existência
        cur.execute("SELECT 1 FROM PACIENTE   WHERE id_pessoa = %s", (id_paciente,))
        if not cur.fetchone():
            print("Erro: paciente não encontrado.")
            return None

        cur.execute("SELECT 1 FROM RESIDENTE  WHERE id_pessoa = %s", (id_residente,))
        if not cur.fetchone():
            print("Erro: residente não encontrado.")
            return None

        cur.execute("SELECT 1 FROM PRECEPTOR  WHERE id_pessoa = %s", (id_preceptor,))
        if not cur.fetchone():
            print("Erro: preceptor não encontrado.")
            return None

        cur.execute("""
            INSERT INTO ATENDIMENTO (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_atendimento
        """, (data_hora, duracao, id_paciente, id_residente, id_preceptor))

        id_novo = cur.fetchone()[0]
        conn.commit()
        print(f" Atendimento criado! ID: {id_novo}")
        return id_novo

    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir atendimento: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def listar_atendimentos_paciente(id_paciente: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT
                a.id_atendimento,
                a.data_hora,
                a.duracao_minutos,
                pp.nome  AS paciente,
                rp.nome  AS residente,
                prp.nome AS preceptor
            FROM ATENDIMENTO a
            JOIN PACIENTE     pac ON a.id_paciente  = pac.id_pessoa
            JOIN PESSOA       pp  ON pac.id_pessoa  = pp.id_pessoa
            JOIN RESIDENTE    res ON a.id_residente = res.id_pessoa
            JOIN PROFISSIONAL rpf ON res.id_pessoa  = rpf.id_pessoa
            JOIN PESSOA       rp  ON rpf.id_pessoa  = rp.id_pessoa
            JOIN PRECEPTOR    pre ON a.id_preceptor = pre.id_pessoa
            JOIN PROFISSIONAL ppf ON pre.id_pessoa  = ppf.id_pessoa
            JOIN PESSOA       prp ON ppf.id_pessoa  = prp.id_pessoa
            WHERE a.id_paciente = %s
            ORDER BY a.data_hora DESC
        """, (id_paciente,))
        rows = cur.fetchall()
        if not rows:
            print("Nenhum atendimento encontrado para este paciente.")
        for r in rows:
            print(r)
        return rows
    finally:
        cur.close()
        conn.close()



def listar_procedimentos_atendimento(id_atendimento: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT
                proc.nome              AS procedimento,
                proc.nivel_risco,
                pr.quantidade,
                pr.tempo_real_minutos,
                pr.observacao,
                (f.id_faturamento IS NOT NULL) AS faturado,
                f.valor                AS valor_faturado
            FROM PROCEDIMENTO_REALIZADO pr
            JOIN PROCEDIMENTO proc ON pr.id_procedimento = proc.id_procedimento
            LEFT JOIN FATURAMENTO f
                   ON f.id_atendimento  = pr.id_atendimento
                  AND f.id_procedimento = pr.id_procedimento
            WHERE pr.id_atendimento = %s
            ORDER BY proc.nome
        """, (id_atendimento,))
        rows = cur.fetchall()
        if not rows:
            print("Nenhum procedimento encontrado para este atendimento.")
        for r in rows:
            print(r)
        return rows
    finally:
        cur.close()
        conn.close()



# ATUALIZAR DADOS DE PACIENTE


def atualizar_paciente(id_paciente: str,
                       novo_convenio: str = None,
                       novas_alergias: str = None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        campos = []
        valores = []

        if novo_convenio is not None:
            campos.append("num_convenio = %s")
            valores.append(novo_convenio)
        if novas_alergias is not None:
            campos.append("alergias = %s")
            valores.append(novas_alergias)

        if not campos:
            print("Nenhum campo para atualizar.")
            return

        valores.append(id_paciente)
        sql = f"UPDATE PACIENTE SET {', '.join(campos)} WHERE id_pessoa = %s"
        cur.execute(sql, valores)
        conn.commit()

        if cur.rowcount == 0:
            print("Paciente não encontrado.")
        else:
            print(f"Paciente {id_paciente} atualizado com sucesso.")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar paciente: {e}")
    finally:
        cur.close()
        conn.close()




def remover_procedimento_realizado(id_atendimento: str, id_procedimento: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM PROCEDIMENTO_REALIZADO pr
            WHERE pr.id_atendimento  = %s
              AND pr.id_procedimento = %s
              AND NOT EXISTS (
                  SELECT 1
                  FROM FATURAMENTO f
                  WHERE f.id_atendimento  = pr.id_atendimento
                    AND f.id_procedimento = pr.id_procedimento
              )
        """, (id_atendimento, id_procedimento))
        conn.commit()

        if cur.rowcount == 0:
            print("Remoção bloqueada: o procedimento tem faturamento associado ou não existe.")
        else:
            print(" Procedimento realizado removido com sucesso.")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao remover procedimento: {e}")
    finally:
        cur.close()
        conn.close()




def tempo_medio_por_residente():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT
                p.nome                           AS residente,
                ROUND(AVG(a.duracao_minutos), 1) AS tempo_medio_minutos,
                COUNT(a.id_atendimento)          AS total_atendimentos
            FROM RESIDENTE res
            JOIN PROFISSIONAL pf ON pf.id_pessoa = res.id_pessoa
            JOIN PESSOA       p  ON p.id_pessoa  = res.id_pessoa
            LEFT JOIN ATENDIMENTO a ON a.id_residente = res.id_pessoa
            GROUP BY res.id_pessoa, p.nome
            ORDER BY tempo_medio_minutos DESC NULLS LAST, p.nome
        """)
        rows = cur.fetchall()
        for r in rows:
            print(r)
        return rows
    finally:
        cur.close()
        conn.close()




def ranking_residentes():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT
                p.nome                      AS residente,
                COUNT(a.id_atendimento)     AS total_atendimentos
            FROM RESIDENTE res
            JOIN PROFISSIONAL pf ON pf.id_pessoa = res.id_pessoa
            JOIN PESSOA       p  ON p.id_pessoa  = res.id_pessoa
            LEFT JOIN ATENDIMENTO a ON a.id_residente = res.id_pessoa
            GROUP BY res.id_pessoa, p.nome
            ORDER BY total_atendimentos DESC, p.nome
        """)
        rows = cur.fetchall()
        print("\n Ranking de Residentes por Atendimentos:")
        for i, r in enumerate(rows, 1):
            print(f"  {i}º {r['residente']} — {r['total_atendimentos']} atendimento(s)")
        return rows
    finally:
        cur.close()
        conn.close()



def preceptores_mais_atendimentos_mes(ano: int, mes: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT
                p.nome                  AS preceptor,
                COUNT(a.id_atendimento) AS total_atendimentos
            FROM ATENDIMENTO a
            JOIN PRECEPTOR    pre ON a.id_preceptor = pre.id_pessoa
            JOIN PROFISSIONAL pf  ON pre.id_pessoa  = pf.id_pessoa
            JOIN PESSOA       p   ON pf.id_pessoa   = p.id_pessoa
            WHERE EXTRACT(YEAR  FROM a.data_hora) = %s
              AND EXTRACT(MONTH FROM a.data_hora) = %s
            GROUP BY p.nome
            HAVING COUNT(a.id_atendimento) > 5
            ORDER BY total_atendimentos DESC
        """, (ano, mes))
        rows = cur.fetchall()
        if not rows:
            print(f"Nenhum preceptor com mais de 5 atendimentos em {mes}/{ano}.")
        for r in rows:
            print(r)
        return rows
    finally:
        cur.close()
        conn.close()


def plantoes_por_unidade_mes():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            WITH dias_mes AS (
                SELECT dia::date AS dia
                FROM generate_series(
                    date_trunc('month', CURRENT_DATE),
                    date_trunc('month', CURRENT_DATE) + interval '1 month' - interval '1 day',
                    interval '1 day'
                ) AS dia
            ),
            mapa_dia AS (
                SELECT dia, (CASE EXTRACT(DOW FROM dia)
                    WHEN 0 THEN 'domingo' WHEN 1 THEN 'segunda' WHEN 2 THEN 'terca'
                    WHEN 3 THEN 'quarta'  WHEN 4 THEN 'quinta'  WHEN 5 THEN 'sexta'
                    WHEN 6 THEN 'sabado' END)::dia_semana_enum AS dia_semana
                FROM dias_mes
            )
            SELECT
                u.nome               AS unidade,
                p.nome               AS residente,
                COUNT(*)             AS total_plantoes_no_mes
            FROM ESCALA e
            JOIN mapa_dia m       ON m.dia_semana = e.dia_semana
            JOIN UNIDADE u        ON u.id_unidade = e.id_unidade
            JOIN RESIDENTE res    ON res.id_pessoa = e.id_residente
            JOIN PROFISSIONAL pf  ON pf.id_pessoa = res.id_pessoa
            JOIN PESSOA p         ON p.id_pessoa = pf.id_pessoa
            GROUP BY u.nome, p.nome
            ORDER BY u.nome, total_plantoes_no_mes DESC
        """)
        rows = cur.fetchall()
        for r in rows:
            print(r)
        return rows
    finally:
        cur.close()
        conn.close()


def pacientes_sem_procedimento_risco_alto():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT p.nome AS paciente, pac.num_convenio
            FROM PACIENTE pac
            JOIN PESSOA p ON p.id_pessoa = pac.id_pessoa
            WHERE NOT EXISTS (
                SELECT 1
                FROM ATENDIMENTO a
                JOIN PROCEDIMENTO_REALIZADO pr ON pr.id_atendimento = a.id_atendimento
                JOIN PROCEDIMENTO proc         ON proc.id_procedimento = pr.id_procedimento
                WHERE a.id_paciente = pac.id_pessoa
                  AND proc.nivel_risco = 'ALTO'
            )
            ORDER BY p.nome
        """)
        rows = cur.fetchall()
        for r in rows:
            print(r)
        return rows
    finally:
        cur.close()
        conn.close()


# ------------------------------------------------------------------
# CADASTROS
# Todos passam pelo _executar: uma transação, commit no sucesso,
# rollback + mensagem no erro (CPF/CRM duplicado, FK inexistente,
# CHECK violado — o banco já barra tudo isso, aqui só traduzimos).
# ------------------------------------------------------------------

def _executar(sql: str, params: tuple, retorna: bool = True):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        valor = cur.fetchone()[0] if retorna else None
        conn.commit()
        return valor
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Erro: {e.diag.message_primary or e}")
        return None
    finally:
        cur.close()
        conn.close()


def cadastrar_paciente(nome, cpf, data_nascimento, telefone=None,
                       num_convenio=None, alergias=None, grupo_sanguineo=None):
    id_novo = _executar("""
        WITH nova_pessoa AS (
            INSERT INTO PESSOA (nome, cpf, data_nascimento, telefone)
            VALUES (%s, %s, %s, %s)
            RETURNING id_pessoa
        )
        INSERT INTO PACIENTE (id_pessoa, num_convenio, alergias, grupo_sanguineo)
        SELECT id_pessoa, %s, %s, %s FROM nova_pessoa
        RETURNING id_pessoa
    """, (nome, cpf, data_nascimento, telefone, num_convenio, alergias, grupo_sanguineo))
    if id_novo:
        print(f"Paciente cadastrado: {id_novo}")
    return id_novo


def cadastrar_profissional(papel, nome, cpf, data_nascimento, crm, data_admissao,
                           especialidade, ano_residencia=None, titulacao=None,
                           telefone=None):
    if papel == "residente" and not ano_residencia:
        print("Erro: residente exige --ano-residencia (R1/R2/R3).")
        return None
    if papel == "preceptor" and not titulacao:
        print("Erro: preceptor exige --titulacao.")
        return None

    subtipo = ("INSERT INTO RESIDENTE (id_pessoa, ano_residencia) SELECT id_pessoa, %s FROM novo_prof"
               if papel == "residente" else
               "INSERT INTO PRECEPTOR (id_pessoa, titulacao) SELECT id_pessoa, %s FROM novo_prof")

    id_novo = _executar(f"""
        WITH nova_pessoa AS (
            INSERT INTO PESSOA (nome, cpf, data_nascimento, telefone)
            VALUES (%s, %s, %s, %s)
            RETURNING id_pessoa
        ), novo_prof AS (
            INSERT INTO PROFISSIONAL (id_pessoa, crm, data_admissao, especialidade, papel_atual)
            SELECT id_pessoa, %s, %s, %s, %s FROM nova_pessoa
            RETURNING id_pessoa
        )
        {subtipo}
        RETURNING id_pessoa
    """, (nome, cpf, data_nascimento, telefone, crm, data_admissao, especialidade, papel,
          ano_residencia if papel == "residente" else titulacao))
    if id_novo:
        print(f"{papel.capitalize()} cadastrado: {id_novo}")
    return id_novo


def cadastrar_unidade(nome, tipo, capacidade_leitos):
    id_novo = _executar("""
        INSERT INTO UNIDADE (nome, tipo, capacidade_leitos)
        VALUES (%s, %s, %s) RETURNING id_unidade
    """, (nome, tipo, capacidade_leitos))
    if id_novo:
        print(f"Unidade cadastrada: {id_novo}")
    return id_novo


def cadastrar_escala(id_unidade, dia_semana, turno, id_residente, id_preceptor):
    id_novo = _executar("""
        INSERT INTO ESCALA (id_unidade, dia_semana, turno, id_residente, id_preceptor)
        VALUES (%s, %s, %s, %s, %s) RETURNING id_escala
    """, (id_unidade, dia_semana, turno, id_residente, id_preceptor))
    if id_novo:
        print(f"Escala cadastrada: {id_novo}")
    return id_novo


def registrar_procedimento(id_atendimento, id_procedimento, quantidade,
                           tempo_real_minutos, observacao=None):
    ok = _executar("""
        INSERT INTO PROCEDIMENTO_REALIZADO
            (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, observacao)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_atendimento
    """, (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, observacao))
    if ok:
        print("Procedimento registrado no atendimento.")
    return ok


def faturar_procedimento(id_atendimento, id_procedimento, valor, data_emissao=None):
    id_novo = _executar("""
        INSERT INTO FATURAMENTO (id_atendimento, id_procedimento, valor, data_emissao)
        VALUES (%s, %s, %s, COALESCE(%s::date, CURRENT_DATE))
        RETURNING id_faturamento
    """, (id_atendimento, id_procedimento, valor, data_emissao))
    if id_novo:
        print(f"Faturamento emitido: {id_novo} (procedimento agora não pode ser removido)")
    return id_novo


LISTAGENS = {
    "pacientes": """SELECT pac.id_pessoa AS id, p.nome, p.cpf, pac.num_convenio, pac.grupo_sanguineo
                    FROM PACIENTE pac JOIN PESSOA p USING (id_pessoa) ORDER BY p.nome""",
    "residentes": """SELECT r.id_pessoa AS id, p.nome, pf.crm, pf.especialidade, r.ano_residencia
                     FROM RESIDENTE r JOIN PROFISSIONAL pf USING (id_pessoa)
                     JOIN PESSOA p USING (id_pessoa) ORDER BY p.nome""",
    "preceptores": """SELECT pr.id_pessoa AS id, p.nome, pf.crm, pf.especialidade, pr.titulacao
                      FROM PRECEPTOR pr JOIN PROFISSIONAL pf USING (id_pessoa)
                      JOIN PESSOA p USING (id_pessoa) ORDER BY p.nome""",
    "unidades": "SELECT id_unidade AS id, nome, tipo, capacidade_leitos FROM UNIDADE ORDER BY nome",
    "procedimentos": """SELECT id_procedimento AS id, codigo, nome, tempo_medio_minutos, nivel_risco
                        FROM PROCEDIMENTO ORDER BY nome""",
    "atendimentos": """SELECT a.id_atendimento AS id, a.data_hora, a.duracao_minutos, p.nome AS paciente
                       FROM ATENDIMENTO a JOIN PESSOA p ON p.id_pessoa = a.id_paciente
                       ORDER BY a.data_hora DESC""",
    "escalas": """SELECT e.id_escala AS id, u.nome AS unidade, e.dia_semana, e.turno, p.nome AS residente
                  FROM ESCALA e JOIN UNIDADE u USING (id_unidade)
                  JOIN PESSOA p ON p.id_pessoa = e.id_residente
                  ORDER BY u.nome, e.dia_semana""",
}


def listar(entidade: str):
    """Mostra os UUIDs necessários para os demais comandos."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(LISTAGENS[entidade])
        rows = cur.fetchall()
        for r in rows:
            print(" | ".join(f"{k}={v}" for k, v in r.items()))
        if not rows:
            print(f"Nenhum registro em {entidade}.")
        return rows
    finally:
        cur.close()
        conn.close()


def _main():
    import argparse

    parser = argparse.ArgumentParser(description="CLI Etapa 1 - Hospital")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("ranking-residentes")
    sub.add_parser("tempo-medio-residente")
    sub.add_parser("plantoes-mes")
    sub.add_parser("pacientes-sem-risco-alto")

    p_pac = sub.add_parser("atendimentos-paciente")
    p_pac.add_argument("id_paciente")

    p_at = sub.add_parser("procedimentos-atendimento")
    p_at.add_argument("id_atendimento")

    p_prec = sub.add_parser("preceptores-mes")
    p_prec.add_argument("ano", type=int)
    p_prec.add_argument("mes", type=int)

    p_rm = sub.add_parser("remover-procedimento")
    p_rm.add_argument("id_atendimento")
    p_rm.add_argument("id_procedimento")

    p_upd = sub.add_parser("atualizar-paciente")
    p_upd.add_argument("id_paciente")
    p_upd.add_argument("--convenio")
    p_upd.add_argument("--alergias")

    p_ins = sub.add_parser("inserir-atendimento")
    p_ins.add_argument("data_hora")
    p_ins.add_argument("duracao", type=int)
    p_ins.add_argument("id_paciente")
    p_ins.add_argument("id_residente")
    p_ins.add_argument("id_preceptor")

    p_lis = sub.add_parser("listar", help="lista registros e seus UUIDs")
    p_lis.add_argument("entidade", choices=sorted(LISTAGENS))

    p_cpac = sub.add_parser("cadastrar-paciente")
    p_cpac.add_argument("nome")
    p_cpac.add_argument("cpf", help="11 digitos, sem pontuacao")
    p_cpac.add_argument("data_nascimento", help="AAAA-MM-DD")
    p_cpac.add_argument("--telefone")
    p_cpac.add_argument("--convenio")
    p_cpac.add_argument("--alergias")
    p_cpac.add_argument("--sangue", help="A+, O-, AB+ ...")

    p_cprof = sub.add_parser("cadastrar-profissional")
    p_cprof.add_argument("papel", choices=["residente", "preceptor"])
    p_cprof.add_argument("nome")
    p_cprof.add_argument("cpf")
    p_cprof.add_argument("data_nascimento", help="AAAA-MM-DD")
    p_cprof.add_argument("crm")
    p_cprof.add_argument("data_admissao", help="AAAA-MM-DD")
    p_cprof.add_argument("especialidade")
    p_cprof.add_argument("--ano-residencia", choices=["R1", "R2", "R3"], help="obrigatorio p/ residente")
    p_cprof.add_argument("--titulacao", help="obrigatorio p/ preceptor")
    p_cprof.add_argument("--telefone")

    p_cuni = sub.add_parser("cadastrar-unidade")
    p_cuni.add_argument("nome")
    p_cuni.add_argument("tipo", choices=["Enfermaria", "UTI", "Pronto-Socorro", "Ambulatorio"])
    p_cuni.add_argument("capacidade_leitos", type=int)

    p_cesc = sub.add_parser("cadastrar-escala")
    p_cesc.add_argument("id_unidade")
    p_cesc.add_argument("dia_semana", choices=["segunda", "terca", "quarta", "quinta",
                                               "sexta", "sabado", "domingo"])
    p_cesc.add_argument("turno", choices=["manha", "tarde", "noite"])
    p_cesc.add_argument("id_residente")
    p_cesc.add_argument("id_preceptor")

    p_reg = sub.add_parser("registrar-procedimento", help="adiciona procedimento a um atendimento")
    p_reg.add_argument("id_atendimento")
    p_reg.add_argument("id_procedimento")
    p_reg.add_argument("quantidade", type=int)
    p_reg.add_argument("tempo_real_minutos", type=int)
    p_reg.add_argument("--obs")

    p_fat = sub.add_parser("faturar", help="emite faturamento de um procedimento realizado")
    p_fat.add_argument("id_atendimento")
    p_fat.add_argument("id_procedimento")
    p_fat.add_argument("valor", type=float)
    p_fat.add_argument("--data-emissao", help="AAAA-MM-DD (padrao: hoje)")

    args = parser.parse_args()

    if args.comando == "ranking-residentes":
        ranking_residentes()
    elif args.comando == "tempo-medio-residente":
        tempo_medio_por_residente()
    elif args.comando == "plantoes-mes":
        plantoes_por_unidade_mes()
    elif args.comando == "pacientes-sem-risco-alto":
        pacientes_sem_procedimento_risco_alto()
    elif args.comando == "atendimentos-paciente":
        listar_atendimentos_paciente(args.id_paciente)
    elif args.comando == "procedimentos-atendimento":
        listar_procedimentos_atendimento(args.id_atendimento)
    elif args.comando == "preceptores-mes":
        preceptores_mais_atendimentos_mes(args.ano, args.mes)
    elif args.comando == "remover-procedimento":
        remover_procedimento_realizado(args.id_atendimento, args.id_procedimento)
    elif args.comando == "atualizar-paciente":
        atualizar_paciente(args.id_paciente, novo_convenio=args.convenio, novas_alergias=args.alergias)
    elif args.comando == "inserir-atendimento":
        inserir_atendimento(args.data_hora, args.duracao, args.id_paciente, args.id_residente, args.id_preceptor)
    elif args.comando == "listar":
        listar(args.entidade)
    elif args.comando == "cadastrar-paciente":
        cadastrar_paciente(args.nome, args.cpf, args.data_nascimento, telefone=args.telefone,
                           num_convenio=args.convenio, alergias=args.alergias,
                           grupo_sanguineo=args.sangue)
    elif args.comando == "cadastrar-profissional":
        cadastrar_profissional(args.papel, args.nome, args.cpf, args.data_nascimento, args.crm,
                               args.data_admissao, args.especialidade,
                               ano_residencia=args.ano_residencia, titulacao=args.titulacao,
                               telefone=args.telefone)
    elif args.comando == "cadastrar-unidade":
        cadastrar_unidade(args.nome, args.tipo, args.capacidade_leitos)
    elif args.comando == "cadastrar-escala":
        cadastrar_escala(args.id_unidade, args.dia_semana, args.turno,
                         args.id_residente, args.id_preceptor)
    elif args.comando == "registrar-procedimento":
        registrar_procedimento(args.id_atendimento, args.id_procedimento, args.quantidade,
                               args.tempo_real_minutos, observacao=args.obs)
    elif args.comando == "faturar":
        faturar_procedimento(args.id_atendimento, args.id_procedimento, args.valor,
                             data_emissao=args.data_emissao)


if __name__ == "__main__":
    _main()
