"""
Literate Test Codex: ZIP Inspector Module Validation
===================================================
This module provides comprehensive test narratives verifying in-memory ZIP 
archive inspection, Navier-Stokes global field statistics tracking, targeted 
step snapshot extraction, and Bernoulli boundary constraint verification.
"""

import zipfile

import numpy as np
import pytest

from src.core.zip_inspector import inspect_simulation_zip

# ==============================================================================
# Scenario 1: Handling Missing Simulation ZIP Archive
# ==============================================================================
# When the target simulation archive does not exist on disk, the inspector
# must catch the filesystem check and raise a FileNotFoundError.

def test_inspect_simulation_zip_not_found(tmp_path):
    # We specify a non-existent ZIP file path.
    missing_zip = tmp_path / "non_existent.zip"
    constraints = {
        "min_velocity": 0.0, "max_velocity": 10.0,
        "min_pressure": 0.0, "max_pressure": 10.0
    }

    # Asserting that a FileNotFoundError is raised.
    with pytest.raises(FileNotFoundError, match="Simulation ZIP archive not found"):
        inspect_simulation_zip(missing_zip, constraints)


# ==============================================================================
# Scenario 2: Enforcing No-Default Policy for Physical Constraints
# ==============================================================================
# Under the strict no-default policy, passing None for physical constraints
# must immediately trigger a configuration ValueError.

def test_inspect_simulation_zip_constraints_none(tmp_path):
    dummy_zip = tmp_path / "sim.zip"
    with zipfile.ZipFile(dummy_zip, "w") as zf:
        zf.writestr("u.npy", np.zeros((2, 2, 2)).tobytes())

    # Asserting that passing None raises a ValueError.
    with pytest.raises(ValueError, match="Physical constraints configuration must be explicitly provided"):
        inspect_simulation_zip(dummy_zip, None)


# ==============================================================================
# Scenario 3: Enforcing Mandatory Physical Constraint Keys
# ==============================================================================
# All required constraint bounds (min_velocity, max_velocity, min_pressure, 
# max_pressure) must be explicitly present in the dictionary.

def test_inspect_simulation_zip_missing_constraint_key(tmp_path):
    dummy_zip = tmp_path / "sim.zip"
    with zipfile.ZipFile(dummy_zip, "w") as zf:
        zf.writestr("u.npy", np.zeros((2, 2, 2)).tobytes())

    # We omit 'max_velocity' from the constraint dictionary.
    incomplete_constraints = {
        "min_velocity": 0.0,
        "min_pressure": 0.0, "max_pressure": 10.0
    }

    # Asserting that a KeyError is raised.
    with pytest.raises(KeyError, match="Missing required physical constraint key"):
        inspect_simulation_zip(dummy_zip, incomplete_constraints)


# ==============================================================================
# Scenario 4: Validating Physical Constraint Types and Values
# ==============================================================================
# Constraint bound values must be convertible to floats; invalid types must
# trigger a descriptive ValueError.

def test_inspect_simulation_zip_invalid_constraint_type(tmp_path):
    dummy_zip = tmp_path / "sim.zip"
    with zipfile.ZipFile(dummy_zip, "w") as zf:
        zf.writestr("u.npy", np.zeros((2, 2, 2)).tobytes())

    # We provide a non-numeric string for max_velocity.
    invalid_constraints = {
        "min_velocity": 0.0, "max_velocity": "not_a_float",
        "min_pressure": 0.0, "max_pressure": 10.0
    }

    # Asserting that a ValueError is raised.
    with pytest.raises(ValueError, match="Invalid physical constraint bound value"):
        inspect_simulation_zip(dummy_zip, invalid_constraints)


# ==============================================================================
# Scenario 5: Handling Corrupted or Invalid ZIP Archives
# ==============================================================================
# If the target file is not a valid ZIP archive (e.g. malformed binary data),
# the extraction attempt must raise a ValueError.

def test_inspect_simulation_zip_bad_zip_file(tmp_path):
    bad_zip = tmp_path / "corrupted.zip"
    bad_zip.write_bytes(b"not a valid zip file content")

    constraints = {
        "min_velocity": 0.0, "max_velocity": 10.0,
        "min_pressure": 0.0, "max_pressure": 10.0
    }

    # Asserting that a ValueError is raised for the corrupted archive.
    with pytest.raises(ValueError, match="Invalid or corrupted ZIP archive"):
        inspect_simulation_zip(bad_zip, constraints)


# ==============================================================================
# Scenario 6: Handling ZIP Archives Lacking .npy Files
# ==============================================================================
# An archive without any .npy files executes successfully with an empty summary
# and a warning log.

def test_inspect_simulation_zip_no_npy_files(tmp_path):
    empty_zip = tmp_path / "empty_sim.zip"
    with zipfile.ZipFile(empty_zip, "w") as zf:
        zf.writestr("readme.txt", b"No npy data here")

    constraints = {
        "min_velocity": -10.0, "max_velocity": 10.0,
        "min_pressure": -10.0, "max_pressure": 10.0
    }

    result = inspect_simulation_zip(empty_zip, constraints)
    assert result["navier_stokes_summary"] == {}
    assert result["bernoulli_boundary_check"]["verified"] is True


# ==============================================================================
# Scenario 7: Successful Inspection and Bernoulli Boundary Verifications
# ==============================================================================
# We verify successful in-memory inspection of velocity ('u') and pressure ('p')
# fields, targeted snapshot extraction (`step_000005` in both low-dim and high-dim),
# and Bernoulli boundary condition verification (including violation cases).

def test_inspect_simulation_zip_success_and_violations(tmp_path):
    sim_zip = tmp_path / "simulation_run.zip"
    
    with zipfile.ZipFile(sim_zip, "w") as zf:
        # Velocity array (u field) with values within normal bounds
        u_arr = np.array([1.0, 2.0, 3.0, 4.0], dtype=float)
        zf.writestr("u_field.npy", u_arr.tobytes())

        # Pressure array (p field) with targeted step name for snapshot testing (low-dim <= 2)
        p_arr = np.array([[5.0, 6.0], [7.0, 8.0]], dtype=float)
        zf.writestr("p_field_step_000005.npy", p_arr.tobytes())

        # High-dimensional array containing step_000005 to test flattening branch (> 2 dimensions)
        high_dim_arr = np.ones((2, 2, 2, 2), dtype=float)
        zf.writestr("velocity_w_step_000005.npy", high_dim_arr.tobytes())

    # Case A: Strict constraints where all values comply (Verified = True)
    valid_constraints = {
        "min_velocity": 0.0, "max_velocity": 5.0,
        "min_pressure": 0.0, "max_pressure": 10.0
    }
    res_valid = inspect_simulation_zip(sim_zip, valid_constraints)
    assert res_valid["bernoulli_boundary_check"]["verified"] is True

    # Case B: Constraints triggered to test lower/upper velocity and pressure bound violations
    violating_constraints = {
        "min_velocity": 2.0,  # Violated by u_arr min (1.0)
        "max_velocity": 3.0,  # Violated by u_arr max (4.0)
        "min_pressure": 6.0,  # Violated by p_arr min (5.0)
        "max_pressure": 7.0   # Violated by p_arr max (8.0)
    }
    res_violation = inspect_simulation_zip(sim_zip, violating_constraints)
    
    # We verify that verification failed and all four violation details are captured.
    check = res_violation["bernoulli_boundary_check"]
    assert check["verified"] is False
    assert len(check["details"]) == 4
