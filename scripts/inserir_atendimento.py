import psycopg2
from datetime import datetime

# Conexão (ajuste conforme seu .env depois)
conn = psycopg2.connect(
    host="localhost",
    database="hospital_db",
    user="postgres",
    password="password"
)
cur = conn.cursor()

def inserir_atendimento(data_hora, duracao, id_paciente, id_residente, id_preceptor):
    try:
        # Verificar se paciente, residente e preceptor existem
        cur.execute("SELECT 1 FROM paciente WHERE id_pessoa = %s", (id_paciente,))
        if not cur.fetchone():
            print("Erro: Paciente não encontrado.")
            return

        cur.execute("SELECT 1 FROM residente WHERE id_profissional = %s", (id_residente,))
        if not cur.fetchone():
            print("Erro: Residente não encontrado.")
            return

        cur.execute("SELECT 1 FROM preceptor WHERE id_profissional = %s", (id_preceptor,))
        if not cur.fetchone():
            print("Erro: Preceptor não encontrado.")
            return

        # Inserir atendimento
        cur.execute("""
            INSERT INTO atendimento (data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_atendimento
        """, (data_hora, duracao, id_paciente, id_residente, id_preceptor))

        id_atendimento = cur.fetchone()[0]
        conn.commit()
        print(f"Atendimento criado com sucesso! ID: {id_atendimento}")
        return id_atendimento

    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir atendimento: {e}")

# Exemplo de uso
inserir_atendimento(
    data_hora=datetime(2025, 6, 14, 10, 0),
    duracao=35,
    id_paciente=1,
    id_residente=101,
    id_preceptor=201
)

cur.close()
conn.close()
