import os

import psycopg2
import psycopg2.extras
from flask import jsonify

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "dbname=hospital_db user=postgres password=password host=localhost port=5433",
)

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def query(sql, params=None, one=False):
    """Executa um SELECT e devolve lista de dicts (ou um dict se one=True)."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            rows = [dict(r) for r in rows]
            return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()

def execute(sql, params=None, returning=False):
    """Executa um INSERT/UPDATE/DELETE. Se returning=True, devolve a linha retornada."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            result = dict(cur.fetchone()) if returning and cur.description else None
            conn.commit()
            return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def api_error(message, status=400):
    return jsonify({"erro": message}), status
