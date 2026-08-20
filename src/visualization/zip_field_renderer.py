"""
In-Memory Zip Field Visualization Engine.
Reads .npy simulation field arrays directly from a ZIP archive without extracting
them to disk, generating 3D colormapped voxel visualizations with black borders.
"""

import io
import json
import logging
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

# Configure structured module logger
logger = logging.getLogger("flow_engine.zip_field_renderer")


def process_field_data(data: np.ndarray, nx: int, ny: int, nz: int) -> np.ndarray:
    """
    Normalizes field data dimensions and handles vector fields (e.g. [u, v, w]) 
    and non-3D arrays. Returns a 3D scalar array of shape (nx, ny, nz).
    """
    if data.ndim != 3 and data.ndim != 4:
        if data.size == nx * ny * nz:
            data = data.reshape((nx, ny, nz), order="F")
        else:
            data = np.resize(data, (nx, ny, nz))
    elif data.ndim == 3:
        if data.shape != (nx, ny, nz) and data.size == nx * ny * nz:
            data = data.reshape((nx, ny, nz), order="F")
    elif data.ndim == 4:
        if data.shape[0] == 3 and data.shape[1] == nx:
            data = np.linalg.norm(data, axis=0)
        elif data.shape[-1] == 3:
            data = np.linalg.norm(data, axis=-1)
        else:
            data = np.linalg.norm(data, axis=-1) if data.shape[-1] == 3 else np.linalg.norm(data, axis=0)
        
        if data.shape != (nx, ny, nz) and data.size == nx * ny * nz:
            data = data.reshape((nx, ny, nz), order="F")

    return data


def render_fields_from_zip(
    zip_path: Path | str,
    output_dir: Path | str,
    grid_bounds: tuple[float, float, float, float, float, float] | None = None,
    colormap_name: str = "viridis",
    mask: list[int] | np.ndarray | None = None
) -> list[Path]:
    """
    Inspects a ZIP file, reads all contained .npy field files in-memory,
    and generates matching 3D voxel colormap PNG images under a strict config-driven policy.
    Loads grid_bounds from config.json if not explicitly provided.
    """
    zip_path = Path(zip_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if grid_bounds is None:
        logger.info("Loading grid_bounds from config.json under config-driven policy.")
        config_path = output_dir / "config.json"

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file for grid_bounds not found at: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        if "grid_bounds" in cfg:
            gb = cfg["grid_bounds"]
            grid_bounds = tuple(float(v) for v in gb)
        else:
            raise KeyError("'grid_bounds' top-level key not found in config.json.")

    x_min, x_max, y_min, y_max, z_min, z_max = grid_bounds
    generated_pngs: list[Path] = []

    if not zip_path.is_file():
        logger.error("Target ZIP archive not found at target path: %s", zip_path)
        raise FileNotFoundError(f"Target ZIP archive not found: {zip_path}")

    logger.info("Opening ZIP archive for in-memory field rendering: %s", zip_path.name)
    with zipfile.ZipFile(zip_path, "r") as archive:
        npy_files = [f for f in archive.namelist() if f.endswith(".npy")]

        if not npy_files:
            logger.warning("No .npy files found inside ZIP archive: %s", zip_path.name)
            return generated_pngs

        logger.info("Found %d field file(s) inside %s", len(npy_files), zip_path.name)

        for file_name in npy_files:
            with archive.open(file_name) as npy_stream:
                field_array = np.load(io.BytesIO(npy_stream.read()), allow_pickle=True)

            if field_array.ndim == 3:
                nx, ny, nz = field_array.shape
            else:
                total_elements = field_array.shape[0] if field_array.ndim == 1 else field_array.size
                n_side = round(total_elements ** (1 / 3))
                nx, ny, nz = n_side, n_side, n_side

            scalar_field = process_field_data(field_array, nx, ny, nz)

            x_edges = np.linspace(x_min, x_max, nx + 1)
            y_edges = np.linspace(y_min, y_max, ny + 1)
            z_edges = np.linspace(z_min, z_max, nz + 1)
            X, Y, Z = np.meshgrid(x_edges, y_edges, z_edges, indexing="ij")

            # Separate fluid vs obstacle (val=0 and val=-1) using the mask
            if mask is not None:
                mask_arr = np.array(mask).reshape((nx, ny, nz), order="F")
                fluid_voxels = (mask_arr == 1)
                obstacle_voxels = (mask_arr <= 0)  # Combines both solid (0) and wall (-1) into light-grey cage
            else:
                fluid_voxels = np.ones((nx, ny, nz), dtype=bool)
                obstacle_voxels = np.zeros((nx, ny, nz), dtype=bool)

            # Normalize colormap strictly across fluid cells for maximum visual contrast
            if np.any(fluid_voxels):
                vmin, vmax = float(np.min(scalar_field[fluid_voxels])), float(np.max(scalar_field[fluid_voxels]))
            else:
                vmin, vmax = float(np.min(scalar_field)), float(np.max(scalar_field))

            if np.isclose(vmin, vmax):
                vmax = vmin + 1e-6

            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
            cmap = matplotlib.colormaps[colormap_name]
            
            fluid_colors = cmap(norm(scalar_field))
            fluid_colors[..., 3] = 0.85  # Fluid opacity

            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection="3d")
            
            # Enforce true physical proportions for anisotropic grids
            ax.set_box_aspect((x_max - x_min, y_max - y_min, z_max - z_min))

            # 1. Render Obstacle Structural Container (mask <= 0) as light grey transparent with visible borders
            if np.any(obstacle_voxels):
                obs_colors = np.zeros((nx, ny, nz, 4), dtype=float)
                obs_colors[obstacle_voxels] = [0.85, 0.85, 0.85, 0.15]  # Light grey, 15% opacity
                ax.voxels(
                    X, Y, Z, obstacle_voxels,
                    facecolors=obs_colors,
                    edgecolors=(0.5, 0.5, 0.5, 0.4),  # Visible light-grey cell edges
                    linewidth=0.5
                )

            # 2. Render Active Fluid Cells (mask == 1) with colormap
            if np.any(fluid_voxels):
                ax.voxels(
                    X, Y, Z, fluid_voxels,
                    facecolors=fluid_colors,
                    edgecolors="k",
                    linewidth=0.7
                )

            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            ax.set_zlim(z_min, z_max)

            display_title = Path(file_name).stem
            ax.set_title(f"3D Field Distribution: {display_title}", fontsize=12, fontweight="bold", pad=15)
            ax.set_xlabel("X Coordinate", labelpad=8)
            ax.set_ylabel("Y Coordinate", labelpad=8)
            ax.set_zlabel("Z Coordinate", labelpad=10)

            mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
            mappable.set_array(scalar_field)
            cbar = fig.colorbar(mappable, ax=ax, shrink=0.65, aspect=12, pad=0.1)
            cbar.set_label("Field Magnitude / Value", rotation=270, labelpad=18, fontweight="bold")

            output_png_name = f"{display_title}_3d_verification.png"
            output_path = output_dir / output_png_name
            plt.savefig(output_path, dpi=150, bbox_inches="tight", pad_inches=0.3)
            plt.close(fig)

            logger.info("Generated 3D field snapshot: %s", output_path.name)
            generated_pngs.append(output_path)

    return generated_pngs
