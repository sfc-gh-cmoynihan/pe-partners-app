# PE Partners — Installation Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Snowpark Container Services (SPCS)                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  PE_APP (single container)                                │  │
│  │  ┌──────────────┐    ┌─────────────────────────────────┐ │  │
│  │  │  Nginx :8080 │───▶│  FastAPI (uvicorn :8000)        │ │  │
│  │  │  Static SPA  │    │  /api/* routes                  │ │  │
│  │  └──────────────┘    │  Snowflake connector (OAuth)    │ │  │
│  │                      └─────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│              ┌───────────────┼───────────────┐                   │
│              ▼               ▼               ▼                   │
│    Interactive Tables   Cortex Search   Cortex Complete (LLMs)   │
│    (FUNDS_IT, etc.)     (Filings)      (Agent chat)             │
└─────────────────────────────────────────────────────────────────┘
```

- **Frontend:** AngularJS 1.x static SPA served by Nginx
- **Backend:** Python FastAPI with Snowflake connector
- **Auth:** SPCS OAuth (auto-injected token) — no credentials in container
- **Orchestration:** Supervisord manages Nginx + Uvicorn in one container

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Snowflake account | Any region | ACCOUNTADMIN role required |
| Docker Desktop | 20.10+ | Must support `--platform linux/amd64` |
| Snowflake CLI | Latest | `pip install snowflake-cli-labs` |
| Python | 3.10+ | For local development only |
| Git | Any | To clone the repository |

### Snowflake CLI Connection

Configure a connection in `~/.snowflake/connections.toml`:

```toml
[pepartners]
account = "YOUR_ACCOUNT"
user = "YOUR_USER"
authenticator = "externalbrowser"   # or SNOWFLAKE_JWT for CI
warehouse = "COMPUTE_WH"
role = "ACCOUNTADMIN"
```

Verify with:

```bash
snow connection test -c pepartners
```

---

## Step 1: Create Snowflake Objects

Run the DDL script to create the database, schema, warehouse, compute pool, network rules, image repository, and all tables:

```bash
snow sql -c pepartners -f setup/01_ddl.sql
```

**What this creates:**

| Object | Name |
|--------|------|
| Database | `PEPARTNERS_DB` |
| Schema | `PEPARTNERS_DB.CORE` |
| Warehouse | `COMPUTE_WH` (XS, auto-suspend 60s) |
| Image Repo | `PEPARTNERS_DB.CORE.PE_REPO` |
| Compute Pool | `PE_APP_POOL` (1x CPU_X64_XS, auto-suspend 3600s) |
| Network Rule | `PE_SNOWFLAKE_RULE` (egress 0.0.0.0:443/80) |
| EAI | `PE_SNOWFLAKE_EAI` |
| Staging Tables | `FUNDS_STG`, `CUSTOMERS_STG`, `INVESTMENTS_STG`, `FUND_PERFORMANCE_STG` |
| Interactive Tables | `FUNDS_IT`, `CUSTOMERS_IT`, `INVESTMENTS_IT`, `FUND_PERFORMANCE_IT` |
| Document Tables | `COMPANY_FILINGS`, `COMPANY_FILINGS_CHUNKS`, `COMPANY_FILINGS_TEXT`, `COMPANY_FILINGS_ANALYSIS` |
| Call Table | `COMPANY_CALLS` |
| Schedule Table | `PE_REPORT_SCHEDULES` |

---

## Step 2: Load Sample Data

Populate all tables with realistic PE fund data:

```bash
snow sql -c pepartners -f setup/02_data.sql
```

This inserts:
- 4 funds (AI Growth, AI Infrastructure, AI Frontier, AI Applications)
- 9 LP investors (institutional — Vanguard, Morgan Stanley, etc.)
- 36 portfolio positions (AI companies)
- 12 monthly performance records (3 months x 4 funds)
- Earnings call metadata
- Report schedules

---

## Step 3: Build the Docker Image

```bash
cd spcs-app

# Login to Snowflake image registry
snow spcs image-registry login -c pepartners

# Build (must target linux/amd64 for SPCS)
docker build --platform linux/amd64 \
  -t sfseeurope-colm-uswest.registry.snowflakecomputing.com/pepartners_db/core/pe_repo/pe-angular:latest .

# Push to registry
docker push sfseeurope-colm-uswest.registry.snowflakecomputing.com/pepartners_db/core/pe_repo/pe-angular:latest
```

> Replace `sfseeurope-colm-uswest` with your account identifier (lowercase, hyphens instead of underscores).

To find your registry URL:

```sql
SHOW IMAGE REPOSITORIES IN SCHEMA PEPARTNERS_DB.CORE;
-- Check the repository_url column
```

---

## Step 4: Deploy the Service

Edit `setup/03_deploy_service.sql` — replace `<YOUR_ACCOUNT>` with your account identifier in the image URL, then run:

```bash
snow sql -c pepartners -f setup/03_deploy_service.sql
```

The service spec:
- 1 instance, 2 CPU / 4 GB RAM (limits)
- Public endpoint on port 8080
- External access integration for outbound HTTPS
- `SNOWFLAKE_WAREHOUSE` env var set to `COMPUTE_WH`

> **Do NOT set** `SNOWFLAKE_ACCOUNT` or `SNOWFLAKE_HOST` in the service spec. SPCS auto-injects these for OAuth to work.

---

## Step 5: Access the App

Wait 1-2 minutes for provisioning, then get the URL:

```sql
SHOW ENDPOINTS IN SERVICE PEPARTNERS_DB.CORE.PE_APP_V3;
```

The `ingress_url` column is your app URL. Open it in a browser — you'll authenticate via Snowflake SSO.

---

## Step 6: Deploy Document Search (Optional)

The Document Intelligence tab requires PDF filings on a Snowflake stage.

### 6a. Prepare PDF Files

Place PDFs in the `documents/` folder using this naming convention:

```
<company>-<ticker>__<form_type>_<YYYY-MM-DD>_<title>.pdf
```

Examples:
```
openai-OAIP__10K_2026-03-15_annual-report.pdf
anthropic-ANTH__8K_2026-06-01_board-update.pdf
nvidia-NVDA__10Q_2026-04-30_quarterly-filing.pdf
```

### 6b. Run the Deploy Script

```bash
SNOW_CONNECTION=pepartners ./documents/deploy_documents_search.sh
```

This will:
1. Create `@PEPARTNERS_DB.CORE.DOCUMENTS_STAGE`
2. Upload all PDFs from `documents/`
3. Parse documents with `SNOWFLAKE.CORTEX.PARSE_DOCUMENT` (OCR)
4. Chunk text (1500 chars, 250 overlap) for vector search
5. Generate AI summaries and sentiment analysis
6. Create `COMPANY_FILINGS_SEARCH_SERVICE` (Cortex Search)

---

## Redeploying After Code Changes

### App code changes (frontend or backend):

```bash
# Rebuild and push
cd spcs-app
docker build --platform linux/amd64 -t <image_url> .
docker push <image_url>
```

```sql
-- SPCS caches image digests; must drop and recreate
DROP SERVICE IF EXISTS PEPARTNERS_DB.CORE.PE_APP_V3;
-- Re-run setup/03_deploy_service.sql
```

### Document-only changes:

No rebuild needed. Just re-run the deploy script:

```bash
SNOW_CONNECTION=pepartners ./documents/deploy_documents_search.sh
```

---

## CI/CD (GitHub Actions)

The repo includes `.github/workflows/build-push.yml` which automatically builds and pushes the image on every push to `main` that touches `spcs-app/`.

### Setup:

1. Add a repository secret `SNOWFLAKE_PRIVATE_KEY` containing your RSA private key (unencrypted `.p8` format)
2. Ensure the Snowflake user has key-pair auth configured
3. Pushes to `main` (or manual dispatch) trigger the workflow

The workflow:
- Installs Snowflake CLI
- Authenticates via JWT (key-pair)
- Builds `linux/amd64` image
- Pushes to `sfseeurope-colm-uswest.registry.snowflakecomputing.com/pepartners_db/core/pe_repo/pe-angular:latest`

> After CI pushes a new image, you still need to recreate the service to pick up the new digest.

---

## Local Development

For testing without deploying to SPCS:

```bash
cd spcs-app/backend

# Create a virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export SNOWFLAKE_ACCOUNT="YOUR_ACCOUNT"
export SF_USER="YOUR_USER"
export SF_PAT="YOUR_PASSWORD_OR_PAT"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"

# Run the backend
uvicorn main:app --reload --port 8000
```

For the frontend, serve the static files:

```bash
cd spcs-app/frontend/src
python -m http.server 8080
```

> Note: In local mode the frontend won't proxy `/api/` to the backend automatically. Use the backend directly at `http://localhost:8000/api/` or configure a local Nginx with the provided `nginx.conf`.

---

## Troubleshooting

### Check service status

```sql
SELECT SYSTEM$GET_SERVICE_STATUS('PEPARTNERS_DB.CORE.PE_APP_V3');
```

### View container logs

```sql
CALL SYSTEM$GET_SERVICE_LOGS('PEPARTNERS_DB.CORE.PE_APP_V3', '0', 'app', 50);
```

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "Client is unauthorized to use Snowpark Container Services OAuth token" | `SNOWFLAKE_ACCOUNT` or `SNOWFLAKE_HOST` set in service spec | Remove those env vars from the spec |
| "Endpoints provisioning in progress" | Service still starting | Wait 1-2 minutes |
| No data in tables | `_STG` tables empty or interactive tables not refreshed | Run `setup/02_data.sql`, then `ALTER DYNAMIC TABLE ... REFRESH` |
| Agent returns errors | Warehouse suspended or model unavailable | Check `COMPUTE_WH` is active; verify model name in Cortex |
| Document search empty | No PDFs uploaded or search service not created | Run the document deploy script |
| Image push fails | Not logged in to registry | Run `snow spcs image-registry login -c pepartners` |
| Compute pool not starting | Quota exceeded or pool suspended | `ALTER COMPUTE POOL PE_APP_POOL RESUME;` |

### Useful Diagnostic Queries

```sql
-- Service status
SELECT SYSTEM$GET_SERVICE_STATUS('PEPARTNERS_DB.CORE.PE_APP_V3');

-- Compute pool status
SHOW COMPUTE POOLS LIKE 'PE_APP_POOL';

-- Verify image exists
SHOW IMAGES IN IMAGE REPOSITORY PEPARTNERS_DB.CORE.PE_REPO;

-- Check interactive table refresh
SHOW DYNAMIC TABLES LIKE '%_IT' IN SCHEMA PEPARTNERS_DB.CORE;

-- Verify Cortex Search service
SHOW CORTEX SEARCH SERVICES IN SCHEMA PEPARTNERS_DB.CORE;
```

---

## Version History

| Version | Notes |
|---------|-------|
| v4.2 | All LLMs restored to Agent (Claude, Gemini, Llama, OpenAI, Mistral) |
| v4.1 | Streamlined to OpenAI-only models |
| v3.x | Initial SPCS deployment |
