"""
Spatial Probing Module.
Extracts and computes field metrics (u, v, w, p) across the configured coordinate interval
from in-memory simulation .npy files without disk extraction.
"""

import io
import json
import logging
import zipfile
from pathlib import Path

import numpy as np

# Configure structured module logger
logger = logging.getLogger("flow_engine.spatial_probe")


def load_spatial_config(config_path: Path | str) -> dict:
    """
    Loads spatial coordinate ranges from config file.
    Adheres to the strict no-default policy (raises FileNotFoundError if missing).
    """
    config_path = Path(config_path)
    if not config_path.is_file():
        logger.error("Spatial config file not found or invalid: %s", config_path)
        raise FileNotFoundError(f"Spatial config file not found: {config_path}")

    logger.info("Loading spatial configuration from %s", config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON from spatial config file: %s", e)
            raise ValueError(f"Failed to decode JSON from spatial config file: {e}") from e

    return data


def analyze_spatial_intervals(
    zip_path: Path | str,
    grid_cfg: dict,
    config_path: Path | str
) -> dict:
    """
    Slices u, v, w, and p fields across the configured spatial coordinate interval
    and computes localized statistics under a strict no-default policy.
    """
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        logger.error("Target ZIP archive not found for spatial analysis: %s", zip_path)
        raise FileNotFoundError(f"Target ZIP archive not found: {zip_path}")

    if config_path is None:
        logger.error("Spatial config path was not provided (no-default policy enforced).")
        raise ValueError("Spatial config path must be explicitly provided.")

    interval_cfg = load_spatial_config(config_path)

    # Extract required grid parameters (no-default policy)
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
        logger.error("Missing required grid parameter for spatial analysis: %s", e)
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

    # Extract required range limits from spatial config (no-default policy)
    try:
        x_rng = interval_cfg["x_range"]
        y_rng = interval_cfg["y_range"]
        z_rng = interval_cfg["z_range"]
    except KeyError as e:
        logger.error("Missing required range key in spatial configuration: %s", e)
        raise KeyError(f"Missing required range key in spatial configuration: {e}") from e

    # Convert physical coordinates to array index slices
    i_start = max(0, int((x_rng[0] - x_min) / dx))
    i_end = min(nx, int(np.ceil((x_rng[1] - x_min) / dx)))
    j_start = max(0, int((y_rng[0] - y_min) / dy))
    j_end = min(ny, int(np.ceil((y_rng[1] - y_min) / dy)))
    k_start = max(0, int((z_rng[0] - z_min) / dz))
    k_end = min(nz, int(np.ceil((z_rng[1] - z_min) / dz)))

    zone_stats = {}

    logger.info("Executing spatial interval slicing and statistics computation.")
    with zipfile.ZipFile(zip_path, "r") as archive:
        npy_files = [name for name in archive.namelist() if name.endswith(".npy")]

        if not npy_files:
            logger.warning("No .npy files found inside ZIP archive for spatial analysis.")

        for name in npy_files:
            with archive.open(name) as f:
                # Added allow_pickle=True for numpy 2.x compatibility
                arr = np.load(io.BytesIO(f.read()), allow_pickle=True)

                if arr.ndim == 1:
                    arr = arr.reshape((nx, ny, nz), order="F")
                elif arr.ndim == 4:
                    if arr.shape[0] == 3 and arr.shape[1] == nx:
                        arr = np.linalg.norm(arr, axis=0)
                    elif arr.shape[-1] == 3:
                        arr = np.linalg.norm(arr, axis=-1)

                if arr.ndim != 3:
                    logger.error("Array '%s' has unsupported dimensions for spatial slicing: %d", name, arr.ndim)
                    raise ValueError(f"Array '{name}' has unsupported dimensions: {arr.ndim}")

                sub_arr = arr[i_start:i_end, j_start:j_end, k_start:k_end]
                if sub_arr.size > 0:
                    zone_stats[name] = {
                        "min": float(sub_arr.min()),
                        "max": float(sub_arr.max()),
                        "mean": float(sub_arr.mean()),
                        "active_cells": int(sub_arr.size)
                    }

    logger.info("Spatial interval analysis completed successfully.")
    return {
        "coordinate_bounds": {
            "x_range": x_rng,
            "y_range": y_rng,
            "z_range": z_rng
        },
        "index_slices": {
            "i": [i_start, i_end],
            "j": [j_start, j_end],
            "k": [k_start, k_end]
        },
        "field_interval_statistics": zone_stats
    }
