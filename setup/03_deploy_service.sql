-- =============================================================================
-- PE Partners - Deploy Service
-- Run AFTER building and pushing the Docker image
-- =============================================================================

-- Replace <YOUR_ACCOUNT> with your account identifier (e.g. myorg-myaccount)
-- The image URL should match what you pushed in the docker push step

USE ROLE ACCOUNTADMIN;
USE SCHEMA PEPARTNERS_DB.CORE;

CREATE SERVICE PEPARTNERS_DB.CORE.PE_APP_V3
  IN COMPUTE POOL PE_APP_POOL
  EXTERNAL_ACCESS_INTEGRATIONS = (PE_SNOWFLAKE_EAI)
  MIN_INSTANCES = 1
  MAX_INSTANCES = 1
  MIN_READY_INSTANCES = 1
  AUTO_RESUME = TRUE
  AUTO_SUSPEND_SECS = 0
  FROM SPECIFICATION $$
spec:
  containers:
  - name: app
    image: <YOUR_ACCOUNT>.registry.snowflakecomputing.com/pepartners_db/core/pe_repo/pe-angular:latest
    env:
      SNOWFLAKE_WAREHOUSE: "COMPUTE_WH"
    resources:
      limits:
        memory: "4Gi"
        cpu: "2"
      requests:
        memory: "1Gi"
        cpu: "0.5"
  endpoints:
  - name: app
    port: 8080
    public: true
$$;

-- Check the service status
SELECT SYSTEM$GET_SERVICE_STATUS('PEPARTNERS_DB.CORE.PE_APP_V3');

-- Get the public URL (wait 1-2 minutes after creation)
SHOW ENDPOINTS IN SERVICE PEPARTNERS_DB.CORE.PE_APP_V3;
