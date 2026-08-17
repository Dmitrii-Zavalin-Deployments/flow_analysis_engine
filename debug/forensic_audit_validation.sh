#!/usr/bin/env bash
set -uo pipefail

echo "=================================================="
echo "🔍 FORENSIC AUDIT: Variable Mismatch / Input Contract Failure"
echo "=================================================="

echo "--- 1. File System & Directory Inspection ---"
echo "Checking contents of data/testing-input-output/:"
ls -la data/testing-input-output/ || echo "Directory not found"

echo "--- 2. Pattern Matching / Grep Diagnostics ---"
echo "Searching for INPUT_FILE and INPUT_JSON definitions in workflow files:"
grep -rn "INPUT_FILE" .github/workflows/ || echo "No INPUT_FILE references found."
grep -rn "INPUT_JSON" .github/workflows/ || echo "No INPUT_JSON references found."

echo "--- 3. Smoking-Gun Source Audit (cat -n) ---"
WORKFLOW_FILE=".github/workflows/flow_analysis_engine.yml"
if [ -f "$WORKFLOW_FILE" ]; then
    echo "Inspecting active workflow file execution block (lines 218-245):"
    sed -n '218,245p' "$WORKFLOW_FILE" | cat -n
else
    echo "❌ Workflow file not found at $WORKFLOW_FILE."
fi

echo "=================================================="
echo "🛠️ AUTOMATED REPAIR INJECTIONS (PRE-CONFIGURED)"
echo "=================================================="
echo "Uncomment the desired sed commands below to apply automated fixes for the variable mismatch[cite: 1]:"

# sed -i 's|if \[ -z "\$INPUT_JSON" \]; then|INPUT_JSON=\$(basename "\$INPUT_FILE")\n          if [ -z "\$INPUT_JSON" ]; then|g' .github/workflows/flow_analysis_engine.yml
# sed -i 's|INPUT_FILE="data/testing-input-output/flow_analysis_engine_input.json"|INPUT_JSON=\$(basename \$(ls data/testing-input-output/*.json 2>/dev/null | head -n 1))\n          INPUT_FILE="data/testing-input-output/\$INPUT_JSON"|g' .github/workflows/flow_analysis_engine.yml

echo "Audit completed successfully."