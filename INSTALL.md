# Installation Guide

## Prerequisites

- Snowflake account with ACCOUNTADMIN access
- Docker Desktop installed locally
- Snowflake CLI (`snow`) installed: `pip install snowflake-cli-labs`
- GitHub CLI (`gh`) for CI/CD setup (optional)

## Step 1: Snowflake Object Setup

Run the DDL script to create all database objects:

```sql
-- In a Snowflake worksheet, run:
-- setup/01_ddl.sql
```

This creates the database, schema, warehouses, compute pool, tables, and interactive tables.

## Step 2: Load Sample Data

Run the data script to populate all tables with sample data:

```sql
-- In a Snowflake worksheet, run:
-- setup/02_data.sql
```

## Step 3: Build and Deploy

```bash
# Login to the Snowflake image registry
snow spcs image-registry login -c <your_connection_name>

# Build the Docker image
cd spcs-app
docker build --platform linux/amd64 \
  -t <account>.registry.snowflakecomputing.com/pepartners_db/core/pe_repo/pe-angular:latest .

# Push to registry
docker push <account>.registry.snowflakecomputing.com/pepartners_db/core/pe_repo/pe-angular:latest
```

## Step 4: Create the Service

Run `setup/03_deploy_service.sql` (replace `<YOUR_ACCOUNT>` with your account identifier).

## Step 5: Access the App

```sql
SHOW ENDPOINTS IN SERVICE PEPARTNERS_DB.CORE.PE_APP_V3;
```

The `ingress_url` column shows the public URL. It takes 1-2 minutes to provision after service creation.

> **Important:** Do NOT set `SNOWFLAKE_ACCOUNT` or `SNOWFLAKE_HOST` in the service spec env vars. Snowflake auto-injects these with the correct values for SPCS OAuth authentication.

## Optional: Cortex Search (Document Search feature)

To enable the Document Search tab, create a Cortex Search service over your filing data:

```sql
CREATE CORTEX SEARCH SERVICE PEPARTNERS_DB.CORE.COMPANY_FILINGS_SEARCH_SERVICE
  ON CHUNK_TEXT
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT FILING_ID, COMPANY_NAME, TICKER, FORM_TYPE, FILING_CATEGORY, FILING_DATE, CHUNK_TEXT
    FROM PEPARTNERS_DB.CORE.COMPANY_FILINGS_CHUNKS
  );
```

## Redeploying

After code changes, rebuild and push the image, then restart the service:

```bash
docker build --platform linux/amd64 -t <image_url> ./spcs-app/
docker push <image_url>
```

```sql
-- Must drop and recreate to pull new image (SPCS caches image digests)
DROP SERVICE PEPARTNERS_DB.CORE.PE_APP_V3;
-- Then re-run the CREATE SERVICE statement above
```

## Troubleshooting

**Check service status:**
```sql
SELECT SYSTEM$GET_SERVICE_STATUS('PEPARTNERS_DB.CORE.PE_APP_V3');
```

**Check logs:**
```sql
CALL SYSTEM$GET_SERVICE_LOGS('PEPARTNERS_DB.CORE.PE_APP_V3', '0', 'app', 50);
```

**Common issues:**
- "Client is unauthorized to use Snowpark Container Services OAuth token" — You have `SNOWFLAKE_ACCOUNT` or `SNOWFLAKE_HOST` set in the service spec. Remove them.
- "Endpoints provisioning in progress" — Wait 1-2 minutes after service creation.
- No data showing — Check that the `_STG` tables have data and the interactive tables have refreshed.
