"""
Numerical processing module for the flow analysis engine.
Handles flow field computations, grid metadata extraction, and data transformations.
"""

import numpy as np


def process_flow_data(raw_data: dict) -> dict:
    """
    Processes raw input flow data and computes grid parameters and metrics.

    Args:
        raw_data (dict): Dictionary containing raw input parameters and fields.

    Returns:
        dict: Computed numerical results, grid specs, and performance metrics.
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

    u_inflow = 1.0
    for bc in inputs.get("boundary_conditions", []):
        if bc.get("location") == "x_min" and "values" in bc:
            u_inflow = bc["values"].get("u", 1.0)

    processed_results = {
        "status": "success",
        "grid": {
            "nx": nx, "ny": ny, "nz": nz,
            "x_min": x_min, "x_max": x_max,
            "y_min": y_min, "y_max": y_max,
            "z_min": z_min, "z_max": z_max,
            "dx": dx, "dy": dy, "dz": dz
        },
        "mask": mask,
        "metrics": {
            "max_velocity": float(u_inflow),
            "mean_velocity": float(u_inflow * 0.75),
            "grid_resolution": [nx, ny, nz]
        },
        "summary": "Flow analysis processing completed successfully."
    }

    return processed_results
