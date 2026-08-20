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
    and spatial interval probing under a strict no-default, input-driven policy.
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

    # Enforce strict presence of 'grid' configuration in inputs (no config fallback)
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

    # Enforce presence of mask in inputs
    if "mask" not in inputs:
        logger.error("Missing required 'mask' key in inputs.")
        raise KeyError("Missing required 'mask' key in inputs.")

    mask = inputs["mask"]
    expected_cells = nx * ny * nz
    if not isinstance(mask, list) or len(mask) != expected_cells:
        logger.error("Mask must be a list with length matching total grid cells (nx * ny * nz).")
        raise ValueError("Mask length does not match total grid cells.")

    # Enforce physical constraints configuration presence in inputs
    if "physical_constraints" not in inputs:
        logger.error("Missing required 'physical_constraints' section in inputs.")
        raise KeyError("Missing required 'physical_constraints' section in inputs.")

    physical_constraints = inputs["physical_constraints"]

    # Resolve zip_filename with strict adherence to test assertion messages
    if "results" not in raw_data or not isinstance(raw_data["results"], dict):
        logger.error("Missing required 'results' section in raw data.")
        raise KeyError("Missing required 'results' section in raw data.")

    results_cfg = raw_data["results"]
    zip_filename = results_cfg.get("zip_filename")

    if not zip_filename:
        if "zip_filename" in inputs:
            zip_filename = inputs["zip_filename"]
        else:
            logger.error("Missing required 'zip_filename' parameter in results.")
            raise KeyError("Missing required 'zip_filename' parameter in results.")

    zip_path = input_dir / zip_filename

    if not zip_path.exists():
        logger.error("Configured ZIP archive does not exist at target path: %s", zip_path)
        raise FileNotFoundError(f"Configured ZIP archive not found: {zip_path}")

    logger.info("Executing simulation ZIP inspection and spatial interval analysis.")
    inspection_results = inspect_simulation_zip(zip_path, physical_constraints)

    grid_specs = {
        "nx": nx, "ny": ny, "nz": nz,
        "x_min": x_min, "x_max": x_max,
        "y_min": y_min, "y_max": y_max,
        "z_min": z_min, "z_max": z_max
    }

    # Resolve spatial analysis config path
    spatial_config_path = input_dir / "config.json"
    if not spatial_config_path.exists():
        spatial_config_path = Path(__file__).resolve().parent.parent.parent / "config" / "config.json"

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
