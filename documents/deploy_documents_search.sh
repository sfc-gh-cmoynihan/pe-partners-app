#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCUMENTS_DIR="${1:-$ROOT_DIR/documents}"
SNOW_CONNECTION="${SNOW_CONNECTION:-}"
STAGE_NAME="PEPARTNERS_DB.CORE.DOCUMENTS_STAGE"
SQL_FILE="$ROOT_DIR/setup/04_documents_search.sql"

if [[ -z "$SNOW_CONNECTION" ]]; then
  echo "SNOW_CONNECTION must be set to a configured Snowflake CLI connection name." >&2
  exit 1
fi

if [[ ! -d "$DOCUMENTS_DIR" ]]; then
  echo "Documents directory not found: $DOCUMENTS_DIR" >&2
  exit 1
fi

if ! compgen -G "$DOCUMENTS_DIR/*.pdf" > /dev/null && ! compgen -G "$DOCUMENTS_DIR/*.PDF" > /dev/null; then
  echo "No PDF files found in $DOCUMENTS_DIR" >&2
  exit 1
fi

snow sql -c "$SNOW_CONNECTION" -f "$ROOT_DIR/setup/01_ddl.sql"
snow sql -c "$SNOW_CONNECTION" -q "CREATE STAGE IF NOT EXISTS $STAGE_NAME DIRECTORY = (ENABLE = TRUE);"
snow stage copy "$DOCUMENTS_DIR" "@$STAGE_NAME" --connection "$SNOW_CONNECTION" --recursive --overwrite
snow sql -c "$SNOW_CONNECTION" -f "$SQL_FILE"

echo "Documents uploaded and Cortex Search deployed from $DOCUMENTS_DIR"