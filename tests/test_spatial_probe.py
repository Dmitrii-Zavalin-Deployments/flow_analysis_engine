"""
Literate Test Codex: Spatial Probe Module Validation
===================================================
This test suite provides comprehensive narratives verifying the spatial probe
module, including configuration loading, coordinate interval slicing, in-memory
NumPy array dimension transformations, and strict error resilience under the no-default policy.
"""

import io
import json
import zipfile
from pathlib import Path
import numpy as np
import pytest

from src.core.spatial_probe import load_spatial_config, analyze_spatial_intervals


# ==============================================================================
# Scenario 1: Spatial Configuration Loading - Missing File Handling
# ==============================================================================
# When loading a spatial configuration file from a path that does not exist on disk,
# the system must catch the filesystem error and raise a FileNotFoundError.

def test_load_spatial_config_file_not_found(tmp_path):
    # We specify a non-existent configuration path.
    missing_config = tmp_path / "non_existent_config.json"

    # We assert that attempting to load this file raises a FileNotFoundError.
    with pytest.raises(FileNotFoundError, match="Spatial config file not found"):
        load_spatial_config(missing_config)


# ==============================================================================
# Scenario 2: Spatial Configuration Loading - Malformed JSON Handling
# ==============================================================================
# If the spatial configuration file contains invalid JSON syntax, the parser
# must catch the decoding error and raise a ValueError.

def test_load_spatial_config_invalid_json(tmp_path):
    # We write malformed JSON data to a temporary config file.
    bad_config = tmp_path / "bad_config.json"
    bad_config.write_text("{ invalid json structure")

    # We assert that a ValueError is raised detailing the decoding failure.
    with pytest.raises(ValueError, match="Failed to decode JSON from spatial config file"):
        load_spatial_config(bad_config)


# ==============================================================================
# Scenario 3: Spatial Analysis - Missing Simulation ZIP Archive
# ==============================================================================
# When the target simulation ZIP archive does not exist on disk, spatial
# analysis must abort and raise a FileNotFoundError.

def test_analyze_spatial_intervals_zip_not_found(tmp_path):
    missing_zip = tmp_path / "missing_sim.zip"
    valid_config = tmp_path / "config.json"
    valid_config.write_text('{"spatial_domain": {"x_range": [0, 1], "y_range": [0, 1], "z_range": [0, 1]}}')
    grid_cfg = {"nx": 2, "ny": 2, "nz": 2, "x_min": 0, "x_max": 2, "y_min": 0, "y_max": 2, "z_min": 0, "z_max": 2}

    # We assert that a FileNotFoundError is raised for the missing archive.
    with pytest.raises(FileNotFoundError, match="Target ZIP archive not found"):
        analyze_spatial_intervals(missing_zip, grid_cfg, valid_config)


# ==============================================================================
# Scenario 4: Enforcing No-Default Policy on Configuration Path
# ==============================================================================
# Under the strict no-default policy, passing None as the config path must
# immediately trigger a configuration ValueError.

def test_analyze_spatial_intervals_config_none(tmp_path):
    dummy_zip = tmp_path / "sim.zip"
    with zipfile.ZipFile(dummy_zip, "w") as zf:
        zf.writestr("u.npy", np.zeros((2, 2, 2)).tobytes())

    grid_cfg = {"nx": 2, "ny": 2, "nz": 2, "x_min": 0, "x_max": 2, "y_min": 0, "y_max": 2, "z_min": 0, "z_max": 2}

    # We assert that passing None raises a ValueError.
    with pytest.raises(ValueError, match="Spatial config path must be explicitly provided"):
        analyze_spatial_intervals(dummy_zip, grid_cfg, None)


# ==============================================================================
# Scenario 5: Grid Parameter Validation (KeyError and ValueError)
# ==============================================================================
# Grid configurations missing required keys or containing invalid type conversions
# must raise explicit KeyError or ValueError exceptions.

def test_analyze_spatial_intervals_grid_validation(tmp_path):
    valid_config = tmp_path / "config.json"
    valid_config.write_text('{"spatial_domain": {"x_range": [0, 1], "y_range": [0, 1], "z_range": [0, 1]}}')
    
    dummy_zip = tmp_path / "sim.zip"
    with zipfile.ZipFile(dummy_zip, "w") as zf:
        zf.writestr("u.npy", np.zeros((2, 2, 2)).tobytes())

    # Test missing grid key (KeyError)
    incomplete_grid = {"nx": 2, "ny": 2}
    with pytest.raises(KeyError, match="Missing required grid parameter"):
        analyze_spatial_intervals(dummy_zip, incomplete_grid, valid_config)

    # Test invalid type value (ValueError)
    invalid_type_grid = {
        "nx": "bad_type", "ny": 2, "nz": 2,
        "x_min": 0.0, "x_max": 2.0,
        "y_min": 0.0, "y_max": 2.0,
        "z_min": 0.0, "z_max": 2.0
    }
    with pytest.raises(ValueError, match="Invalid grid parameter value"):
        analyze_spatial_intervals(dummy_zip, invalid_type_grid, valid_config)

    # Test non-positive dimensions (ValueError)
    zero_dim_grid = {
        "nx": 0, "ny": 2, "nz": 2,
        "x_min": 0.0, "x_max": 2.0,
        "y_min": 0.0, "y_max": 2.0,
        "z_min": 0.0, "z_max": 2.0
    }
    with pytest.raises(ValueError, match="Grid dimensions.*must be strictly greater than zero"):
        analyze_spatial_intervals(dummy_zip, zero_dim_grid, valid_config)


# ==============================================================================
# Scenario 6: Configuration Schema Variants and Range Fallbacks
# ==============================================================================
# The spatial probe supports multiple configuration keys ('spatial_domain',
# 'spatial', 'intervals', and 'grid_bounds' fallbacks). We verify each variant
# and error out when range keys are completely missing.

def test_analyze_spatial_intervals_config_variants(tmp_path):
    dummy_zip = tmp_path / "sim.zip"
    with zipfile.ZipFile(dummy_zip, "w") as zf:
        zf.writestr("u.npy", np.ones((2, 2, 2)).tobytes())

    grid_cfg = {"nx": 2, "ny": 2, "nz": 2, "x_min": 0.0, "x_max": 2.0, "y_min": 0.0, "y_max": 2.0, "z_min": 0.0, "z_max": 2.0}

    # 1. Test 'spatial' nesting key
    cfg_spatial = tmp_path / "spatial.json"
    cfg_spatial.write_text(json.dumps({"spatial": {"x_range": [0, 2], "y_range": [0, 2], "z_range": [0, 2]}}))
    res1 = analyze_spatial_intervals(dummy_zip, grid_cfg, cfg_spatial)
    assert "coordinate_bounds" in res1

    # 2. Test 'intervals' nesting key
    cfg_intervals = tmp_path / "intervals.json"
    cfg_intervals.write_text(json.dumps({"intervals": {"x_range": [0, 2], "y_range": [0, 2], "z_range": [0, 2]}}))
    res2 = analyze_spatial_intervals(dummy_zip, grid_cfg, cfg_intervals)
    assert "coordinate_bounds" in res2

    # 3. Test 'grid_bounds' fallback mechanism
    cfg_bounds = tmp_path / "bounds.json"
    cfg_bounds.write_text(json.dumps({"grid_bounds": [0, 2, 0, 2, 0, 2]}))
    res3 = analyze_spatial_intervals(dummy_zip, grid_cfg, cfg_bounds)
    assert res3["coordinate_bounds"]["x_range"] == [0, 2]

    # 4. Test missing required range keys (KeyError)
    cfg_missing = tmp_path / "missing_ranges.json"
    cfg_missing.write_text(json.dumps({"spatial_domain": {"x_range": [0, 2]}}))
    with pytest.raises(KeyError, match="Missing required range key"):
        analyze_spatial_intervals(dummy_zip, grid_cfg, cfg_missing)


# ==============================================================================
# Scenario 7: Array Shape Transformations and Dimension Verification
# ==============================================================================
# The spatial probe handles different NumPy array shapes stored inside the archive:
# 1. Archives with no .npy files (warning check).
# 2. 1D flattened arrays reshaped using Fortran order ('F').
# 3. 4D vector arrays converted via vector magnitude norms.
# 4. Unsupported array dimensions (raising ValueError).

def test_analyze_spatial_intervals_array_processing(tmp_path):
    grid_cfg = {"nx": 2, "ny": 2, "nz": 2, "x_min": 0.0, "x_max": 2.0, "y_min": 0.0, "y_max": 2.0, "z_min": 0.0, "z_max": 2.0}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"spatial_domain": {"x_range": [0, 2], "y_range": [0, 2], "z_range": [0, 2]}}))

    # Case A: ZIP archive with no .npy files
    empty_zip = tmp_path / "empty.zip"
    with zipfile.ZipFile(empty_zip, "w") as zf:
        zf.writestr("readme.txt", b"No npy files here")
    res_empty = analyze_spatial_intervals(empty_zip, grid_cfg, config_path)
    assert res_empty["field_interval_statistics"] == {}

    # Case B: Archive with 1D array, 4D vector arrays, and invalid 2D array
    complex_zip = tmp_path / "complex.zip"
    with zipfile.ZipFile(complex_zip, "w") as zf:
        # 1D array (size 8 = 2*2*2)
        arr_1d = np.arange(8, dtype=float)
        zf.writestr("field_1d.npy", arr_1d.tobytes())

        # 4D vector array (shape (3, nx, ny, nz) -> axis=0 norm)
        arr_4d_0 = np.ones((3, 2, 2, 2), dtype=float)
        zf.writestr("vector_0.npy", arr_4d_0.tobytes())

        # 4D vector array (shape (nx, ny, nz, 3) -> axis=-1 norm)
        arr_4d_last = np.ones((2, 2, 2, 3), dtype=float)
        zf.writestr("vector_last.npy", arr_4d_last.tobytes())

        # Unsupported 2D array
        arr_2d = np.ones((2, 2), dtype=float)
        zf.writestr("bad_2d.npy", arr_2d.tobytes())

    # Executing analysis and asserting that unsupported 2D arrays trigger ValueError.
    with pytest.raises(ValueError, match="has unsupported dimensions"):
        analyze_spatial_intervals(complex_zip, grid_cfg, config_path)
