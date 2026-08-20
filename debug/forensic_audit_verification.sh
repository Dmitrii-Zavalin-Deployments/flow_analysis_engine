#!/usr/bin/env bash
# ==============================================================================
# Forensic Audit Script for CI/CD Failure Diagnostics (Post-Test)
# Target: flow_analysis_engine (test_full_pipeline_integration_positive_path)
# ==============================================================================

set -euo pipefail

echo "=================================================="
echo "          BEGINNING FORENSIC AUDIT RUN            "
echo "=================================================="

# 1. Diagnostic: Environment & Git State Checks
echo "[DIAGNOSTIC] Checking repository status and recent commits..."
git status -s || true
git log -1 --oneline || true
python3 --version || true
python3 -m pytest --version || true

# 2. Diagnostic: Search codebase for SystemExit or exit triggers
echo "[DIAGNOSTIC] Searching for explicit SystemExit or exit triggers..."
grep -rn "SystemExit" src/ tests/ || true
grep -rn "sys.exit" src/ tests/ || true

# 3. Smoking-Gun Source Audit: Main Orchestrator (`src/main.py`)
echo "[SMOKING-GUN AUDIT] Line-numbered view of src/main.py exit blocks:"
if [ -f "src/main.py" ]; then
    cat -n src/main.py | head -n 135
else
    echo "WARNING: src/main.py not found."
fi

# 4. Smoking-Gun Source Audit: Parser Module
echo "[SMOKING-GUN AUDIT] Line-numbered view of src/core/parser.py:"
if [ -f "src/core/parser.py" ]; then
    cat -n src/core/parser.py
else
    echo "WARNING: src/core/parser.py not found."
fi

# 5. Diagnostic: Re-run targeted pytest using python module execution
echo "[DIAGNOSTIC] Executing targeted pytest with short tracebacks..."
python3 -m pytest tests/test_integration_flow.py -k "test_full_pipeline_integration_positive_path" --tb=short || true

# 6. Automated Repair Injection Templates (Commented out via # sed)
# Uncomment below to replace sys.exit(1) with exceptions for cleaner test capture if desired:
# sed -i 's/sys.exit(1)/raise RuntimeError("Pipeline execution failed")/g' src/main.py

echo "=================================================="
echo "            FORENSIC AUDIT COMPLETE               "
echo "=================================================="