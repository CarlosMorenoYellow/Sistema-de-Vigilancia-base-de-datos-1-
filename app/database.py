import psycopg
from psycopg.rows import dict_row

# Cadena de conexión hacia el contenedor Docker de PostgreSQL
DATABASE_URL = "postgresql://usuario:password123@localhost:5432/vision_db"

def get_db_connection():
    """
    Generador de conexión a PostgreSQL para inyección de dependencias en FastAPI.
    - dict_row permite mapear automáticamente cada tupla SQL a un diccionario llave-valor.
    """
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()