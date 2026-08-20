"""
Literate Test Codex: Main Orchestration Script Validation
========================================================
This test suite provides comprehensive narratives verifying CLI argument parsing,
schema validation error handling, process execution failures, visualization warnings,
missing inputs key protection, ZIP field rendering error pathways, and output file 
write error handling in the main orchestration module.
"""

import json
import sys
import zipfile

import numpy as np
import pytest

from src.main import main


def setup_test_environment(tmp_path):
    """Helper to set up standard schema and config directory structures for CLI tests."""
    base = tmp_path
    schema_dir = base / "schema"
    schema_dir.mkdir(parents=True, exist_ok=True)
    config_dir = base / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Write valid configuration schema
    config_schema = {
        "type": "object",
        "properties": {"settings": {"type": "object"}},
        "required": ["settings"]
    }
    (schema_dir / "flow_analysis_engine_config_schema.json").write_text(json.dumps(config_schema))
    
    # Write valid input schema
    input_schema = {
        "type": "object",
        "properties": {"inputs": {"type": "object"}},
        "required": ["inputs"]
    }
    (schema_dir / "flow_analysis_engine_input_schema.json").write_text(json.dumps(input_schema))
    
    # Write valid config file
    (config_dir / "config.json").write_text(json.dumps({"settings": {}}))
    
    return data_dir


# ==============================================================================
# Scenario 1: Config File Validation Error Handling
# ==============================================================================
# When the system configuration file violates its corresponding schema, 
# main must catch the validation error and terminate with exit code 1.

def test_main_config_validation_error(tmp_path, monkeypatch):
    data_dir = setup_test_environment(tmp_path)
    
    # We write a configuration that violates the schema (missing required 'settings').
    config_path = tmp_path / "config" / "config.json"
    config_path.write_text(json.dumps({"invalid_key": 123}))
    
    input_file = data_dir / "input.json"
    input_file.write_text(json.dumps({"inputs": {}}))
    
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(data_dir),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])

    # Asserting that configuration validation failure exits with code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


# ==============================================================================
# Scenario 2: Input File Not Found Handling
# ==============================================================================
# If the specified input JSON file does not exist on disk, main must log 
# an error and exit with code 1.

def test_main_input_file_not_found(tmp_path, monkeypatch):
    data_dir = setup_test_environment(tmp_path)
    
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(data_dir),
        "--input_file_name", "missing_input.json",
        "--output_file_name", "output.json"
    ])

    # Asserting that missing input files trigger exit code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


# ==============================================================================
# Scenario 3: Input Schema Validation Error Handling
# ==============================================================================
# When input data violates the input schema structure, main must catch the 
# error and exit with code 1.

def test_main_input_schema_validation_error(tmp_path, monkeypatch):
    data_dir = setup_test_environment(tmp_path)
    
    input_file = data_dir / "input.json"
    # Violates input schema by omitting the required 'inputs' section.
    input_file.write_text(json.dumps({"wrong_section": {}}))
    
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(data_dir),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])

    # Asserting that schema validation failure exits with code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


# ==============================================================================
# Scenario 4: Flow Processing Execution Error Handling
# ==============================================================================
# If flow data processing encounters an exception (such as a missing simulation 
# archive), main must catch the error and terminate with exit code 1.

def test_main_flow_processing_error(tmp_path, monkeypatch):
    data_dir = setup_test_environment(tmp_path)
    
    input_file = data_dir / "input.json"
    payload = {
        "inputs": {
            "grid": {"nx": 1, "ny": 1, "nz": 1, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [1],
            "physical_constraints": {"min_velocity": 0, "max_velocity": 10, "min_pressure": 0, "max_pressure": 10},
            "zip_filename": "non_existent_sim.zip"  # Triggers FileNotFoundError during processing
        }
    }
    input_file.write_text(json.dumps(payload))
    
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(data_dir),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])

    # Asserting that processing errors trigger exit code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


# ==============================================================================
# Scenario 5: Voxel Visualization Rendering Warning Recovery
# ==============================================================================
# When voxel visualization rendering encounters an issue, main logs a warning 
# and continues execution gracefully without terminating.

def test_main_visualization_rendering_warning(tmp_path, monkeypatch):
    data_dir = setup_test_environment(tmp_path)
    
    input_file = data_dir / "input.json"
    payload = {
        "inputs": {
            "grid": {"nx": 1, "ny": 1, "nz": 1, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [1],
            "physical_constraints": {"min_velocity": 0, "max_velocity": 10, "min_pressure": 0, "max_pressure": 10},
            "zip_filename": "sim.zip"
        }
    }
    input_file.write_text(json.dumps(payload))
    
    # We create a valid simulation ZIP archive.
    sim_zip = data_dir / "sim.zip"
    with zipfile.ZipFile(sim_zip, "w") as zf:
        zf.writestr("u.npy", np.zeros((1, 1, 1)).tobytes())

    # We mock render_visualization to raise a ValueError to verify warning catch.
    import src.main as main_module
    monkeypatch.setattr(main_module, "render_visualization", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("Render failed")))
    
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(data_dir),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])

    # Executing main; it should succeed despite the rendering warning.
    main()


# ==============================================================================
# Scenario 6: Missing 'inputs' Section KeyError Enforcement
# ==============================================================================
# Under the strict no-default policy, raw data missing the 'inputs' section 
# during post-processing must raise a KeyError.

def test_main_missing_inputs_key_error(tmp_path, monkeypatch):
    data_dir = setup_test_environment(tmp_path)
    
    # We mock parse_input_file to return a payload devoid of the 'inputs' key.
    import src.main as main_module
    monkeypatch.setattr(main_module, "parse_input_file", lambda *args, **kwargs: {"invalid_key": "data"})
    
    input_file = data_dir / "input.json"
    input_file.write_text("{}")
    
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(data_dir),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])

    # Asserting that a KeyError is raised.
    with pytest.raises(KeyError, match="Required 'inputs' section is missing"):
        main()


# ==============================================================================
# Scenario 7: ZIP Field Rendering Branches and Error Handling
# ==============================================================================
# We verify both ZIP field rendering warning pathways:
# 1. Configured zip archive path does not exist (logging warning).
# 2. ZIP field rendering raises an exception (catching and logging warning).

def test_main_zip_field_rendering_branches(tmp_path, monkeypatch):
    data_dir = setup_test_environment(tmp_path)
    
    input_file = data_dir / "input.json"
    payload = {
        "inputs": {
            "grid": {"nx": 1, "ny": 1, "nz": 1, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [1],
            "physical_constraints": {"min_velocity": 0, "max_velocity": 10, "min_pressure": 0, "max_pressure": 10},
            "zip_filename": "non_existent_zip.zip"
        }
    }
    input_file.write_text(json.dumps(payload))
    
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(data_dir),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])
    
    # Branch 1: Zip file does not exist on disk (logs warning).
    main()
    
    # Branch 2: Zip file exists, but rendering raises BadZipFile.
    existent_zip = data_dir / "non_existent_zip.zip"
    existent_zip.write_bytes(b"corrupted zip bytes")
    
    import src.main as main_module
    monkeypatch.setattr(main_module, "render_fields_from_zip", lambda *args, **kwargs: (_ for _ in ()).throw(zipfile.BadZipFile("Bad zip")))
    
    main()


# ==============================================================================
# Scenario 8: Output File Write Error Handling
# ==============================================================================
# If writing the final merged output file encounters an OSError, main must 
# catch the exception and terminate with exit code 1.

def test_main_write_output_error(tmp_path, monkeypatch):
    data_dir = setup_test_environment(tmp_path)
    
    input_file = data_dir / "input.json"
    payload = {
        "inputs": {
            "grid": {"nx": 1, "ny": 1, "nz": 1, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [1],
            "physical_constraints": {"min_velocity": 0, "max_velocity": 10, "min_pressure": 0, "max_pressure": 10},
            "zip_filename": "sim.zip"
        }
    }
    input_file.write_text(json.dumps(payload))
    
    sim_zip = data_dir / "sim.zip"
    with zipfile.ZipFile(sim_zip, "w") as zf:
        zf.writestr("u.npy", np.zeros((1, 1, 1)).tobytes())
    
    # We mock built-in open to raise an OSError when writing the output file.
    import builtins
    orig_open = builtins.open
    def mock_open(file, *args, **kwargs):
        if str(file).endswith("output.json"):
            raise OSError("Simulated disk write failure")
        return orig_open(file, *args, **kwargs)
    
    monkeypatch.setattr(builtins, "open", mock_open)
    
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(data_dir),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])

    # Asserting that output write failure triggers exit code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
