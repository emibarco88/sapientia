#!/bin/bash

set -euo pipefail

DATABASE_DIR="database"
OUTPUT_FILE="sapientia_database_schema_context.txt"

if [ ! -d "$DATABASE_DIR" ]; then
    echo "Error: '$DATABASE_DIR' was not found."
    echo "Run this script from the Sapientia project root."
    exit 1
fi

rm -f "$OUTPUT_FILE"

{
    echo "=========================================="
    echo " Sapientia Database Schema Context"
    echo "=========================================="
    echo
    echo "Generated from: $DATABASE_DIR"
    echo
    echo "Directory structure:"
    echo "------------------------------------------"
    find "$DATABASE_DIR" -type f | sort
    echo
} >> "$OUTPUT_FILE"

find "$DATABASE_DIR" \
    -type f \
    \( -name "*.sql" -o -name "*.ddl" -o -name "*.psql" \) \
    -print0 |
while IFS= read -r -d '' FILE
do
    {
        echo
        echo "========================================================="
        echo "FILE: $FILE"
        echo "========================================================="
        cat "$FILE"
        echo
    } >> "$OUTPUT_FILE"
done

echo "Created: $OUTPUT_FILE"
