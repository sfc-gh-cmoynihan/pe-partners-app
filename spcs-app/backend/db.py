import os
import threading
import snowflake.connector

# Thread-local connections: each worker thread in FastAPI's threadpool gets
# its own Snowflake connection, so concurrent requests no longer serialize on
# a single shared connection/cursor.
_local = threading.local()


def get_conn():
    conn = getattr(_local, "conn", None)
    if conn:
        try:
            conn.cursor().execute("SELECT 1")
            return conn
        except Exception:
            conn = None

    pat = os.getenv("SF_PAT", "")
    account = os.getenv("SNOWFLAKE_ACCOUNT", "SFSEEUROPE-COLM_USWEST")
    host = os.getenv("SNOWFLAKE_HOST", "")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "PE_INTERACTIVE_WH")
    user = os.getenv("SF_USER", "PE_SERVICE_USER")

    print(f"[DB] Connecting (thread={threading.get_ident()}): user={user}, host={host}, account={account}, wh={warehouse}, pat_len={len(pat)}", flush=True)

    conn = snowflake.connector.connect(
        user=user,
        password=pat,
        account=account,
        host=host,
        warehouse=warehouse,
        database="PEPARTNERS_DB",
        schema="CORE",
        client_session_keep_alive=True,
    )
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
        cur.execute(f"USE WAREHOUSE {os.getenv('SNOWFLAKE_WAREHOUSE', 'PE_INTERACTIVE_WH')}")
    return [dict(zip(cols, row)) for row in rows]
