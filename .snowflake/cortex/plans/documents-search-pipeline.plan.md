# Plan: Documents Folder and Cortex Search Pipeline

## Current State
- The app already exposes a document search endpoint in `spcs-app/backend/main.py:51` that calls `SNOWFLAKE.CORTEX.SEARCH_PREVIEW` against `PEPARTNERS_DB.CORE.COMPANY_FILINGS_SEARCH_SERVICE`.
- The current schema creates filing metadata and chunk tables in `setup/01_ddl.sql:112` and `setup/01_ddl.sql:123`, but there is no repo-managed pipeline that ingests PDFs from a local `documents/` folder into those tables.
- The install docs only describe manual search-service creation in `INSTALL.md:59`, so deployment is incomplete for the workflow you want.
- No PDFs are currently present in the repo, and the provided local source path did not surface any PDFs during discovery. I will treat `documents/` as a required runtime/input folder contract rather than committing files.

## Proposed Changes

### 1. Add a `documents/` folder contract to the repo
- Create an empty `documents/` directory with a small README describing the expected inputs: annual reports, 8-Ks, 10-Ks in PDF format.
- Keep the PDFs out of git by default, but make the app and deployment expect that folder to exist.
- This keeps the repo lightweight while making ingestion deterministic.

### 2. Add a Snowflake-native PDF ingestion pipeline
- Extend setup SQL to create the document stage and processing objects needed for PDF ingestion.
- The conservative approach is:
  - a named internal stage for uploaded PDFs
  - a raw document inventory table keyed by relative path / filename
  - a parsed text table generated from staged PDFs using Snowflake document parsing
  - a chunk table shaped for Cortex Search
- If the repo already uses `COMPANY_FILINGS` / `COMPANY_FILINGS_CHUNKS` in the UI, prefer preserving those objects and backfilling them from the PDF pipeline rather than changing the frontend contract.

### 3. Add a repeatable local-to-Snowflake deployment script
- Add a script that uploads PDFs from `documents/` to the Snowflake stage and then runs the SQL pipeline to parse/chunk them.
- The script should be explicit and idempotent so the deployment flow becomes:
  - populate `documents/`
  - run setup SQL
  - run document upload/index script
  - create/refresh Cortex Search service
- Use the existing warehouse `COMPUTE_WH` per your instruction.

### 4. Make backend search target configurable and aligned
- Update `spcs-app/backend/main.py:67` to use the search service created by the new setup path through a constant/env var instead of a hard-coded object name.
- Keep the API payload shape stable so frontend code in `spcs-app/frontend/src/controllers/searchCtrl.js:118` does not need behavioral changes unless the returned metadata columns expand.

### 5. Update deployment documentation
- Update `INSTALL.md` and likely `README.md` with the exact workflow for:
  - where PDFs go
  - how to upload them
  - how to build embeddings/search index
  - how to redeploy or refresh after adding more PDFs
- Document assumptions and prerequisites clearly, especially that `documents/` must be populated locally before running the ingestion step.

## Key Decisions
- Preserve the existing app search API and result contract rather than introducing a new search feature surface.
- Treat `documents/` as an expected local input folder, not a source-controlled binary dump.
- Use Snowflake-native document parsing plus Cortex Search indexing, with `COMPUTE_WH` as the warehouse.

## Open Risk
- The provided local source path appears empty from the workspace view. If that remains true at implementation time, I can still wire the full pipeline and folder structure, but I will not be able to validate end-to-end ingestion against real PDFs until files are placed in `documents/`.

## Validation Plan
- Verify the repo contains the new `documents/` contract and deployment script/docs.
- Compile/inspect the new SQL objects for stage, parse, chunk, and search service creation.
- Smoke-check backend references to ensure the search endpoint points at the new configurable Cortex Search object.
- If PDFs are available during implementation, run the ingestion workflow and confirm `/api/search` returns results from indexed PDF content.