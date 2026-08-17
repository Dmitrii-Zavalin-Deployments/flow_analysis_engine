#!/usr/bin/env bash
set -uo pipefail

echo "=================================================="
echo "🔍 STARTING FORENSIC AUDIT FOR INPUT CONTRACT ERROR"
echo "=================================================="

echo "--- 1. Directory & File System Diagnostics ---"
echo "Checking target directory: data/testing-input-output/"
if [ -d "data/testing-input-output" ]; then
    echo "✅ Directory exists. Listing contents:"
    ls -la data/testing-input-output/
else
    echo "❌ CRITICAL: Directory 'data/testing-input-output/' does not exist."
    echo "Listing workspace root to find where data files might be located:"
    find . -maxdepth 3 -not -path '*/.*' -not -path './conda*'
fi

echo "--- 2. Pattern Matching / Grep Diagnostics ---"
echo "Searching codebase for input folder references..."
grep -rn "testing-input-output" src/ .github/ || echo "No direct references found."

echo "--- 3. Smoking-Gun Source Audit (cat -n) ---"
if [ -f "src/main.py" ]; then
    echo "Inspecting src/main.py:"
    cat -n src/main.py
else
    echo "❌ src/main.py not found."
fi

echo "=================================================="
echo "🛠️ AUTOMATED REPAIR INJECTIONS (PRE-CONFIGURED)"
echo "=================================================="
echo "Uncomment the desired sed command below to apply automated fixes."

# sed -i 's|ls data/testing-input-output/\*.json|ls data/testing-input-output/*.json data/*.json 2>/dev/null|g' .github/workflows/*.yml
# sed -i 's|if \[ -z "\$INPUT_JSON" \]; then|mkdir -p data/testing-input-output \&\& echo "{\\"parameters\\":{\\"grid_resolution\\":[32,32,32],\\"reynolds_number\\":1000.0}}" > data/testing-input-output/fallback_input.json\nif [ -z "$INPUT_JSON" ]; then|g' .github/workflows/*.yml

echo "Audit completed."