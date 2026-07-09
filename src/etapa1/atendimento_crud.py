
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database="hospital_db",
        user="postgres",
        password="password",
    )



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
                pr.quantidade,
                pr.tempo_real_minutos,
                pr.observacao,
                pr.faturado
            FROM PROCEDIMENTO_REALIZADO pr
            JOIN PROCEDIMENTO proc ON pr.id_procedimento = proc.id_procedimento
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
            DELETE FROM PROCEDIMENTO_REALIZADO
            WHERE id_atendimento  = %s
              AND id_procedimento = %s
              AND faturado = FALSE
        """, (id_atendimento, id_procedimento))
        conn.commit()

        if cur.rowcount == 0:
            print("Remoção bloqueada: o procedimento já foi faturado ou não existe.")
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
            FROM ATENDIMENTO a
            JOIN RESIDENTE    res ON a.id_residente = res.id_pessoa
            JOIN PROFISSIONAL pf  ON res.id_pessoa  = pf.id_pessoa
            JOIN PESSOA       p   ON pf.id_pessoa   = p.id_pessoa
            GROUP BY p.nome
            ORDER BY tempo_medio_minutos DESC
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
            FROM ATENDIMENTO a
            JOIN RESIDENTE    res ON a.id_residente = res.id_pessoa
            JOIN PROFISSIONAL pf  ON res.id_pessoa  = pf.id_pessoa
            JOIN PESSOA       p   ON pf.id_pessoa   = p.id_pessoa
            GROUP BY p.nome
            ORDER BY total_atendimentos DESC
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


if __name__ == "__main__":
    print("\n=== Tempo médio por residente ===")
    tempo_medio_por_residente()

    print("\n=== Ranking de residentes ===")
    ranking_residentes()

    print("\n=== Atendimentos do paciente Arthur ===")
    listar_atendimentos_paciente("a1111111-1111-1111-1111-111111111111")

    print("\n=== Procedimentos do atendimento e1111111 ===")
    listar_procedimentos_atendimento("e1111111-1111-1111-1111-111111111111")

    print("\n=== Preceptores com +5 atendimentos em jun/2025 ===")
    preceptores_mais_atendimentos_mes(2025, 6)
