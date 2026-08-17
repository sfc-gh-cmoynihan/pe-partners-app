import os
import threading
import snowflake.connector

_local = threading.local()

SPCS_TOKEN_PATH = "/snowflake/session/token"


def _read_spcs_token():
    try:
        with open(SPCS_TOKEN_PATH, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def get_conn():
    conn = getattr(_local, "conn", None)
    if conn:
        try:
            conn.cursor().execute("SELECT 1")
            return conn
        except Exception:
            conn = None

    account = os.getenv("SNOWFLAKE_ACCOUNT", "SFSEEUROPE-COLM_USWEST")
    host = os.getenv("SNOWFLAKE_HOST")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

    # Try SPCS OAuth token first (internal routing, bypasses network policies)
    spcs_token = _read_spcs_token()
    if spcs_token:
        print(f"[DB] Connecting via SPCS OAuth token (thread={threading.get_ident()})", flush=True)
        conn = snowflake.connector.connect(
            account=account,
            host=host,
            authenticator="oauth",
            token=spcs_token,
            warehouse=warehouse,
            database="PEPARTNERS_DB",
            schema="CORE",
            client_session_keep_alive=True,
        )
    else:
        # Fallback to password auth (local dev)
        pat = os.getenv("SF_PAT", "")
        user = os.getenv("SF_USER", "PE_SERVICE_USER")
        print(f"[DB] Connecting via password (thread={threading.get_ident()}): user={user}", flush=True)
        connect_params = dict(
            user=user,
            password=pat,
            account=account,
            warehouse=warehouse,
            database="PEPARTNERS_DB",
            schema="CORE",
            client_session_keep_alive=True,
        )
        if host:
            connect_params["host"] = host
        conn = snowflake.connector.connect(**connect_params)

    _local.conn = conn
    print(f"[DB] Connected successfully (thread={threading.get_ident()})", flush=True)
    return conn


def query(sql, warehouse=None):
    conn = get_conn()
    cur = conn.cursor()
    if warehouse:
        cur.execute(f"USE WAREHOUSE {warehouse}")
    cur.execute(sql)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    if warehouse:
        cur.execute(f"USE WAREHOUSE {os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')}")
    return [dict(zip(cols, row)) for row in rows]
