# Plan: Add Staged PDFs and Vectorization

## Context
I inspected the current app and found that the document search path is already mostly in place.

- The backend search endpoint in [spcs-app/backend/main.py](spcs-app/backend/main.py) already calls `SNOWFLAKE.CORTEX.SEARCH_PREVIEW` against `PEPARTNERS_DB.CORE.COMPANY_FILINGS_SEARCH_SERVICE` and returns filing search results through `/api/search`.
- The frontend search page in [spcs-app/frontend/src/controllers/searchCtrl.js](spcs-app/frontend/src/controllers/searchCtrl.js) already consumes `/api/search`, lists filing companies from `/api/filings/companies`, and drills into filing text and precomputed analysis.
- The base schema in [setup/01_ddl.sql](setup/01_ddl.sql) already defines the key document objects: `COMPANY_FILINGS`, `COMPANY_FILINGS_CHUNKS`, `COMPANY_FILINGS_TEXT`, and `COMPANY_FILINGS_ANALYSIS`.
- The rebuild pipeline in [setup/04_documents_search.sql](setup/04_documents_search.sql) already assumes PDFs are in `@PEPARTNERS_DB.CORE.DOCUMENTS_STAGE`, parses them with `SNOWFLAKE.CORTEX.PARSE_DOCUMENT`, chunks text with `SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER`, and recreates the Cortex Search service.
- The docs in [README.md](README.md), [documents/README.md](documents/README.md), and [documents/INSTALL.md](documents/INSTALL.md) currently describe a local `documents/` folder workflow, but your request is stage-first: "add the pdfs in stage to this app and vectorise them". The implementation should therefore align the documentation and operator flow to the stage-backed pipeline already present in SQL.

The main design conclusion is that this is not a net-new feature. The repo already has the right object model. The work should focus on tightening the existing stage-to-search pipeline and making the app consume it reliably.

```mermaid
flowchart LR
    pdfStage[DOCUMENTS_STAGE] --> rawTable[DOCUMENTS_RAW]
    rawTable --> filingsTable[COMPANY_FILINGS]
    rawTable --> fullTextTable[COMPANY_FILINGS_TEXT]
    fullTextTable --> chunksTable[COMPANY_FILINGS_CHUNKS]
    fullTextTable --> analysisTable[COMPANY_FILINGS_ANALYSIS]
    chunksTable --> searchService[COMPANY_FILINGS_SEARCH_SERVICE]
    searchService --> backendApi[/api/search]
    filingsTable --> backendApi
    analysisTable --> backendApi
    backendApi --> searchUi[SearchCtrl]
```

## Implementation steps
1. Normalize the stage-first ingestion contract in [setup/04_documents_search.sql](setup/04_documents_search.sql).
   - Preserve `DOCUMENTS_STAGE` as the source of truth.
   - Keep `DOCUMENTS_RAW` as the inventory/parse layer.
   - Ensure the script remains repeatable by explicitly rebuilding downstream tables from staged PDFs.
   - Review the filename parsing assumptions so company name, ticker, form type, and filing date extraction are robust for the naming convention the repo already documents.

2. Ensure vectorization/search indexing uses the existing objects cleanly.
   - Keep chunk generation in `COMPANY_FILINGS_CHUNKS` as the search corpus instead of introducing a parallel embeddings table.
   - Recreate `PEPARTNERS_DB.CORE.COMPANY_FILINGS_SEARCH_SERVICE` from `COMPANY_FILINGS_CHUNKS` with the attributes already expected by the app.
   - If needed, add stable metadata columns only when the backend or UI can actually use them; otherwise keep the current payload shape.

3. Tighten the backend contract in [spcs-app/backend/main.py](spcs-app/backend/main.py).
   - Leave `/api/search`, `/api/filings`, `/api/filings/{id}/text`, and `/api/filings/{id}/analysis` in place.
   - Confirm the configured `FILINGS_SEARCH_SERVICE` name matches the SQL-created object and make any small adjustments needed so the backend remains environment-configurable.
   - Avoid changing the response shape consumed by the Angular controller.

4. Keep the frontend unchanged unless a mismatch is uncovered.
   - The current controller in [spcs-app/frontend/src/controllers/searchCtrl.js](spcs-app/frontend/src/controllers/searchCtrl.js) already matches the existing backend flow.
   - Only touch it if the stage-backed pipeline exposes a metadata mismatch that prevents correct rendering or filing selection.

5. Update the operator documentation to match the actual workflow.
   - Revise [README.md](README.md) and [documents/INSTALL.md](documents/INSTALL.md) to say the PDFs live in the Snowflake stage and the repo SQL rebuilds the searchable corpus from there.
   - Keep [documents/README.md](documents/README.md) only as a staging/upload convention if you still want a local preload folder; otherwise rewrite it so it no longer implies local files are required for the app to function.
   - Document the exact sequence: upload PDFs to `@PEPARTNERS_DB.CORE.DOCUMENTS_STAGE`, run `setup/04_documents_search.sql`, verify the search service, then use the Search page in the app.

## Verification
- Compile or execute read-only verification queries against Snowflake after the SQL changes are prepared:
  - `SHOW STAGES LIKE 'DOCUMENTS_STAGE' IN SCHEMA PEPARTNERS_DB.CORE;`
  - `SELECT * FROM DIRECTORY('@PEPARTNERS_DB.CORE.DOCUMENTS_STAGE') WHERE LOWER(RELATIVE_PATH) LIKE '%.pdf';`
  - `SHOW CORTEX SEARCH SERVICES IN SCHEMA PEPARTNERS_DB.CORE;`
  - `SELECT COUNT(*) FROM PEPARTNERS_DB.CORE.COMPANY_FILINGS;`
  - `SELECT COUNT(*) FROM PEPARTNERS_DB.CORE.COMPANY_FILINGS_CHUNKS;`
- Smoke-check the backend search route against the rebuilt service by verifying `FILINGS_SEARCH_SERVICE` still points to `PEPARTNERS_DB.CORE.COMPANY_FILINGS_SEARCH_SERVICE` in [spcs-app/backend/main.py](spcs-app/backend/main.py).
- Manual app validation after implementation:
  - Open the Search tab.
  - Run a filing search query that should match staged PDF content.
  - Open a filing and confirm summary, sentiment, and extracted text render correctly.

## Critical Files
- [setup/04_documents_search.sql](setup/04_documents_search.sql) - Core stage-to-parse-to-chunk-to-search pipeline that will do the actual vectorization work.
- [setup/01_ddl.sql](setup/01_ddl.sql) - Defines the durable document tables the pipeline populates.
- [spcs-app/backend/main.py](spcs-app/backend/main.py) - Search API integration point for the Cortex Search service and filing detail endpoints.
- [spcs-app/frontend/src/controllers/searchCtrl.js](spcs-app/frontend/src/controllers/searchCtrl.js) - Existing UI contract that consumes the search and filing detail APIs.
- [documents/INSTALL.md](documents/INSTALL.md) - Operator instructions that need to reflect the stage-first workflow accurately.