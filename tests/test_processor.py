"""
Literate Test Codex: Processor Module Validation
================================================
This module defines the validation narratives for the numerical processing
pipeline, verifying strict enforcement of configuration schemas, grid parameter
bounds, mask dimensions, and zip file existence under the no-default policy.
"""

from pathlib import Path
import pytest
import zipfile
import json

from src.core.processor import process_flow_data


# ==============================================================================
# Scenario 1: Validating Input Directory Integrity
# ==============================================================================
# If the provided input directory path does not exist or points to a file 
# instead of a directory, the processor must raise a NotADirectoryError.

def test_process_flow_data_invalid_directory(tmp_path):
    # We define a path that does not correspond to an actual directory.
    non_existent_dir = tmp_path / "missing_directory"
    
    # We assert that a NotADirectoryError is raised immediately.
    with pytest.raises(NotADirectoryError, match="Input directory not found"):
        process_flow_data({}, non_existent_dir)


# ==============================================================================
# Scenario 2: Enforcing Mandatory 'inputs' Root Key
# ==============================================================================
# Under the strict no-default policy, raw configuration payloads must contain 
# an explicit 'inputs' dictionary section.

def test_process_flow_data_missing_inputs(tmp_path):
    # We supply a raw data dictionary devoid of the 'inputs' key.
    raw_data = {}

    # We assert that a KeyError is raised for the missing section.
    with pytest.raises(KeyError, match="Missing required 'inputs' section"):
        process_flow_data(raw_data, tmp_path)


# ==============================================================================
# Scenario 3: Enforcing Mandatory 'grid' Configuration
# ==============================================================================
# Within the inputs block, a grid definition containing spatial boundaries and
# resolution dimensions must be explicitly provided.

def test_process_flow_data_missing_grid(tmp_path):
    raw_data = {"inputs": {}}

    # We assert that a KeyError is raised when 'grid' is omitted.
    with pytest.raises(KeyError, match="Missing required 'grid' configuration"):
        process_flow_data(raw_data, tmp_path)


# ==============================================================================
# Scenario 4: Handling Invalid or Missing Grid Parameters and Types
# ==============================================================================
# If individual grid bounds or resolution fields are missing or malformed 
# (e.g. non-numeric strings), parsing errors must be caught and raised.

def test_process_flow_data_invalid_grid_parameters(tmp_path):
    # We omit required grid keys like 'ny', 'nz', etc., or provide bad types.
    raw_data = {
        "inputs": {
            "grid": {
                "nx": "invalid_integer",  # Causes type conversion error
                "x_min": 0.0, "x_max": 10.0,
                "y_min": 0.0, "y_max": 10.0,
                "z_min": 0.0, "z_max": 10.0
            }
        }
    }

    # We assert that a ValueError is raised for invalid type conversion.
    with pytest.raises(ValueError, match="Invalid grid parameter value"):
        process_flow_data(raw_data, tmp_path)


# ==============================================================================
# Scenario 5: Enforcing Positive Grid Dimensions
# ==============================================================================
# Grid dimensions (nx, ny, nz) must be strictly greater than zero. Zero or 
# negative dimensions violate numerical discretization constraints.

def test_process_flow_data_non_positive_dimensions(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 0, "ny": 10, "nz": 10,
                "x_min": 0.0, "x_max": 10.0,
                "y_min": 0.0, "y_max": 10.0,
                "z_min": 0.0, "z_max": 10.0
            }
        }
    }

    # We assert that a ValueError is raised for non-positive grid size.
    with pytest.raises(ValueError, match="Grid dimensions.*must be strictly greater than zero"):
        process_flow_data(raw_data, tmp_path)


# ==============================================================================
# Scenario 6: Enforcing Mandatory Simulation Mask Key
# ==============================================================================
# The input block must contain a cell selection mask for numerical processing.

def test_process_flow_data_missing_mask(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 2, "ny": 2, "nz": 2,
                "x_min": 0.0, "x_max": 2.0,
                "y_min": 0.0, "y_max": 2.0,
                "z_min": 0.0, "z_max": 2.0
            }
        }
    }

    # We assert that a KeyError is raised when 'mask' is absent.
    with pytest.raises(KeyError, match="Missing required 'mask' key"):
        process_flow_data(raw_data, tmp_path)


# ==============================================================================
# Scenario 7: Verifying Mask Length and Structure
# ==============================================================================
# The provided mask list must match the total number of grid cells (nx * ny * nz).

def test_process_flow_data_invalid_mask_length(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 2, "ny": 2, "nz": 2,  # Total expected cells = 2 * 2 * 2 = 8
                "x_min": 0.0, "x_max": 2.0,
                "y_min": 0.0, "y_max": 2.0,
                "z_min": 0.0, "z_max": 2.0
            },
            "mask": [1, 1, 1]  # Incorrect length (3 instead of 8)
        }
    }

    # We assert that a ValueError is raised due to cell count mismatch.
    with pytest.raises(ValueError, match="Mask length does not match"):
        process_flow_data(raw_data, tmp_path)


# ==============================================================================
# Scenario 8: Enforcing Physical Constraints Configuration
# ==============================================================================
# Physical boundary conditions and constraint thresholds must be explicitly declared.

def test_process_flow_data_missing_constraints(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 1, "ny": 1, "nz": 1,
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            },
            "mask": [1]
        }
    }

    # We assert that a KeyError is raised for missing physical constraints.
    with pytest.raises(KeyError, match="Missing required 'physical_constraints' section"):
        process_flow_data(raw_data, tmp_path)


# ==============================================================================
# Scenario 9: Enforcing Zip Filename Presence
# ==============================================================================
# The processor requires an explicit target simulation archive filename with 
# no auto-discovery or globbing fallbacks.

def test_process_flow_data_missing_zip_filename(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 1, "ny": 1, "nz": 1,
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            },
            "mask": [1],
            "physical_constraints": {}
        }
    }

    # We assert that a KeyError is raised when zip_filename is omitted.
    with pytest.raises(KeyError, match="Missing required 'zip_filename' parameter"):
        process_flow_data(raw_data, tmp_path)


# ==============================================================================
# Scenario 10: Verifying Simulation Archive Existence
# ==============================================================================
# If the configured zip filename does not exist within the input directory,
# a FileNotFoundError must be raised.

def test_process_flow_data_zip_not_found(tmp_path):
    raw_data = {
        "inputs": {
            "grid": {
                "nx": 1, "ny": 1, "nz": 1,
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            },
            "mask": [1],
            "physical_constraints": {},
            "zip_filename": "non_existent_simulation.zip"
        }
    }

    # We assert that a FileNotFoundError is raised when the archive is missing.
    with pytest.raises(FileNotFoundError, match="Configured ZIP archive not found"):
        process_flow_data(raw_data, tmp_path)
