#!/usr/bin/env bash
# ==============================================================================
# Forensic Audit Script for CI/CD Pipeline Failure Diagnostics
# Target: flow_analysis_engine (NumPy allow_pickle=False error on np.load)
# File: src/debug/forensic_audit.sh
# ==============================================================================

set -euo pipefail

echo "=================================================="
echo "          BEGINNING FORENSIC AUDIT RUN            "
echo "=================================================="

# 1. Environment & Repository Diagnostics
echo "[DIAGNOSTIC] Checking repository status and Python environment..."
git status -s || true
git log -1 --oneline || true
python3 --version || true
python3 -c "import numpy; print('NumPy version:', numpy.__version__)" || true
python3 -m pytest --version || true

# 2. Diagnostics: Codebase Inspection for np.load occurrences
echo "[DIAGNOSTIC] Auditing codebase for np.load calls..."
grep -rn "np.load" src/ || true

# 3. Smoking-Gun Source Audits (cat -n)
echo "[SMOKING-GUN AUDIT] Line-numbered inspection of src/core/spatial_probe.py:"
if [ -f "src/core/spatial_probe.py" ]; then
    cat -n src/core/spatial_probe.py
fi

echo "[SMOKING-GUN AUDIT] Line-numbered inspection of src/core/zip_inspector.py:"
if [ -f "src/core/zip_inspector.py" ]; then
    cat -n src/core/zip_inspector.py
fi

echo "[SMOKING-GUN AUDIT] Line-numbered inspection of src/visualization/zip_field_renderer.py:"
if [ -f "src/visualization/zip_field_renderer.py" ]; then
    cat -n src/visualization/zip_field_renderer.py
fi

# 4. Targeted Pytest Re-run with Verbose Logging & Full Traceback
echo "[DIAGNOSTIC] Re-running failing integration test with detailed tracebacks..."
python3 -m pytest tests/test_integration_flow.py -k "test_full_pipeline_integration_positive_path" --tb=long -vv -s || true

# 5. Automated Repair Injection Templates (Commented out via # sed)
echo "[REPAIR TEMPLATES] Suggested automated repair injections for allow_pickle=True:"
# sed -i 's/np.load(io.BytesIO(f.read()))/np.load(io.BytesIO(f.read()), allow_pickle=True)/g' src/core/spatial_probe.py
# sed -i 's/np.load(io.BytesIO(f.read()))/np.load(io.BytesIO(f.read()), allow_pickle=True)/g' src/core/zip_inspector.py
# sed -i 's/np.load(io.BytesIO(npy_stream.read()))/np.load(io.BytesIO(npy_stream.read()), allow_pickle=True)/g' src/visualization/zip_field_renderer.py

echo "=================================================="
echo "            FORENSIC AUDIT COMPLETE               "
echo "=================================================="