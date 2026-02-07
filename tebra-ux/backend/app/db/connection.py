import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

# Database configuration - matches existing tebra-e2e-extraction DB
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "tebra_dw"),
    "user": os.getenv("DB_USER", "tebra_user"),
    "password": os.getenv("DB_PASSWORD", "tebra_password"),
}

# Connection pool - initialized lazily
connection_pool = None

def get_pool():
    """Get or create connection pool"""
    global connection_pool
    if connection_pool is None:
        connection_pool = SimpleConnectionPool(1, 10, **DB_CONFIG)
    return connection_pool

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

@contextmanager
def get_db_cursor():
    """Get database cursor for queries"""
    pool = get_pool()
    conn = pool.getconn()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        pool.putconn(conn)
