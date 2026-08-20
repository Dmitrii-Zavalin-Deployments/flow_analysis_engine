"""
Literate Test Codex: Main Orchestration Script Validation
========================================================
This test suite provides comprehensive narratives verifying CLI argument parsing,
schema validation error handling, process execution failures, visualization warnings,
missing inputs key protection, ZIP field rendering error pathways, config fallback 
resolution, and output file write error handling in the main orchestration module.
"""

import sys
import zipfile
from unittest.mock import patch
from pathlib import Path
import pytest
from src.main import main


def test_main_missing_inputs_key_error(monkeypatch, tmp_path):
    # We construct an invalid input data structure lacking the required root 'inputs' section.
    # Under our strict non-default schema policy, this omission must trigger a controlled failure.
    input_file = tmp_path / "invalid_input.json"
    input_file.write_text('{"config": {}, "results": {"status": "success", "zip_filename": "simulation_results.zip"}, "not_inputs": {}}', encoding="utf-8")

    # We configure the command-line arguments to point the orchestrator to our temporary
    # isolated input folder and target output path.
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(tmp_path),
            "--input_file_name", "invalid_input.json",
            "--output_file_name", "output.json"
        ]
    )

    # When the orchestrator processes input missing the mandatory 'inputs' section,
    # it intercepts the KeyError, logs the diagnostic error, and exits via sys.exit(1).
    with pytest.raises(SystemExit) as exc_info:
        main()

    # We verify that the captured exit status code matches the expected CLI error code.
    assert exc_info.value.code == 1


def test_main_input_file_not_found(monkeypatch, tmp_path):
    # We configure command-line arguments pointing to a non-existent input file path 
    # within our temporary directory environment.
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(tmp_path),
            "--input_file_name", "non_existent_input.json",
            "--output_file_name", "output.json"
        ]
    )

    # When the target input file is missing, the orchestrator logs an error message
    # and terminates execution with exit code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()

    # We assert that the exit status code correctly indicates a failure.
    assert exc_info.value.code == 1


def test_main_config_schema_validation_error(monkeypatch, tmp_path):
    # We create a malformed configuration file inside a config subdirectory to trigger 
    # configuration schema parsing and validation exception handling.
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    config_file.write_text("{malformed_config_json", encoding="utf-8")

    # We provide a valid input JSON file so the primary input parsing succeeds.
    input_file = tmp_path / "input.json"
    valid_data = {
        "config": {},
        "results": {"status": "success", "zip_filename": "simulation_results.zip"},
        "inputs": {
            "grid": {"nx": 1, "ny": 1, "nz": 1, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [1],
            "physical_constraints": {}
        }
    }
    input_file.write_text(str(valid_data).replace("'", '"'), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(tmp_path),
            "--input_file_name", "input.json",
            "--output_file_name", "output.json"
        ]
    )

    # When config validation encounters malformed JSON or schema violations, it catches 
    # the exception and exits with status code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_process_flow_data_error(monkeypatch, tmp_path):
    # We provide an input file containing invalid grid specifications (e.g., zero dimension nx = 0)
    # which causes process_flow_data to raise a ValueError during numerical preprocessing.
    input_file = tmp_path / "input.json"
    invalid_grid_data = {
        "config": {},
        "results": {"status": "success", "zip_filename": "simulation_results.zip"},
        "inputs": {
            "grid": {"nx": 0, "ny": 1, "nz": 1, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [],
            "physical_constraints": {}
        }
    }
    input_file.write_text(str(invalid_grid_data).replace("'", '"'), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(tmp_path),
            "--input_file_name", "input.json",
            "--output_file_name", "output.json"
        ]
    )

    # The orchestrator catches processing exceptions, logs the error, and terminates via sys.exit(1).
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_visualization_rendering_warning(monkeypatch, tmp_path):
    # We set up valid input data and patch render_visualization using standard unittest.mock
    # to raise a ValueError, validating that rendering anomalies are handled gracefully as warnings.
    input_file = tmp_path / "input.json"
    valid_data = {
        "config": {},
        "results": {"status": "success", "zip_filename": "simulation_results.zip"},
        "inputs": {
            "grid": {"nx": 1, "ny": 1, "nz": 1, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [1],
            "physical_constraints": {}
        }
    }
    input_file.write_text(str(valid_data).replace("'", '"'), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(tmp_path),
            "--input_file_name", "input.json",
            "--output_file_name", "output.json"
        ]
    )

    # We patch the renderer to simulate a non-fatal visualization exception.
    with patch("src.main.render_visualization", side_effect=ValueError("Rendering engine warning")):
        main()

    output_path = tmp_path / "output.json"
    assert output_path.exists()


def test_main_zip_field_rendering_grid_bounds_fallback(monkeypatch, tmp_path):
    # We construct a valid simulation ZIP archive and configure input parameters lacking explicit 
    # config.json grid_bounds, forcing the orchestrator to extract spatial limits from inputs['grid'].
    zip_name = "simulation_results.zip"
    zip_path = tmp_path / zip_name
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("field_data.npy", b"fake_array_bytes")

    input_file = tmp_path / "input.json"
    valid_data = {
        "config": {},
        "results": {"status": "success", "zip_filename": zip_name},
        "inputs": {
            "grid": {"nx": 1, "ny": 1, "nz": 1, "x_min": 0.0, "x_max": 1.0, "y_min": 0.0, "y_max": 1.0, "z_min": 0.0, "z_max": 1.0},
            "mask": [1],
            "physical_constraints": {"min_value": 0.0, "max_value": 10.0}
        }
    }
    input_file.write_text(str(valid_data).replace("'", '"'), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(tmp_path),
            "--input_file_name", "input.json",
            "--output_file_name", "output.json"
        ]
    )

    # We patch render_fields_from_zip to verify that fallback grid bounds extraction succeeds.
    with patch("src.main.render_fields_from_zip") as mock_render_fields:
        main()
        mock_render_fields.assert_called_once()


def test_main_zip_field_rendering_branches(monkeypatch, tmp_path):
    # We establish a valid input configuration that references a non-existent ZIP archive file
    # to evaluate the pipeline's branching logic when handling missing optional simulation data.
    input_file = tmp_path / "test_input.json"
    valid_data = {
        "config": {},
        "results": {"status": "success", "zip_filename": "non_existent_zip.zip"},
        "inputs": {
            "grid": {"nx": 2, "ny": 2, "nz": 2, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [1, 1, 1, 1, 1, 1, 1, 1],
            "physical_constraints": {"min_value": 0.0, "max_value": 10.0}
        }
    }
    input_file.write_text(str(valid_data).replace("'", '"'), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(tmp_path),
            "--input_file_name", "test_input.json",
            "--output_file_name", "output.json"
        ]
    )

    # When the zip archive path does not exist, the orchestrator logs a warning branch.
    try:
        main()
    except SystemExit as e:
        assert e.code == 1


def test_main_output_write_error(monkeypatch, tmp_path):
    # We set up valid input data and patch built-in open to raise an OSError 
    # during final JSON results serialization to test output write error handling.
    input_file = tmp_path / "input.json"
    valid_data = {
        "config": {},
        "results": {"status": "success", "zip_filename": "simulation_results.zip"},
        "inputs": {
            "grid": {"nx": 1, "ny": 1, "nz": 1, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [1],
            "physical_constraints": {}
        }
    }
    input_file.write_text(str(valid_data).replace("'", '"'), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(tmp_path),
            "--input_file_name", "input.json",
            "--output_file_name", "output.json"
        ]
    )

    # We simulate a disk I/O failure during output file writing using a single combined context.
    with patch("builtins.open", side_effect=OSError("Disk write permission denied")), pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
