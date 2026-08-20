#!/usr/bin/env bash
# ==============================================================================
# Forensic Audit & Automated Repair Script for Flow Analysis Engine
# Target Issue: NumPy loading error due to pickled data objects (allow_pickle=False)
# ==============================================================================

set -euo pipefail

echo "=============================================================================="
echo "1. DIAGNOSTICS: Locating numpy.load() occurrences across the codebase"
echo "=============================================================================="
grep -rn "np.load" src/ || echo "No direct np.load found, searching for load variants..."
grep -rn "load(" src/core/ || true

echo ""
echo "=============================================================================="
echo "2. SMOKING-GUN SOURCE AUDIT: Line-numbered view of processor.py"
echo "=============================================================================="
if [ -f "src/core/processor.py" ]; then
    cat -n src/core/processor.py
else
    echo "Warning: src/core/processor.py not found in current directory."
fi

echo ""
echo "=============================================================================="
echo "3. ENVIRONMENT & TEST RUNNER CHECK"
echo "=============================================================================="
python3 -c "import sys, numpy; print('Python:', sys.version); print('NumPy version:', numpy.__version__)"
pytest --version || echo "pytest not found in current PATH environment."

echo ""
echo "=============================================================================="
echo "4. AUTOMATED REPAIRS (sed Injections - Uncomment to apply)"
echo "=============================================================================="
# Fix numpy load in processor.py by enabling allow_pickle=True for trusted array files
# sed -i 's/np.load(/np.load(..., allow_pickle=True)/g' src/core/processor.py
# sed -i 's/np.load(\([^)]*\))/np.load(\1, allow_pickle=True)/g' src/core/processor.py

echo "Forensic audit script execution completed."