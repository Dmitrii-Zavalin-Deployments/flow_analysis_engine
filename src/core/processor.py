"""
Numerical processing module for coordinate grid computation and zip inspection coordination.
"""

import logging
from pathlib import Path

from src.core.spatial_probe import analyze_spatial_intervals
from src.core.zip_inspector import inspect_simulation_zip

# Configure structured module logger
logger = logging.getLogger("flow_engine.processor")


def process_flow_data(raw_data: dict, input_dir: Path | str) -> dict:
    """
    Processes flow grid configurations, invokes zip inspection, boundary verification,
    and config-driven spatial interval probing under a strict no-default policy.
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        logger.error("Input directory path is invalid or does not exist: %s", input_dir)
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    logger.info("Extracting and validating configuration from input data.")

    # No-default policy: Enforce presence of 'inputs' section
    if "inputs" not in raw_data:
        logger.error("Missing required 'inputs' section in raw data.")
        raise KeyError("Missing required 'inputs' section in raw data.")

    inputs = raw_data["inputs"]

    # Enforce presence of 'grid' configuration
    if "grid" not in inputs:
        logger.error("Missing required 'grid' configuration in inputs.")
        raise KeyError("Missing required 'grid' configuration in inputs.")

    grid_cfg = inputs["grid"]

    # Required grid parameters (no-default policy enforced)
    try:
        nx = int(grid_cfg["nx"])
        ny = int(grid_cfg["ny"])
        nz = int(grid_cfg["nz"])
        x_min = float(grid_cfg["x_min"])
        x_max = float(grid_cfg["x_max"])
        y_min = float(grid_cfg["y_min"])
        y_max = float(grid_cfg["y_max"])
        z_min = float(grid_cfg["z_min"])
        z_max = float(grid_cfg["z_max"])
    except KeyError as e:
        logger.error("Missing required grid parameter: %s", e)
        raise KeyError(f"Missing required grid parameter: {e}") from e
    except (ValueError, TypeError) as e:
        logger.error("Invalid type or value for grid parameters: %s", e)
        raise ValueError(f"Invalid grid parameter value: {e}") from e

    if nx <= 0 or ny <= 0 or nz <= 0:
        logger.error("Grid dimensions (nx, ny, nz) must be strictly greater than zero.")
        raise ValueError("Grid dimensions (nx, ny, nz) must be strictly greater than zero.")

    dx = (x_max - x_min) / nx
    dy = (y_max - y_min) / ny
    dz = (z_max - z_min) / nz

    # Enforce presence of mask
    if "mask" not in inputs:
        logger.error("Missing required 'mask' key in inputs.")
        raise KeyError("Missing required 'mask' key in inputs.")

    mask = inputs["mask"]
    expected_cells = nx * ny * nz
    if not isinstance(mask, list) or len(mask) != expected_cells:
        logger.error("Mask must be a list with length matching total grid cells (nx * ny * nz).")
        raise ValueError("Mask length does not match total grid cells.")

    # Enforce physical constraints configuration presence
    if "physical_constraints" not in inputs:
        logger.error("Missing required 'physical_constraints' section in inputs.")
        raise KeyError("Missing required 'physical_constraints' section in inputs.")

    physical_constraints = inputs["physical_constraints"]

    # Enforce zip_filename presence (no auto-discovery or globbing fallback)
    if "zip_filename" not in inputs:
        logger.error("Missing required 'zip_filename' parameter in inputs.")
        raise KeyError("Missing required 'zip_filename' parameter in inputs.")

    zip_filename = inputs["zip_filename"]
    zip_path = input_dir / zip_filename

    if not zip_path.exists():
        logger.error("Configured ZIP archive does not exist at target path.")
        raise FileNotFoundError(f"Configured ZIP archive not found: {zip_path}")

    logger.info("Executing simulation ZIP inspection and spatial interval analysis.")
    inspection_results = inspect_simulation_zip(zip_path, physical_constraints)

    grid_specs = {
        "nx": nx, "ny": ny, "nz": nz,
        "x_min": x_min, "x_max": x_max,
        "y_min": y_min, "y_max": y_max,
        "z_min": z_min, "z_max": z_max
    }

    # Resolve config.json directly from input_dir or fallback to the repository's config/config.json
    spatial_config_path = input_dir / "config.json"
    if not spatial_config_path.exists():
        repo_root = Path(__file__).resolve().parent.parent.parent
        spatial_config_path = repo_root / "config" / "config.json"

    spatial_analysis = analyze_spatial_intervals(zip_path, grid_specs, spatial_config_path)

    processed_results = {
        "status": "success",
        "grid": {
            **grid_specs,
            "dx": dx, "dy": dy, "dz": dz
        },
        "mask": mask,
        "metrics": {
            "grid_resolution": [nx, ny, nz],
            "total_cells": expected_cells
        },
        **inspection_results,
        "spatial_interval_analysis": spatial_analysis
    }

    logger.info("Flow data processing completed successfully.")
    return processed_results
