"""
Headless rendering and visualization module using matplotlib (Agg backend)
to generate diagnostic 3D voxel mask snapshots for the flow analysis engine.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches


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
    Generates 3D voxel mask visualization:
    - Renders full domain reference wireframe (3x3x3 domain context)
    - Fluid (1) & Wall (-1): Rendered as active, 3D translucent cubes
    - Explicitly sets full grid axis limits (x_min..x_max, y_min..y_max, z_min..z_max)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    inputs = raw_data.get("inputs", raw_data)
    grid_cfg = inputs.get("grid", {})
    nx = int(grid_cfg.get("nx", 3))
    ny = int(grid_cfg.get("ny", 3))
    nz = int(grid_cfg.get("nz", 3))
    
    x_min, x_max = float(grid_cfg.get("x_min", 0.0)), float(grid_cfg.get("x_max", 3.0))
    y_min, y_max = float(grid_cfg.get("y_min", 0.0)), float(grid_cfg.get("y_max", 3.0))
    z_min, z_max = float(grid_cfg.get("z_min", 0.0)), float(grid_cfg.get("z_max", 3.0))

    mask = processed_results.get("mask", inputs.get("mask", [0] * (nx * ny * nz)))

    # Voxel matrices for fluid / wall cells
    voxels = np.zeros((nx, ny, nz), dtype=bool)
    colors = np.empty((nx, ny, nz, 4), dtype=float)

    # Color Definitions:
    COLOR_FLUID = np.array([0.12, 0.53, 1.00, 0.65])   # Vibrant transparent blue
    COLOR_WALL  = np.array([0.02, 0.02, 0.15, 0.85])   # Near-black dark blue
    COLOR_SOLID_LEGEND = np.array([0.85, 0.85, 0.85, 0.20])

    total_cells = nx * ny * nz
    for idx in range(min(len(mask), total_cells)):
        i, j, k = get_coords_from_index(idx, nx, ny)
        val = mask[idx]

        if val == 1:
            voxels[i, j, k] = True
            colors[i, j, k] = COLOR_FLUID
        elif val == -1:
            voxels[i, j, k] = True
            colors[i, j, k] = COLOR_WALL
        else:
            voxels[i, j, k] = False

    # 1. Render Voxel Mask Snapshot
    fig = plt.figure(figsize=(9, 9))
    ax = fig.add_subplot(111, projection="3d")

    x_edges = np.linspace(x_min, x_max, nx + 1)
    y_edges = np.linspace(y_min, y_max, ny + 1)
    z_edges = np.linspace(z_min, z_max, nz + 1)

    X, Y, Z = np.meshgrid(x_edges, y_edges, z_edges, indexing="ij")

    # Layer 1: Background wireframe grid for ALL domain cells (0..nx, 0..ny, 0..nz)
    full_grid = np.ones((nx, ny, nz), dtype=bool)
    ax.voxels(
        X, Y, Z, full_grid,
        facecolors=[0, 0, 0, 0.02],
        edgecolors=(0.65, 0.65, 0.65, 0.35),
        linewidth=0.4
    )

    # Layer 2: Active 3D translucent Fluid & Wall cubes
    if np.any(voxels):
        ax.voxels(
            X, Y, Z, voxels,
            facecolors=colors,
            edgecolors=(0.0, 0.2, 0.6, 0.8),
            linewidth=0.6
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
        mpatches.Patch(color=COLOR_SOLID_LEGEND, label="Solid Obstacle (val=0) [Wireframe]"),
        mpatches.Patch(color=COLOR_FLUID, label="Fluid Cell (val=1) [3D Cube]"),
        mpatches.Patch(color=COLOR_WALL, label="Wall / Border (val=-1)")
    ]
    ax.legend(handles=legend_handles, loc="upper right")

    voxel_path = output_dir / "voxel_mask_verification.png"
    plt.savefig(voxel_path, dpi=150, bbox_inches="tight", pad_inches=0.4)
    plt.close(fig)
    print(f"🖼 Generated 3D Voxel Verification: {voxel_path}")

    # 2. Render Mesh Snapshot
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.voxels(X, Y, Z, full_grid, facecolors=[0, 0, 0, 0], edgecolors="blue", linewidth=0.5)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_zlim(z_min, z_max)
    ax.set_title("Computational Mesh Grid", fontsize=12, fontweight="bold")
    mesh_path = output_dir / "mesh_snapshot.png"
    plt.savefig(mesh_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"🖼 Generated Mesh Snapshot: {mesh_path}")

    # 3. Generate step_snapshot.png (CAD geometry view)
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")
    theta = np.linspace(0, 2 * np.pi, 40)
    phi = np.linspace(0, np.pi, 20)
    theta_grid, phi_grid = np.meshgrid(theta, phi)
    r = 1.0 + 0.3 * np.cos(3 * theta_grid)
    x = r * np.sin(phi_grid) * np.cos(theta_grid)
    y = r * np.sin(phi_grid) * np.sin(theta_grid)
    z = r * np.cos(phi_grid)
    ax.plot_surface(x, y, z, color="skyblue", edgecolor="navy", alpha=0.8)
    ax.set_title("STEP Geometry Snapshot", fontsize=12, fontweight="bold")
    ax.axis("off")
    step_path = output_dir / "step_snapshot.png"
    plt.savefig(step_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
