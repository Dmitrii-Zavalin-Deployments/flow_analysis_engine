"""
Literate Test Codex: Renderer Module Validation
===============================================
This module provides comprehensive test narratives verifying headless rendering error
pathways, missing inputs and grid parameters, non-positive grid dimensions, missing
mask data, mask length validation, and spatial index coordinate mapping.
"""

import pytest

from src.visualization.renderer import get_coords_from_index, render_visualization

# ==============================================================================
# Scenario 1: Missing 'inputs' Section in Raw Data
# ==============================================================================
# Under the strict no-default policy, raw data missing the 'inputs' dictionary
# must immediately raise a KeyError.

def test_render_visualization_missing_inputs(tmp_path):
    raw_data = {}
    processed_results = {}

    # Asserting that missing inputs raises a KeyError.
    with pytest.raises(KeyError, match="Missing required 'inputs' section"):
        render_visualization(raw_data, processed_results, tmp_path)


# ==============================================================================
# Scenario 2: Missing 'grid' Configuration in Inputs
# ==============================================================================
# If the inputs dictionary lacks the required 'grid' configuration key, rendering
# must abort and raise a KeyError.

def test_render_visualization_missing_grid(tmp_path):
    raw_data = {"inputs": {}}
    processed_results = {}

    # Asserting that missing grid configuration raises a KeyError.
    with pytest.raises(KeyError, match="Missing required 'grid' configuration"):
        render_visualization(raw_data, processed_results, tmp_path)


# ==============================================================================
# Scenario 3: Missing Required Grid Parameters
# ==============================================================================
# Omitting any required grid dimension or coordinate bounds (e.g. 'nz') must
# trigger a KeyError during parameter extraction.

def test_render_visualization_missing_grid_parameter(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 2, "ny": 2,  # 'nz' is missing
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            }
        }
    }
    processed_results = {}

    # Asserting that missing grid parameter raises a KeyError.
    with pytest.raises(KeyError, match="Missing required grid parameter"):
        render_visualization(raw_data, processed_results, tmp_path)


# ==============================================================================
# Scenario 4: Invalid Grid Parameter Types or Values
# ==============================================================================
# Providing non-numeric or malformed values for grid parameters (e.g. string for nx)
# must trigger a ValueError.

def test_render_visualization_invalid_grid_parameter_type(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": "invalid_int", "ny": 2, "nz": 2,
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            }
        }
    }
    processed_results = {}

    # Asserting that invalid grid parameter types raise a ValueError.
    with pytest.raises(ValueError, match="Invalid grid parameter value"):
        render_visualization(raw_data, processed_results, tmp_path)


# ==============================================================================
# Scenario 5: Non-Positive Grid Dimensions
# ==============================================================================
# Grid dimensions (nx, ny, nz) must be strictly greater than zero; non-positive
# values must raise a ValueError.

def test_render_visualization_non_positive_grid_dimensions(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 0, "ny": 2, "nz": 2,  # nx is zero
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            }
        }
    }
    processed_results = {}

    # Asserting that non-positive dimensions raise a ValueError.
    with pytest.raises(ValueError, match="Grid dimensions .* must be strictly greater than zero"):
        render_visualization(raw_data, processed_results, tmp_path)


# ==============================================================================
# Scenario 6: Missing Mask Data Across Sources
# ==============================================================================
# Under the no-default policy, if 'mask' is absent from both processed_results
# and inputs, rendering must raise a KeyError.

def test_render_visualization_missing_mask(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 1, "ny": 1, "nz": 1,
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            }
        }
    }
    processed_results = {}

    # Asserting that missing mask raises a KeyError.
    with pytest.raises(KeyError, match="Missing required 'mask' data"):
        render_visualization(raw_data, processed_results, tmp_path)


# ==============================================================================
# Scenario 7: Invalid Mask Type or Length Mismatch
# ==============================================================================
# The mask must be provided as a list whose length exactly matches the total
# number of grid cells (nx * ny * nz). Mismatches raise a ValueError.

def test_render_visualization_invalid_mask_length(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 2, "ny": 2, "nz": 2,  # Expected cells = 8
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            },
            "mask": [1, 0, 1]  # Length 3 != 8
        }
    }
    processed_results = {}

    # Asserting that mask length mismatch raises a ValueError.
    with pytest.raises(ValueError, match="Mask length does not match total grid cells"):
        render_visualization(raw_data, processed_results, tmp_path)


# ==============================================================================
# Scenario 8: Successful Render and Coordinate Mapping Validation
# ==============================================================================
# We verify that valid configuration and mask data execute the entire rendering
# pipeline successfully and that coordinate index mapping matches SSoT specifications.

def test_render_visualization_success(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 2, "ny": 2, "nz": 2,  # Expected cells = 8
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            },
            "mask": [1, -1, 0, 1, -1, 0, 1, -1]
        }
    }
    processed_results = {}

    # Executing rendering pipeline successfully
    render_visualization(raw_data, processed_results, tmp_path)

    # Verifying coordinate mapping helper function directly
    # index = i + nx * j + (nx * ny) * k
    # For nx=2, ny=2: xy_plane = 4. index 5 -> k=1, rem=1 -> j=0, i=1.
    i, j, k = get_coords_from_index(5, 2, 2)
    assert (i, j, k) == (1, 0, 1)
