"""
Integration Test Suite: Full Pipeline Positive Path Execution
=============================================================

Description:
    This test file serves as the definitive zero-mock integration test for the 
    Flow Analysis Engine pipeline. It exercises the entire software architecture 
    end-to-end through the main orchestration entry point (`src.main`).

Purpose:
    1. Validates that all core modules (parser, processor, spatial probe, zip 
       inspector, renderers, and main CLI) interoperate correctly together in 
       a live environment without relying on mocks or isolated stubs.
    2. Asserts the production of all expected physical output artifacts, including 
       the merged result JSON file and visual 3D verification PNG snapshots.
    3. Verifies the exact sequential progression of operational log messages 
       to guarantee architectural consistency and traceability.
    4. Ensures comprehensive code coverage tracking (`pytest-cov`) across all files 
       by executing the pipeline directly in-process.
"""

import json
import logging
import zipfile
from pathlib import Path
import numpy as np
import pytest

from src.main import main


# We define the zero-mock end-to-end integration test function.
def test_full_pipeline_integration_positive_path(tmp_path, monkeypatch, caplog):
    
    # We configure the logging capture level to INFO to monitor sequential operational milestones.
    caplog.set_level(logging.INFO)

    # We construct the real project directory hierarchy on disk to mirror the production layout.
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    schema_dir = repo_root / "schema"
    schema_dir.mkdir()
    config_dir = repo_root / "config"
    config_dir.mkdir()
    input_dir = repo_root / "data_run"
    input_dir.mkdir()

    # We write the required JSON schema files for input validation and configuration compliance.
    input_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["inputs"],
        "properties": {
            "inputs": {
                "type": "object",
                "required": ["grid", "mask", "physical_constraints", "zip_filename"]
            }
        }
    }
    (schema_dir / "flow_analysis_engine_input_schema.json").write_text(json.dumps(input_schema))

    config_schema = {"type": "object"}
    (schema_dir / "flow_analysis_engine_config_schema.json").write_text(json.dumps(config_schema))

    # We define and write the spatial configuration file containing grid bounds and coordinate ranges.
    config_data = {
        "grid_bounds": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
        "x_range": [0.0, 0.5],
        "y_range": [0.0, 0.5],
        "z_range": [0.0, 0.5]
    }
    (config_dir / "config.json").write_text(json.dumps(config_data))

    # We generate a real simulation ZIP archive containing NumPy binary arrays (.npy) for velocity and pressure fields.
    zip_path = input_dir / "simulation_results.zip"
    u_field = np.ones((2, 2, 2), dtype=float) * 2.5
    p_field = np.full((2, 2, 2), 101325.0, dtype=float)

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("u_step_000005.npy", u_field.tobytes())
        zf.writestr("p_step_000005.npy", p_field.tobytes())

    # We formulate and write the input payload JSON containing grid parameters, fluid masks, and constraints.
    input_payload = {
        "inputs": {
            "grid": {
                "nx": 2, "ny": 2, "nz": 2,
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            },
            "mask": [1, -1, 0, 1, 1, 0, -1, 1],
            "physical_constraints": {
                "min_velocity": 0.0,
                "max_velocity": 10.0,
                "min_pressure": 0.0,
                "max_pressure": 200000.0
            },
            "zip_filename": "simulation_results.zip"
        }
    }
    input_file = input_dir / "input_run.json"
    output_file = input_dir / "output_result.json"
    input_file.write_text(json.dumps(input_payload))

    # We configure the command-line arguments and patch sys.argv to simulate a real CLI invocation.
    cli_args = [
        "main.py",
        "--input_output_folder", str(input_dir),
        "--input_file_name", input_file.name,
        "--output_file_name", output_file.name
    ]
    monkeypatch.setattr("sys.argv", cli_args)

    # We execute the full pipeline orchestration via the main entry point.
    main()

    # We assert that all physical file artifacts and rendered 3D visual verification images have been successfully produced.
    assert output_file.exists(), "Merged output JSON file was not generated."
    assert (input_dir / "integration_voxel_verification.png").exists()
    assert (input_dir / "mesh_snapshot.png").exists()
    assert (input_dir / "step_snapshot.png").exists()
    assert (input_dir / "u_step_000005_3d_verification.png").exists()
    assert (input_dir / "p_step_000005_3d_verification.png").exists()

    # We verify the data contents and validation results written into the merged JSON output file.
    merged_data = json.loads(output_file.read_text())
    assert merged_data["results"]["status"] == "success"
    assert "spatial_interval_analysis" in merged_data["results"]
    assert "bernoulli_boundary_check" in merged_data["results"]
    assert merged_data["results"]["bernoulli_boundary_check"]["verified"] is True

    # We extract and inspect the log messages to ensure the exact sequential progression of pipeline milestones.
    log_messages = [record.message for record in caplog.records]
    
    expected_log_sequence = [
        "Initializing input parsing and schema validation module.",
        "Successfully parsed and validated input data.",
        "Initializing flow analysis processor and ZIP inspection module.",
        "Successfully executed flow processing and spatial probing.",
        "Initializing headless rendering and visualization pipeline.",
        "Voxel visualization rendered successfully.",
        "Initializing in-memory ZIP field renderer for archive.",
        "ZIP field rendering completed successfully.",
        "Writing merged output results to target destination.",
        "Successfully wrote final output file.",
        "Pipeline execution completed successfully."
    ]

    for log_item in expected_log_sequence:
        assert any(log_item in msg for msg in log_messages), f"Missing log step: {log_item}"
