#!/usr/bin/env bash
set -euo pipefail

ZIP_PATH="${1:-data/testing-input-output/20260819_150716.zip}"

echo "=================================================="
echo "📦 Inspecting Simulation ZIP: $ZIP_PATH"
echo "=================================================="

# 1. Summary Statistics Across All NPY Files
echo -e "\n--- [1] Summary Statistics Across All NPY Files ---"
python3 -c '
import zipfile, io, numpy as np
import sys

zip_path = sys.argv[1]
with zipfile.ZipFile(zip_path, "r") as z:
    for name in sorted(z.namelist()):
        if name.endswith(".npy"):
            arr = np.load(io.BytesIO(z.read(name)))
            non_zero = np.count_nonzero(arr)
            print(f"{name:30s} | Shape: {str(arr.shape):12s} | Min: {arr.min():.6e} | Max: {arr.max():.6e} | Non-Zero: {non_zero}/{arr.size}")
' "$ZIP_PATH"

# 2. Print Raw Values of Specific Fluid Channel Steps
echo -e "\n--- [2] Raw Values for Specific Steps ---"
python3 -c '
import zipfile, io, numpy as np
import sys

zip_path = sys.argv[1]
with zipfile.ZipFile(zip_path, "r") as z:
    for file_key in ["field_u_step_000005.npy", "field_p_step_000005.npy"]:
        if file_key in z.namelist():
            arr = np.load(io.BytesIO(z.read(file_key)))
            print(f"=== {file_key} raw array ===")
            print(arr)
' "$ZIP_PATH"

echo -e "\n✅ Inspection complete."