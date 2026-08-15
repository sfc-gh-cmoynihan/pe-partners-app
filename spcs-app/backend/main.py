import os
import json
import re
import tempfile
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse, Response
from backend.db import get_conn, query
from backend import report as report_module

app = FastAPI(title="PE Partners API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/customers")
def list_customers():
    return query("SELECT * FROM CUSTOMERS_IT ORDER BY AUM_COMMITMENT_GBP DESC")


@app.get("/api/funds")
def list_funds():
    return query("SELECT * FROM FUNDS_IT ORDER BY TOTAL_AUM_GBP DESC")


@app.get("/api/investments")
def list_investments():
    return query("SELECT * FROM INVESTMENTS_IT ORDER BY MARKET_VALUE_GBP DESC")


@app.get("/api/performance")
def list_performance():
    return query("""
        SELECT fp.*, f.FUND_NAME
        FROM FUND_PERFORMANCE_IT fp
        JOIN FUNDS_IT f ON fp.FUND_ID = f.FUND_ID
        ORDER BY fp.REPORTING_DATE DESC
    """)


@app.post("/api/search")
async def search_filings(request: Request):
    body = await request.json()
    search_query = body.get("query", "")
    if not search_query:
        return JSONResponse({"error": "No query"}, status_code=400)
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("USE WAREHOUSE COMPUTE_WH")
        cur.execute("USE WAREHOUSE COMPUTE_WH")
        params = json.dumps({
            "query": search_query,
            "columns": ["FILING_ID", "COMPANY_NAME", "TICKER", "FORM_TYPE", "FILING_CATEGORY", "FILING_DATE", "CHUNK_TEXT"],
            "limit": 8,
        })
        cur.execute("SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW('PEPARTNERS_DB.CORE.COMPANY_FILINGS_SEARCH_SERVICE', %s)", (params,))
        row = cur.fetchone()
        items = []
        if row and row[0]:
            results = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            items = results.get("results", [])
        return {"results": items}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/filings/companies")
def list_filing_companies():
    return query("""
        SELECT DISTINCT COMPANY_NAME, TICKER
        FROM COMPANY_FILINGS
        ORDER BY COMPANY_NAME
    """, warehouse='COMPUTE_WH')


@app.get("/api/filings")
def list_filings(ticker: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("USE WAREHOUSE COMPUTE_WH")
    cur.execute(
        "SELECT FILING_ID, COMPANY_NAME, TICKER, FORM_TYPE, FILING_CATEGORY, FILING_DATE, SOURCE_URL "
        "FROM COMPANY_FILINGS WHERE TICKER = %s ORDER BY FILING_CATEGORY",
        (ticker,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _get_filing_text(filing_id, max_chars=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("USE WAREHOUSE COMPUTE_WH")
    cur.execute(
        "SELECT COMPANY_NAME, TICKER, FORM_TYPE, FILING_CATEGORY, FILING_DATE, FULL_TEXT "
        "FROM COMPANY_FILINGS_TEXT WHERE FILING_ID = %s",
        (filing_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    company_name, ticker, form_type, filing_category, filing_date, full_text = row
    full_text = full_text or ""
    truncated = False
    if max_chars and len(full_text) > max_chars:
        full_text = full_text[:max_chars]
        truncated = True
    return {
        "company_name": company_name,
        "ticker": ticker,
        "form_type": form_type,
        "filing_category": filing_category,
        "filing_date": str(filing_date),
        "text": full_text,
        "truncated": truncated,
    }


@app.get("/api/filings/{filing_id}/text")
def get_filing_text(filing_id: str):
    result = _get_filing_text(filing_id, max_chars=100000)
    if not result:
        return JSONResponse({"error": "Filing not found"}, status_code=404)
    return result


@app.get("/api/filings/{filing_id}/analysis")
def get_filing_analysis(filing_id: str):
    """Returns precomputed summary + sentiment for a filing (generated ahead of time via a backfill job)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT SUMMARY, SENTIMENT_JSON FROM COMPANY_FILINGS_ANALYSIS WHERE FILING_ID = %s",
        (filing_id,),
    )
    row = cur.fetchone()
    if not row:
        return JSONResponse({"error": "No precomputed analysis for this filing"}, status_code=404)
    summary, sentiment_json = row
    sentiment = json.loads(sentiment_json) if isinstance(sentiment_json, str) else sentiment_json
    return {"summary": summary, "sentiment": sentiment}


@app.post("/api/search/calls")
async def search_calls(request: Request):
    body = await request.json()
    search_query = body.get("query", "")
    if not search_query:
        return JSONResponse({"error": "No query"}, status_code=400)
    try:
        conn = get_conn()
        cur = conn.cursor()
        params = json.dumps({
            "query": search_query,
            "columns": ["CHUNK_TEXT", "DOCUMENT_TITLE", "SOURCE_TYPE", "SUMMARY", "SENTIMENT"],
            "limit": 8,
        })
        cur.execute("SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW('TRISTAN_DB.APP.TRISTAN_SEARCH', %s)", (params,))
        row = cur.fetchone()
        items = []
        if row and row[0]:
            results = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            items = results.get("results", [])
        return {"results": items}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/calls/companies")
def list_call_companies():
    rows = query("""
        SELECT COMPANY_NAME, TICKER, COUNT(*) AS CALL_COUNT
        FROM COMPANY_CALLS
        GROUP BY COMPANY_NAME, TICKER
        ORDER BY COMPANY_NAME
    """, warehouse='COMPUTE_WH')
    return rows


@app.get("/api/calls/by-company")
def list_calls_for_company(company: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("USE WAREHOUSE COMPUTE_WH")
    cur.execute("""
        SELECT CALL_ID, COMPANY_NAME, TICKER, CALL_TITLE, CALL_DATE, PARTICIPANTS, SENTIMENT, SENTIMENT_SCORE
        FROM COMPANY_CALLS
        WHERE COMPANY_NAME = %s
        ORDER BY CALL_DATE DESC
    """, (company,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@app.get("/api/calls/{call_id}")
def get_call_detail(call_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("USE WAREHOUSE COMPUTE_WH")
    cur.execute("SELECT * FROM COMPANY_CALLS WHERE CALL_ID = %s", (call_id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    if not row:
        return JSONResponse({"error": "Call not found"}, status_code=404)
    return dict(zip(cols, row))


@app.get("/api/calls/{call_id}/video")
def get_call_video(call_id: str):
    cache_path = os.path.join(tempfile.gettempdir(), f"lp_call_{call_id}.mp4")
    video_headers = {"Cache-Control": "public, max-age=86400"}
    if os.path.exists(cache_path):
        return FileResponse(cache_path, media_type="video/mp4", filename=f"{call_id}.mp4", headers=video_headers)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("USE WAREHOUSE COMPUTE_WH")
    cur.execute("SELECT VIDEO_FILENAME FROM COMPANY_CALLS WHERE CALL_ID = %s", (call_id,))
    row = cur.fetchone()
    if not row:
        return JSONResponse({"error": "Call not found"}, status_code=404)
    filename = row[0]
    with tempfile.TemporaryDirectory() as tmp_dir:
        cur.execute(
            f"GET @PEPARTNERS_DB.CORE.CALL_RECORDINGS_STAGE/{filename} file://{tmp_dir}/"
        )
        local_path = os.path.join(tmp_dir, filename)
        if not os.path.exists(local_path):
            return JSONResponse({"error": "Video not found in stage"}, status_code=404)
        with open(local_path, "rb") as f:
            data = f.read()
    with open(cache_path, "wb") as f:
        f.write(data)
    return FileResponse(cache_path, media_type="video/mp4", filename=filename, headers=video_headers)


@app.get("/api/models")
def list_models():
    return [
        "openai-gpt-5.2",
        "openai-gpt-5.4-mini",
        "openai-o3",
        "openai-o4-mini",
    ]


@app.post("/api/agent")
async def agent_chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    model = body.get("model", "openai-gpt-5.2")
    user_msg = messages[-1].get("content", "") if messages else ""
    if not user_msg:
        return JSONResponse({"error": "No message"}, status_code=400)
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("USE WAREHOUSE COMPUTE_WH")

        # Fetch live data context
        context_parts = []
        try:
            cur.execute("SELECT FUND_ID, FUND_NAME, STRATEGY, TOTAL_AUM_GBP, MANAGEMENT_FEE_PCT, PERFORMANCE_FEE_PCT FROM FUNDS_IT")
            funds = cur.fetchall()
            cols = [d[0] for d in cur.description]
            fund_rows = [dict(zip(cols, r)) for r in funds]
            total_aum = sum(f['TOTAL_AUM_GBP'] or 0 for f in fund_rows)
            context_parts.append(f"FUNDS (Total AUM: GBP {total_aum:,.0f}):\n" + "\n".join([f"- {f['FUND_NAME']}: AUM GBP {f['TOTAL_AUM_GBP']:,.0f}, Strategy: {f['STRATEGY']}, Mgmt Fee: {f['MANAGEMENT_FEE_PCT']}%, Perf Fee: {f['PERFORMANCE_FEE_PCT']}%" for f in fund_rows]))
        except Exception:
            pass

        try:
            cur.execute("SELECT SECURITY_NAME, TICKER, SECTOR, POSITION_TYPE, MARKET_VALUE_GBP, WEIGHT_PCT, GEOGRAPHY FROM INVESTMENTS_IT ORDER BY MARKET_VALUE_GBP DESC")
            invs = cur.fetchall()
            cols = [d[0] for d in cur.description]
            inv_rows = [dict(zip(cols, r)) for r in invs]
            context_parts.append("POSITIONS:\n" + "\n".join([f"- {i['SECURITY_NAME']} ({i['TICKER']}): {i['POSITION_TYPE']}, Sector: {i['SECTOR']}, Value: GBP {i['MARKET_VALUE_GBP']:,.0f}, Weight: {i['WEIGHT_PCT']}%, Geo: {i['GEOGRAPHY']}" for i in inv_rows]))
        except Exception:
            pass

        try:
            cur.execute("SELECT f.FUND_NAME, fp.REPORTING_DATE, fp.MONTHLY_RETURN_PCT, fp.YTD_RETURN_PCT, fp.SHARPE_RATIO, fp.MAX_DRAWDOWN_PCT, fp.VOLATILITY_PCT FROM FUND_PERFORMANCE_IT fp JOIN FUNDS_IT f ON fp.FUND_ID = f.FUND_ID ORDER BY fp.REPORTING_DATE DESC LIMIT 10")
            perfs = cur.fetchall()
            cols = [d[0] for d in cur.description]
            perf_rows = [dict(zip(cols, r)) for r in perfs]
            context_parts.append("PERFORMANCE (latest):\n" + "\n".join([f"- {p['FUND_NAME']} ({p['REPORTING_DATE']}): Monthly {p['MONTHLY_RETURN_PCT']}%, YTD {p['YTD_RETURN_PCT']}%, Sharpe {p['SHARPE_RATIO']}, MaxDD {p['MAX_DRAWDOWN_PCT']}%, Vol {p['VOLATILITY_PCT']}%" for p in perf_rows]))
        except Exception:
            pass

        try:
            cur.execute("SELECT FULL_NAME, COMPANY_NAME, INVESTOR_TYPE, REGION, AUM_COMMITMENT_GBP FROM CUSTOMERS_IT ORDER BY AUM_COMMITMENT_GBP DESC")
            custs = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cust_rows = [dict(zip(cols, r)) for r in custs]
            context_parts.append("INVESTORS:\n" + "\n".join([f"- {c['FULL_NAME']} ({c['COMPANY_NAME']}): {c['INVESTOR_TYPE']}, Region: {c['REGION']}, Commitment: GBP {c['AUM_COMMITMENT_GBP']:,.0f}" for c in cust_rows]))
        except Exception:
            pass

        data_context = "\n\n".join(context_parts)
        system_prompt = f"You are the PE Partners Investment Intelligence Assistant. Answer using ONLY the data below. Be concise with exact numbers.\n\n{data_context}"

        cur.execute("""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                %s,
                ARRAY_CONSTRUCT(
                    OBJECT_CONSTRUCT('role', 'system', 'content', %s),
                    OBJECT_CONSTRUCT('role', 'user', 'content', %s)
                ),
                OBJECT_CONSTRUCT('temperature', 0.3, 'max_tokens', 1024)
            ):choices[0]:messages::VARCHAR
        """, (model, system_prompt, user_msg))
        row = cur.fetchone()
        if row and row[0]:
            return {"response": str(row[0]).strip()}
        return JSONResponse({"error": "No response"}, status_code=502)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/reports/pdf")
def download_report_pdf(fund_id: str = None):
    try:
        pdf_bytes = report_module.generate_pdf(fund_id)
        filename = f"PE_Report_{fund_id or 'AllFunds'}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/reports/email")
async def email_report(request: Request):
    body = await request.json()
    fund_id = body.get("fund_id")
    recipient = body.get("recipient", "").strip()
    if not fund_id:
        return JSONResponse({"error": "fund_id is required"}, status_code=400)
    if not recipient:
        return JSONResponse({"error": "recipient email is required"}, status_code=400)
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "CALL PEPARTNERS_DB.CORE.SEND_LP_REPORT_EMAIL(%s, %s)",
            (int(fund_id), recipient),
        )
        return {"status": "sent"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def _build_cron(frequency, day_of_week, day_of_month, hour, minute):
    hour = int(hour)
    minute = int(minute)
    if frequency == "DAILY":
        return f"{minute} {hour} * * *"
    if frequency == "WEEKLY":
        return f"{minute} {hour} * * {int(day_of_week)}"
    if frequency == "MONTHLY":
        return f"{minute} {hour} {int(day_of_month)} * *"
    raise ValueError(f"Unsupported frequency: {frequency}")


@app.post("/api/reports/schedule")
async def create_report_schedule(request: Request):
    body = await request.json()
    fund_id = body.get("fund_id")
    fund_name = body.get("fund_name", "All Funds")
    recipient = body.get("recipient", "").strip()
    frequency = body.get("frequency", "MONTHLY")
    day_of_week = body.get("day_of_week", 1)
    day_of_month = body.get("day_of_month", 1)
    hour = body.get("hour", 8)
    minute = body.get("minute", 0)

    if not fund_id:
        return JSONResponse({"error": "fund_id is required"}, status_code=400)
    if not recipient:
        return JSONResponse({"error": "recipient email is required"}, status_code=400)
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", recipient):
        return JSONResponse({"error": "Invalid recipient email address"}, status_code=400)

    try:
        cron_expr = _build_cron(frequency, day_of_week, day_of_month, hour, minute)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("USE WAREHOUSE COMPUTE_WH")
        cur.execute(
            """
            INSERT INTO PEPARTNERS_DB.CORE.PE_REPORT_SCHEDULES
                (FUND_ID, FUND_NAME, RECIPIENT_EMAIL, FREQUENCY, CRON_EXPR, TASK_NAME, CREATED_BY)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (int(fund_id), fund_name, recipient, frequency, cron_expr, "PENDING", "LP_APP"),
        )
        cur.execute(
            "SELECT SCHEDULE_ID FROM PEPARTNERS_DB.CORE.PE_REPORT_SCHEDULES ORDER BY SCHEDULE_ID DESC LIMIT 1"
        )
        schedule_id = cur.fetchone()[0]
        task_name = f"LP_REPORT_TASK_{schedule_id}"

        cur.execute(f"""
            CREATE OR REPLACE TASK PEPARTNERS_DB.CORE.{task_name}
                WAREHOUSE = COMPUTE_WH
                SCHEDULE = 'USING CRON {cron_expr} Europe/London'
            AS
                CALL PEPARTNERS_DB.CORE.SEND_LP_REPORT_EMAIL({int(fund_id)}, '{recipient}')
        """)
        cur.execute(f"ALTER TASK PEPARTNERS_DB.CORE.{task_name} RESUME")
        cur.execute(
            "UPDATE PEPARTNERS_DB.CORE.PE_REPORT_SCHEDULES SET TASK_NAME = %s WHERE SCHEDULE_ID = %s",
            (task_name, schedule_id),
        )
        return {"schedule_id": schedule_id, "task_name": task_name, "cron_expr": cron_expr}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/reports/schedules")
def list_report_schedules():
    return query("""
        SELECT * FROM PEPARTNERS_DB.CORE.PE_REPORT_SCHEDULES
        WHERE ACTIVE = TRUE
        ORDER BY CREATED_AT DESC
    """, warehouse='COMPUTE_WH')


@app.delete("/api/reports/schedule/{schedule_id}")
def delete_report_schedule(schedule_id: int):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT TASK_NAME FROM PEPARTNERS_DB.CORE.PE_REPORT_SCHEDULES WHERE SCHEDULE_ID = %s",
            (schedule_id,),
        )
        row = cur.fetchone()
        if not row:
            return JSONResponse({"error": "Schedule not found"}, status_code=404)
        task_name = row[0]
        try:
            cur.execute(f"ALTER TASK PEPARTNERS_DB.CORE.{task_name} SUSPEND")
        except Exception:
            pass
        cur.execute(f"DROP TASK IF EXISTS PEPARTNERS_DB.CORE.{task_name}")
        cur.execute(
            "UPDATE PEPARTNERS_DB.CORE.PE_REPORT_SCHEDULES SET ACTIVE = FALSE WHERE SCHEDULE_ID = %s",
            (schedule_id,),
        )
        return {"status": "deleted"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/user/role")
def get_user_role(request: Request):
    sf_user = request.headers.get("Sf-Context-Current-User", "")
    if sf_user:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(f'DESCRIBE USER "{sf_user}"')
            rows = cur.fetchall()
            props = {r[0]: r[1] for r in rows}
            first = props.get("FIRST_NAME", "")
            last = props.get("LAST_NAME", "")
            display = f"{first} {last}".strip() if (first or last) else sf_user
            return {"user": display}
        except Exception:
            return {"user": sf_user}
    return {"user": "Unknown"}


@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(
        url="/logged-out.html",
        status_code=302,
    )
    for cookie in request.cookies:
        response.delete_cookie(cookie)
    return response
