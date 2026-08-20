"""
Literate Test Codex: ZIP Field Renderer Module Validation
=========================================================
This test suite provides comprehensive narratives verifying 1D/4D field data 
normalization, config-driven grid bounds resolution, missing config file handling, 
missing configuration keys, non-existent ZIP archives, empty archive handling, 
and non-3D array dimension inference.
"""

import io
import json
import zipfile

import numpy as np
import pytest

from src.visualization.zip_field_renderer import (
    process_field_data,
    render_fields_from_zip,
)

# ==============================================================================
# Scenario 1: Normalizing 1D Field Arrays
# ==============================================================================
# When field data is provided as a flat 1D array, process_field_data reshapes it 
# into a 3D scalar grid of shape (nx, ny, nz) using Fortran-style ordering.

def test_process_field_data_1d():
    # We create a flat 1D array representing 8 grid elements (2x2x2).
    flat_data = np.arange(8, dtype=float)
    reshaped = process_field_data(flat_data, 2, 2, 2)

    # Asserting correct 3D shape and value mapping.
    assert reshaped.shape == (2, 2, 2)
    assert reshaped[0, 0, 0] == 0.0
    assert reshaped[1, 1, 1] == 7.0


# ==============================================================================
# Scenario 2: Processing 4D Vector Fields ((3, nx, ny, nz) and (nx, ny, nz, 3))
# ==============================================================================
# For 4D vector fields representing velocity components (u, v, w), we compute the 
# Euclidean norm along the component axis to yield a 3D scalar magnitude field.

def test_process_field_data_4d_vector_fields():
    # Case A: Shape (3, nx, ny, nz)
    vec_data_a = np.ones((3, 2, 2, 2), dtype=float)
    scalar_a = process_field_data(vec_data_a, 2, 2, 2)
    # The norm of [1, 1, 1] is sqrt(1^2 + 1^2 + 1^2) = sqrt(3) ~= 1.73205
    assert scalar_a.shape == (2, 2, 2)
    assert abs(scalar_a[0, 0, 0] - np.sqrt(3.0)) < 1e-6

    # Case B: Shape (nx, ny, nz, 3)
    vec_data_b = np.full((2, 2, 2, 3), 2.0, dtype=float)
    scalar_b = process_field_data(vec_data_b, 2, 2, 2)
    # The norm of [2, 2, 2] is sqrt(2^2 + 2^2 + 2^2) = sqrt(12) ~= 3.4641
    assert scalar_b.shape == (2, 2, 2)
    assert abs(scalar_b[0, 0, 0] - np.sqrt(12.0)) < 1e-6


# ==============================================================================
# Scenario 3: Config-Driven Grid Bounds Resolution and Missing Config File
# ==============================================================================
# When grid_bounds is not explicitly provided, the renderer attempts to load 
# config.json from the repository root or the output directory. If absent, it raises FileNotFoundError.

def test_render_fields_missing_config_file(tmp_path):
    zip_path = tmp_path / "dummy.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        pass

    # Asserting that FileNotFoundError is raised when config.json cannot be found.
    with pytest.raises(FileNotFoundError, match="Configuration file for grid_bounds not found"):
        render_fields_from_zip(zip_path, tmp_path, grid_bounds=None)


# ==============================================================================
# Scenario 4: Loading Grid Bounds from Output Directory Config
# ==============================================================================
# If config.json is present directly inside the output directory, the renderer 
# successfully loads grid bounds from it.

def test_render_fields_config_in_output_dir(tmp_path):
    # We place config.json in the output directory.
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "grid_bounds": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    }))

    zip_path = tmp_path / "dummy.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        # Empty zip with no npy files to trigger safe return
        zf.writestr("readme.txt", b"no npy")

    # Executing renderer; should successfully locate config in output_dir and return empty list.
    pngs = render_fields_from_zip(zip_path, tmp_path, grid_bounds=None)
    assert pngs == []


# ==============================================================================
# Scenario 5: Missing 'grid_bounds' Key in Configuration File
# ==============================================================================
# If config.json exists but lacks the top-level 'grid_bounds' key, the renderer 
# must raise a KeyError.

def test_render_fields_missing_grid_bounds_key(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"wrong_key": [0, 1, 0, 1, 0, 1]}))

    zip_path = tmp_path / "dummy.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        pass

    # Asserting that a KeyError is raised for the missing key.
    with pytest.raises(KeyError, match="'grid_bounds' top-level key not found"):
        render_fields_from_zip(zip_path, tmp_path, grid_bounds=None)


# ==============================================================================
# Scenario 6: Non-Existent Target ZIP Archive Handling
# ==============================================================================
# If the target ZIP archive file does not exist on disk, the renderer raises 
# a FileNotFoundError.

def test_render_fields_zip_not_found(tmp_path):
    missing_zip = tmp_path / "non_existent.zip"
    explicit_bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)

    # Asserting that missing ZIP raises FileNotFoundError.
    with pytest.raises(FileNotFoundError, match="Target ZIP archive not found"):
        render_fields_from_zip(missing_zip, tmp_path, grid_bounds=explicit_bounds)


# ==============================================================================
# Scenario 7: ZIP Archive Lacking .npy Files
# ==============================================================================
# When a valid ZIP archive contains no .npy field files, the renderer logs a warning 
# and returns an empty list of generated paths.

def test_render_fields_no_npy_in_zip(tmp_path):
    empty_zip = tmp_path / "empty.zip"
    with zipfile.ZipFile(empty_zip, "w") as zf:
        zf.writestr("notes.txt", b"no data")

    explicit_bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
    pngs = render_fields_from_zip(empty_zip, tmp_path, grid_bounds=explicit_bounds)
    assert pngs == []


# ==============================================================================
# Scenario 8: Non-3D Array Shape Handling (In-Memory Dimension Inference)
# ==============================================================================
# When an array stored in the ZIP archive has a non-3D shape (e.g. 2D array), 
# the renderer infers the cubic grid dimension via total element count.

def test_render_fields_non_3d_array_inference(tmp_path):
    sim_zip = tmp_path / "sim_2d.zip"
    with zipfile.ZipFile(sim_zip, "w") as zf:
        # We store a 2D array with 8 elements (e.g., shape 4x2) to trigger dimension inference
        arr_2d = np.ones((4, 2), dtype=float)
        bio = io.BytesIO()
        np.save(bio, arr_2d)
        zf.writestr("field_2d.npy", bio.getvalue())

    explicit_bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
    pngs = render_fields_from_zip(sim_zip, tmp_path, grid_bounds=explicit_bounds)
    
    # Verifying that the snapshot was successfully generated
    assert len(pngs) == 1
    assert pngs[0].name == "field_2d_3d_verification.png"
