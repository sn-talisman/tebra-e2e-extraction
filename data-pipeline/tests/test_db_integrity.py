import sys
import os
import pytest
import psycopg2

# Paths
pipeline_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
loading_dir = os.path.join(pipeline_root, 'loading')
sys.path.append(loading_dir)

try:
    from load_to_postgres import DB_CONFIG
except ImportError:
    # Fallback config if import fails (should be caught by pipeline test)
    DB_CONFIG = {
        "dbname": "tebra_dw",
        "user": "tebra_user",
        "password": "tebra_password",
        "host": "localhost",
        "port": "5432"
    }

@pytest.fixture(scope="module")
def db_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")
    finally:
        if conn:
            conn.close()

def test_practices_exist(db_connection):
    cur = db_connection.cursor()
    cur.execute("SELECT count(*) FROM tebra.cmn_practice")
    count = cur.fetchone()[0]
    assert count > 0, "No practices found in DB"
    cur.close()

def test_claims_exist(db_connection):
    cur = db_connection.cursor()
    cur.execute("SELECT count(*) FROM tebra.fin_claim_line")
    count = cur.fetchone()[0]
    assert count > 0, "No claims found in DB"
    cur.close()

def test_integrity_encounters(db_connection):
    # Check FK linkage
    cur = db_connection.cursor()
    # Simple check: do we have encounters linked to practices?
    cur.execute("SELECT count(*) FROM tebra.clin_encounter WHERE practice_guid IS NOT NULL")
    count = cur.fetchone()[0]
    assert count > 0, "Encounters missing practice linkage"
    cur.close()
