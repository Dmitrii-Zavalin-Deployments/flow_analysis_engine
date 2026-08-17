#!/usr/bin/env bash
set -uo pipefail

echo "=================================================="
echo "🔍 FORENSIC AUDIT: Missing Input JSON Contract Failure"
echo "=================================================="

echo "--- 1. File System & Directory Inspection ---"
echo "Listing workspace root structure:"
find . -maxdepth 3 -not -path '*/.*' -not -path './conda*'

echo "Checking target input data directory status:"
if [ -d "data/testing-input-output" ]; then
    echo "✅ 'data/testing-input-output' exists. Listing contents:"
    ls -la data/testing-input-output/
else
    echo "❌ CRITICAL: 'data/testing-input-output' directory does NOT exist."
    echo "Searching for any .json files across the workspace:"
    find . -name "*.json" -not -path '*/.*' -not -path './conda*'
fi

echo "--- 2. Pattern Matching / Grep Diagnostics ---"
echo "Searching for input folder definitions and contract checks across codebase and workflows:"
grep -rn "testing-input-output" .github/ src/ || echo "No references found."

echo "--- 3. Smoking-Gun Source Audit (cat -n) ---"
WORKFLOW_FILE=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | head -n 1)
if [ -n "$WORKFLOW_FILE" ]; then
    echo "Inspecting active workflow file: $WORKFLOW_FILE"
    cat -n "$WORKFLOW_FILE"
else
    echo "❌ No GitHub Actions workflow file located."
fi

echo "=================================================="
echo "🛠️ AUTOMATED REPAIR INJECTIONS (PRE-CONFIGURED)"
echo "=================================================="
echo "Uncomment the desired sed commands below to apply automated fixes."

# sed -i 's|if \[ -z "\$INPUT_JSON" \]; then|mkdir -p data/testing-input-output \&\& echo "{\\"parameters\\":{\\"grid_resolution\\":[32,32,32],\\"reynolds_number\\":1000.0}}" > data/testing-input-output/fallback_input.json\n          INPUT_JSON="fallback_input.json"\n          if [ -z "$INPUT_JSON" ]; then|g' .github/workflows/*.yml
# sed -i 's|data/testing-input-output/|data/|g' .github/workflows/*.yml

echo "Audit completed successfully."