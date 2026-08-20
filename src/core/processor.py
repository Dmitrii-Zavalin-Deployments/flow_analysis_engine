"""
Numerical processing module for coordinate grid computation and zip inspection coordination.
"""

from pathlib import Path
from src.core.zip_inspector import inspect_simulation_zip
from src.core.spatial_probe import analyze_spatial_intervals


def process_flow_data(raw_data: dict, input_dir: Path | str = None) -> dict:
    """
    Processes flow grid configurations, invokes zip inspection, boundary verification,
    and config-driven spatial interval probing.
    """
    inputs = raw_data.get("inputs", raw_data)
    grid_cfg = inputs.get("grid", {})
    
    nx = int(grid_cfg.get("nx", 3))
    ny = int(grid_cfg.get("ny", 3))
    nz = int(grid_cfg.get("nz", 3))

    x_min = float(grid_cfg.get("x_min", 0.0))
    x_max = float(grid_cfg.get("x_max", 3.0))
    y_min = float(grid_cfg.get("y_min", 0.0))
    y_max = float(grid_cfg.get("y_max", 3.0))
    z_min = float(grid_cfg.get("z_min", 0.0))
    z_max = float(grid_cfg.get("z_max", 3.0))

    dx = (x_max - x_min) / nx if nx > 0 else 1.0
    dy = (y_max - y_min) / ny if ny > 0 else 1.0
    dz = (z_max - z_min) / nz if nz > 0 else 1.0

    mask = inputs.get("mask", [0] * (nx * ny * nz))
    physical_constraints = inputs.get("physical_constraints", {})

    # Dynamic Discovery of ZIP archive
    zip_filename = inputs.get("zip_filename")
    inspection_results = {}
    spatial_analysis = {}

    grid_specs = {
        "nx": nx, "ny": ny, "nz": nz,
        "x_min": x_min, "x_max": x_max,
        "y_min": y_min, "y_max": y_max,
        "z_min": z_min, "z_max": z_max
    }

    if input_dir and zip_filename:
        zip_path = Path(input_dir) / zip_filename
        if zip_path.exists():
            inspection_results = inspect_simulation_zip(zip_path, physical_constraints)
            spatial_analysis = analyze_spatial_intervals(zip_path, grid_specs)
    elif zip_filename and Path(zip_filename).exists():
        zip_path = Path(zip_filename)
        inspection_results = inspect_simulation_zip(zip_path, physical_constraints)
        spatial_analysis = analyze_spatial_intervals(zip_path, grid_specs)
    else:
        if input_dir:
            zips = list(Path(input_dir).glob("*.zip"))
            if zips:
                zip_path = zips[0]
                inspection_results = inspect_simulation_zip(zip_path, physical_constraints)
                spatial_analysis = analyze_spatial_intervals(zip_path, grid_specs)

    processed_results = {
        "status": "success",
        "grid": {
            **grid_specs,
            "dx": dx, "dy": dy, "dz": dz
        },
        "mask": mask,
        "metrics": {
            "grid_resolution": [nx, ny, nz],
            "total_cells": nx * ny * nz
        },
        **inspection_results,
        "spatial_interval_analysis": spatial_analysis
    }

    return processed_results
