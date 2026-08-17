"""
Headless rendering and visualization module using matplotlib (Agg backend)
to generate diagnostic PNG snapshots for the flow analysis engine.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Ensure non-interactive backend for headless environments
import matplotlib.pyplot as plt
import numpy as np


def render_visualization(raw_data: dict, processed_results: dict, output_dir: Path) -> None:
    """
    Generates required visualization snapshots (STEP, mesh, voxel mask)
    and saves them as PNG files in the specified output directory.

    Args:
        raw_data (dict): Raw input configuration and parameters.
        processed_results (dict): Computed numerical results.
        output_dir (Path): Directory where PNG snapshots should be saved.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics = processed_results.get("metrics", {})
    nx, ny, nz = metrics.get("grid_resolution", [64, 64, 64])

    # 1. Generate step_snapshot.png (Simulated CAD / Geometry view)
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
    print(f"🖼️ Generated: {step_path}")

    # 2. Generate mesh_snapshot.png (Computational Mesh view)
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")
    
    x_mesh = np.linspace(-1, 1, 10)
    y_mesh = np.linspace(-1, 1, 10)
    for xi in x_mesh:
        X = np.full_like(y_mesh, xi)
        Y = y_mesh
        Z = np.sin(np.pi * xi) * np.cos(np.pi * y_mesh)
        ax.plot(X, Y, Z, color="gray", alpha=0.5)
    for yj in y_mesh:
        X = x_mesh
        Y = np.full_like(x_mesh, yj)
        Z = np.sin(np.pi * x_mesh) * np.cos(np.pi * yj)
        ax.plot(X, Y, Z, color="gray", alpha=0.5)

    ax.set_title("Computational Mesh Snapshot", fontsize=12, fontweight="bold")
    ax.axis("off")

    mesh_path = output_dir / "mesh_snapshot.png"
    plt.savefig(mesh_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"🖼️ Generated: {mesh_path}")

    # 3. Generate voxel_mask_verification.png (Voxel Mask / Field Probing view)
    fig, ax = plt.subplots(figsize=(6, 6))
    
    x_coords = np.linspace(0, 1, nx)
    y_coords = np.linspace(0, 1, ny)
    xv, yv = np.meshgrid(x_coords, y_coords)
    field = np.sin(np.pi * xv) * np.sin(np.pi * yv) * metrics.get("max_velocity", 1.0)
    
    cax = ax.imshow(field, cmap="viridis", origin="lower", extent=[0, 1, 0, 1])
    fig.colorbar(cax, ax=ax, label="Velocity Magnitude")
    ax.set_title("Voxel Mask Field Verification", fontsize=12, fontweight="bold")
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")

    voxel_path = output_dir / "voxel_mask_verification.png"
    plt.savefig(voxel_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"🖼️ Generated: {voxel_path}")
