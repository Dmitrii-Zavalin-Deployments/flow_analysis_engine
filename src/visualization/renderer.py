"""
Headless rendering and visualization module using matplotlib (Agg backend)
to generate diagnostic 3D voxel mask snapshots for the flow analysis engine.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


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


def render_visualization(raw_data: dict, processed_results: dict, output_dir: Path) -> None:
    """
    Generates 3D voxel mask visualization matching grid dimensions and cell classification.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    grid_info = processed_results.get("grid", {})
    nx = grid_info.get("nx", 3)
    ny = grid_info.get("ny", 3)
    nz = grid_info.get("nz", 3)
    
    x_min, x_max = grid_info.get("x_min", 0.0), grid_info.get("x_max", 3.0)
    y_min, y_max = grid_info.get("y_min", 0.0), grid_info.get("y_max", 3.0)
    z_min, z_max = grid_info.get("z_min", 0.0), grid_info.get("z_max", 3.0)

    mask = processed_results.get("mask", [0] * (nx * ny * nz))

    # Initialize 3D voxel matrices (filled=True, colors=RGBA)
    voxels = np.ones((nx, ny, nz), dtype=bool)
    colors = np.empty((nx, ny, nz, 4), dtype=float)

    # RGBA color definition with transparency
    COLOR_SOLID = np.array([0.7, 0.7, 0.7, 0.4])       # Transparent Light Grey
    COLOR_FLUID = np.array([0.12, 0.56, 1.0, 0.15])    # Transparent Blue
    COLOR_WALL  = np.array([0.0, 0.0, 0.55, 0.25])     # Transparent Dark Blue

    total_cells = nx * ny * nz
    for idx in range(min(len(mask), total_cells)):
        i, j, k = get_coords_from_index(idx, nx, ny)

        is_boundary = (i == 0 or i == nx - 1 or j == 0 or j == ny - 1 or k == 0 or k == nz - 1)
        is_solid = (mask[idx] == 1)

        if is_solid:
            colors[i, j, k] = COLOR_SOLID
        elif is_boundary:
            colors[i, j, k] = COLOR_WALL
        else:
            colors[i, j, k] = COLOR_FLUID

    # 1. Render Voxel Mask Snapshot
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Define physical voxel grid boundaries
    x_edges = np.linspace(x_min, x_max, nx + 1)
    y_edges = np.linspace(y_min, y_max, ny + 1)
    z_edges = np.linspace(z_min, z_max, nz + 1)

    X, Y, Z = np.meshgrid(x_edges, y_edges, z_edges, indexing="ij")

    ax.voxels(X, Y, Z, voxels, facecolors=colors, edgecolors="k", linewidth=0.3)

    ax.set_title("3D Voxel Mask & Grid Cell Classification", fontsize=12, fontweight="bold")
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.set_zlabel("Z Coordinate")

    # Legend handles
    import matplotlib.patches as mpatches
    legend_handles = [
        mpatches.Patch(color=COLOR_SOLID, label="Solid Obstacle (mask=1)"),
        mpatches.Patch(color=COLOR_FLUID, label="Fluid Cell (mask=0)"),
        mpatches.Patch(color=COLOR_WALL, label="Domain Wall / Boundary")
    ]
    ax.legend(handles=legend_handles, loc="upper right")

    voxel_path = output_dir / "voxel_mask_verification.png"
    plt.savefig(voxel_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"🖼️ Generated 3D Voxel Verification: {voxel_path}")

    # 2. Render Mesh Snapshot
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.voxels(X, Y, Z, voxels, facecolors=[0, 0, 0, 0], edgecolors="blue", linewidth=0.5)
    ax.set_title("Computational Mesh Grid", fontsize=12, fontweight="bold")
    mesh_path = output_dir / "mesh_snapshot.png"
    plt.savefig(mesh_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"🖼️ Generated Mesh Snapshot: {mesh_path}")
