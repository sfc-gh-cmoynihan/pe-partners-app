----------------------------------------------------------------------
-- NESTED NOTEBOOKS DEMO: Customer Deduplication Pipeline
-- 
-- This script demonstrates:
--   1. Creating the lineage tracking table
--   2. Setting up a 3-step dependent task graph (notebook chaining)
--   3. Running the pipeline
--   4. Querying lineage to see the full data flow
----------------------------------------------------------------------

USE DATABASE PEPARTNERS_DB;
USE SCHEMA CORE;
USE WAREHOUSE COMPUTE_WH;

----------------------------------------------------------------------
-- STEP 1: Create the lineage tracking table
----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS PIPELINE_LINEAGE (
    LINEAGE_ID NUMBER AUTOINCREMENT,
    RUN_ID VARCHAR(100),
    NOTEBOOK_NAME VARCHAR(200),
    STEP_NAME VARCHAR(200),
    SOURCE_OBJECT VARCHAR(500),
    TARGET_OBJECT VARCHAR(500),
    OPERATION VARCHAR(50),
    ROW_COUNT NUMBER,
    EXECUTION_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    STATUS VARCHAR(20) DEFAULT 'SUCCESS',
    ERROR_MESSAGE VARCHAR(2000),
    DURATION_SECONDS NUMBER
);

----------------------------------------------------------------------
-- STEP 2: Create the dependent task graph
--
--   TASK_DEDUPLICATE_CUSTOMERS (root - runs daily)
--       └─► TASK_CUSTOMERS_UK_VIEW (child of root)
--               └─► TASK_CUSTOMERS_IRELAND_MATVIEW (child of UK task)
----------------------------------------------------------------------

-- Root task: Deduplicate customers and create golden source
CREATE OR REPLACE TASK TASK_DEDUPLICATE_CUSTOMERS
    WAREHOUSE = 'COMPUTE_WH'
    SCHEDULE = '1440 MINUTE'
AS
    EXECUTE NOTEBOOK PEPARTNERS_DB.CORE."01_deduplicate_customers";

-- Child task 2: Create UK view (depends on dedup completing)
CREATE OR REPLACE TASK TASK_CUSTOMERS_UK_VIEW
    WAREHOUSE = 'COMPUTE_WH'
    AFTER TASK_DEDUPLICATE_CUSTOMERS
AS
    EXECUTE NOTEBOOK PEPARTNERS_DB.CORE."02_customers_uk_view";

-- Child task 3: Create Ireland materialized view (depends on UK view)
CREATE OR REPLACE TASK TASK_CUSTOMERS_IRELAND_MATVIEW
    WAREHOUSE = 'COMPUTE_WH'
    AFTER TASK_CUSTOMERS_UK_VIEW
AS
    EXECUTE NOTEBOOK PEPARTNERS_DB.CORE."03_customers_ireland_matview";

----------------------------------------------------------------------
-- STEP 3: Resume all tasks in the graph
----------------------------------------------------------------------
SELECT SYSTEM$TASK_DEPENDENTS_ENABLE('PEPARTNERS_DB.CORE.TASK_DEDUPLICATE_CUSTOMERS');

----------------------------------------------------------------------
-- STEP 4: Execute the pipeline manually (on-demand run)
----------------------------------------------------------------------
EXECUTE TASK TASK_DEDUPLICATE_CUSTOMERS;

----------------------------------------------------------------------
-- STEP 5: Monitor task execution
----------------------------------------------------------------------

-- Check recent task history
SELECT name, state, scheduled_time, completed_time, error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('hour', -1, CURRENT_TIMESTAMP()),
    RESULT_LIMIT => 20
))
WHERE name IN ('TASK_DEDUPLICATE_CUSTOMERS', 'TASK_CUSTOMERS_UK_VIEW', 'TASK_CUSTOMERS_IRELAND_MATVIEW')
ORDER BY scheduled_time DESC;

----------------------------------------------------------------------
-- STEP 6: Query lineage (the full data flow)
----------------------------------------------------------------------

-- View all lineage entries
SELECT 
    RUN_ID,
    NOTEBOOK_NAME,
    STEP_NAME,
    SOURCE_OBJECT,
    TARGET_OBJECT,
    OPERATION,
    ROW_COUNT,
    EXECUTION_TIMESTAMP,
    DURATION_SECONDS,
    STATUS
FROM PIPELINE_LINEAGE
ORDER BY EXECUTION_TIMESTAMP DESC;

-- View lineage as a graph (source → target relationships)
SELECT DISTINCT
    SOURCE_OBJECT AS "FROM",
    TARGET_OBJECT AS "TO",
    OPERATION,
    NOTEBOOK_NAME AS "EXECUTED_BY"
FROM PIPELINE_LINEAGE
WHERE STATUS = 'SUCCESS'
ORDER BY SOURCE_OBJECT;

----------------------------------------------------------------------
-- CLEANUP (optional - uncomment to tear down)
----------------------------------------------------------------------
-- ALTER TASK TASK_DEDUPLICATE_CUSTOMERS SUSPEND;
-- DROP TASK IF EXISTS TASK_CUSTOMERS_IRELAND_MATVIEW;
-- DROP TASK IF EXISTS TASK_CUSTOMERS_UK_VIEW;
-- DROP TASK IF EXISTS TASK_DEDUPLICATE_CUSTOMERS;
-- DROP MATERIALIZED VIEW IF EXISTS CUSTOMERS_IRELAND;
-- DROP VIEW IF EXISTS CUSTOMERS_UK;
-- DROP TABLE IF EXISTS CUSTOMERS_GOLDEN;
-- DROP TABLE IF EXISTS PIPELINE_LINEAGE;
