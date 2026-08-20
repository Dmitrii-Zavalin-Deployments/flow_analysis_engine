"""
Headless rendering and visualization module using matplotlib (Agg backend)
to generate diagnostic 3D voxel mask snapshots for the flow analysis engine.
"""

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# Configure structured module logger
logger = logging.getLogger("flow_engine.renderer")


def get_coords_from_index(index: int, nx: int, ny: int) -> tuple[int, int, int]:
    """
    SSoT Mapping: Converts flat index back to 3D grid indices (i, j, k).
    Matches grid_math.hpp logic: index = i + nx * j + (nx * ny) * k
    """
    xy_plane = nx * ny
    k = index // xy_plane
    rem = index % xy_plane
    j = rem // nx
    i = rem % nx
    return i, j, k


def render_visualization(raw_data: dict, processed_results: dict, output_dir: Path | str) -> None:
    """
    Generates 3D voxel mask visualization with crisp black perimeter and cell edge lines
    under a strict no-default policy.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing 3D voxel mask and mesh rendering pipeline.")

    # No-default policy: Enforce presence of 'inputs' and 'grid'
    if "inputs" not in raw_data:
        logger.error("Missing required 'inputs' section in raw data.")
        raise KeyError("Missing required 'inputs' section in raw data.")

    inputs = raw_data["inputs"]
    if "grid" not in inputs:
        logger.error("Missing required 'grid' configuration in inputs.")
        raise KeyError("Missing required 'grid' configuration in inputs.")

    grid_cfg = inputs["grid"]

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
        logger.error("Missing required grid parameter for rendering: %s", e)
        raise KeyError(f"Missing required grid parameter: {e}") from e
    except (ValueError, TypeError) as e:
        logger.error("Invalid type or value for grid parameters during rendering: %s", e)
        raise ValueError(f"Invalid grid parameter value: {e}") from e

    if nx <= 0 or ny <= 0 or nz <= 0:
        logger.error("Grid dimensions (nx, ny, nz) must be strictly greater than zero.")
        raise ValueError("Grid dimensions (nx, ny, nz) must be strictly greater than zero.")

    # Retrieve mask from processed_results or inputs (no-default policy)
    if "mask" in processed_results:
        mask = processed_results["mask"]
    elif "mask" in inputs:
        mask = inputs["mask"]
    else:
        logger.error("Missing required 'mask' data for rendering.")
        raise KeyError("Missing required 'mask' data for rendering.")

    expected_cells = nx * ny * nz
    if not isinstance(mask, list) or len(mask) != expected_cells:
        logger.error("Mask must be a list with length matching total grid cells.")
        raise ValueError("Mask length does not match total grid cells.")

    # Voxel matrices for fluid / wall cells
    voxels = np.zeros((nx, ny, nz), dtype=bool)
    colors = np.empty((nx, ny, nz, 4), dtype=float)

    # Color Definitions:
    color_fluid = np.array([0.12, 0.53, 1.00, 0.65])   # Vibrant transparent blue
    color_wall  = np.array([0.02, 0.02, 0.15, 0.85])   # Near-black dark blue
    color_solid_legend = np.array([0.85, 0.85, 0.85, 0.20])

    for idx in range(min(len(mask), expected_cells)):
        i, j, k = get_coords_from_index(idx, nx, ny)
        val = mask[idx]

        if val == 1:
            voxels[i, j, k] = True
            colors[i, j, k] = color_fluid
        elif val == -1:
            voxels[i, j, k] = True
            colors[i, j, k] = color_wall
        else:
            voxels[i, j, k] = False

    # 1. Render Voxel Mask Snapshot
    fig = plt.figure(figsize=(9, 9))
    ax = fig.add_subplot(111, projection="3d")

    x_edges = np.linspace(x_min, x_max, nx + 1)
    y_edges = np.linspace(y_min, y_max, ny + 1)
    z_edges = np.linspace(z_min, z_max, nz + 1)

    X, Y, Z = np.meshgrid(x_edges, y_edges, z_edges, indexing="ij")

    # Layer 1: Background wireframe grid for ALL domain cells with distinct dark edges
    full_grid = np.ones((nx, ny, nz), dtype=bool)
    ax.voxels(
        X, Y, Z, full_grid,
        facecolors=[0, 0, 0, 0.01],
        edgecolors=(0.15, 0.15, 0.15, 0.45),  # Darker gray-black for background wireframe
        linewidth=0.5
    )

    # Layer 2: Active 3D translucent Fluid & Wall cubes with sharp black boundary edges
    if np.any(voxels):
        ax.voxels(
            X, Y, Z, voxels,
            facecolors=colors,
            edgecolors="k",  # Pure black edge lines for maximum model visibility
            linewidth=0.8
        )

    # Force axis bounds to full domain dimensions
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_zlim(z_min, z_max)

    ax.set_title("3D Voxel Mask & Cell Classification (Fluid Cubes & Domain Bounds)", fontsize=11, fontweight="bold", pad=15)
    ax.set_xlabel("X Coordinate", labelpad=10)
    ax.set_ylabel("Y Coordinate", labelpad=10)
    ax.set_zlabel("Z Coordinate", labelpad=12)

    legend_handles = [
        mpatches.Patch(color=color_solid_legend, label="Solid Obstacle (val=0) [Wireframe]"),
        mpatches.Patch(color=color_fluid, label="Fluid Cell (val=1) [3D Cube]"),
        mpatches.Patch(color=color_wall, label="Wall / Border (val=-1)")
    ]
    ax.legend(handles=legend_handles, loc="upper right")

    voxel_path = output_dir / "integration_voxel_verification.png"
    plt.savefig(voxel_path, dpi=150, bbox_inches="tight", pad_inches=0.4)
    plt.close(fig)
    logger.info("Generated 3D Voxel Verification snapshot: %s", voxel_path.name)