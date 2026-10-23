import mysql.connector
from mysql.connector import Error
from config import Config

def get_db_connection():
    """Returns a new connection to the MySQL database."""
    print("--> CONNECTING TO DB:", Config.DB_NAME)  # <--- Add this print statement here
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False
    )

def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """Executes parameterized queries safely preventing SQL injection."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    result = None
    try:
        cursor.execute(query, params or ())
        if commit:
            conn.commit()
            result = cursor.lastrowid
        elif fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
    return result
