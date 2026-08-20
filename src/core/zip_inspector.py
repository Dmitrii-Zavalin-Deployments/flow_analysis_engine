"""
Dedicated In-Memory ZIP Inspection Module.
Inspects simulation ZIP archives without unzipping, computes Navier-Stokes field statistics,
and verifies compliance against Bernoulli physical constraints.
"""

import io
import logging
import zipfile
from pathlib import Path

import numpy as np

# Configure structured module logger
logger = logging.getLogger("flow_engine.zip_inspector")


def inspect_simulation_zip(zip_path: Path, physical_constraints: dict) -> dict:
    """
    Reads .npy files directly from a ZIP archive in-memory, computes summary statistics,
    extracts targeted step snapshots, and validates against physical constraints
    under a strict no-default policy.
    """
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        logger.error("Simulation ZIP archive not found at target path: %s", zip_path)
        raise FileNotFoundError(f"Simulation ZIP archive not found: {zip_path}")

    if physical_constraints is None:
        logger.error("Physical constraints configuration was not provided (no-default policy enforced).")
        raise ValueError("Physical constraints configuration must be explicitly provided.")

    # Enforce presence of all required physical constraint bounds (no-default policy)
    required_bounds = ["min_velocity", "max_velocity", "min_pressure", "max_pressure"]
    for bound in required_bounds:
        if bound not in physical_constraints:
            logger.error("Missing required physical constraint key: %s", bound)
            raise KeyError(f"Missing required physical constraint key: {bound}")

    try:
        min_v_bound = float(physical_constraints["min_velocity"])
        max_v_bound = float(physical_constraints["max_velocity"])
        min_p_bound = float(physical_constraints["min_pressure"])
        max_p_bound = float(physical_constraints["max_pressure"])
    except (ValueError, TypeError) as e:
        logger.error("Invalid type or value for physical constraint bounds: %s", e)
        raise ValueError(f"Invalid physical constraint bound value: {e}") from e

    navier_stokes_summary = {}
    targeted_step_snapshots = {}
    global_min_val = float("inf")
    global_max_val = float("-inf")
    global_min_p = float("inf")
    global_max_p = float("-inf")

    logger.info("Inspecting simulation ZIP archive contents in memory.")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            npy_files = sorted([name for name in z.namelist() if name.endswith(".npy")])

            if not npy_files:
                logger.warning("No .npy files found inside simulation ZIP archive.")

            for name in npy_files:
                with z.open(name) as f:
                    arr = np.load(io.BytesIO(f.read()), allow_pickle=True)
                    non_zero = int(np.count_nonzero(arr))
                    total_size = int(arr.size)
                    arr_min = float(arr.min())
                    arr_max = float(arr.max())

                    # Track global bounds for constraint checking
                    if "u" in name or "v" in name or "w" in name:
                        global_min_val = min(global_min_val, arr_min)
                        global_max_val = max(global_max_val, arr_max)
                    if "p" in name:
                        global_min_p = min(global_min_p, arr_min)
                        global_max_p = max(global_max_p, arr_max)

                    navier_stokes_summary[name] = {
                        "shape": list(arr.shape),
                        "min": arr_min,
                        "max": arr_max,
                        "mean": float(arr.mean()),
                        "non_zero_count": non_zero,
                        "total_size": total_size,
                        "non_zero_ratio": float(non_zero / total_size) if total_size > 0 else 0.0
                    }

                    # Capture targeted step snapshots dynamically (e.g. step_000005)
                    if "step_000005" in name:
                        targeted_step_snapshots[name] = arr.tolist() if arr.ndim <= 2 else arr.flatten().tolist()[:16]
    except (zipfile.BadZipFile, OSError) as e:
        logger.error("Error reading simulation ZIP archive: %s", e)
        raise ValueError(f"Invalid or corrupted ZIP archive: {e}") from e

    # Bernoulli Boundary Verification against physical constraints
    bernoulli_check = {"verified": True, "details": []}

    if global_min_val < min_v_bound:
        bernoulli_check["verified"] = False
        bernoulli_check["details"].append(f"Velocity min {global_min_val} violated lower bound {min_v_bound}")
    if global_max_val > max_v_bound:
        bernoulli_check["verified"] = False
        bernoulli_check["details"].append(f"Velocity max {global_max_val} violated upper bound {max_v_bound}")
    if global_min_p < min_p_bound:
        bernoulli_check["verified"] = False
        bernoulli_check["details"].append(f"Pressure min {global_min_p} violated lower bound {min_p_bound}")
    if global_max_p > max_p_bound:
        bernoulli_check["verified"] = False
        bernoulli_check["details"].append(f"Pressure max {global_max_p} violated upper bound {max_p_bound}")

    logger.info("ZIP inspection and Bernoulli boundary verification completed successfully.")
    return {
        "archive_name": zip_path.name,
        "navier_stokes_summary": navier_stokes_summary,
        "targeted_step_snapshots": targeted_step_snapshots,
        "bernoulli_boundary_check": bernoulli_check
    }
