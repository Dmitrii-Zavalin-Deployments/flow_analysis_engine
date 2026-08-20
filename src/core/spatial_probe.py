"""
Spatial Probing Module.
Extracts and computes field metrics (u, v, w, p) across the configured coordinate interval
from in-memory simulation .npy files without disk extraction.
"""

import io
import json
import zipfile
from pathlib import Path

import numpy as np


def load_spatial_config(config_path: Path | str) -> dict:
    """Loads spatial coordinate ranges from config.json."""
    config_path = Path(config_path)
    if not config_path.exists():
        return {
            "x_range": [0.0, 3.0],
            "y_range": [0.0, 3.0],
            "z_range": [0.0, 3.0]
        }
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_spatial_intervals(
    zip_path: Path | str,
    grid_cfg: dict,
    config_path: Path | str = "config/config.json"
) -> dict:
    """
    Slices u, v, w, and p fields across the configured spatial coordinate interval
    and computes localized statistics.
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        return {}

    interval_cfg = load_spatial_config(config_path)

    nx = int(grid_cfg.get("nx", 3))
    ny = int(grid_cfg.get("ny", 3))
    nz = int(grid_cfg.get("nz", 3))

    x_min, x_max = float(grid_cfg.get("x_min", 0.0)), float(grid_cfg.get("x_max", 3.0))
    y_min, y_max = float(grid_cfg.get("y_min", 0.0)), float(grid_cfg.get("y_max", 3.0))
    z_min, z_max = float(grid_cfg.get("z_min", 0.0)), float(grid_cfg.get("z_max", 3.0))

    dx = (x_max - x_min) / nx if nx > 0 else 1.0
    dy = (y_max - y_min) / ny if ny > 0 else 1.0
    dz = (z_max - z_min) / nz if nz > 0 else 1.0

    x_rng = interval_cfg.get("x_range", [x_min, x_max])
    y_rng = interval_cfg.get("y_range", [y_min, y_max])
    z_rng = interval_cfg.get("z_range", [z_min, z_max])

    # Convert physical coordinates to array index slices
    i_start = max(0, int((x_rng[0] - x_min) / dx))
    i_end = min(nx, int(np.ceil((x_rng[1] - x_min) / dx)))
    j_start = max(0, int((y_rng[0] - y_min) / dy))
    j_end = min(ny, int(np.ceil((y_rng[1] - y_min) / dy)))
    k_start = max(0, int((z_rng[0] - z_min) / dz))
    k_end = min(nz, int(np.ceil((z_rng[1] - z_min) / dz)))

    zone_stats = {}

    with zipfile.ZipFile(zip_path, "r") as archive:
        npy_files = [name for name in archive.namelist() if name.endswith(".npy")]
        
        for name in npy_files:
            with archive.open(name) as f:
                arr = np.load(io.BytesIO(f.read()))
                if arr.ndim == 1:
                    arr = arr.reshape((nx, ny, nz), order="F")
                
                sub_arr = arr[i_start:i_end, j_start:j_end, k_start:k_end]
                if sub_arr.size > 0:
                    zone_stats[name] = {
                        "min": float(sub_arr.min()),
                        "max": float(sub_arr.max()),
                        "mean": float(sub_arr.mean()),
                        "active_cells": int(sub_arr.size)
                    }

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
