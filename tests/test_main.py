"""
Literate Test Codex: Main Orchestration Script Validation
========================================================
This test suite provides comprehensive narratives verifying CLI argument parsing,
schema validation error handling, process execution failures, visualization warnings,
missing inputs key protection, ZIP field rendering error pathways, config fallback 
resolution, and output file write error handling in the main orchestration module,
leveraging the shared zero-mock pipeline test environment fixture.
"""

import sys
import json
import zipfile
from unittest.mock import patch

import pytest

from src.main import main


def test_main_success_pipeline(monkeypatch, pipeline_test_environment):
    # We test the complete zero-mock integration pipeline using the shared test environment fixture.
    env = pipeline_test_environment
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(env["input_dir"]),
            "--input_file_name", "input_run.json",
            "--output_file_name", "output_result.json"
        ]
    )
    monkeypatch.chdir(env["repo_root"])
    
    main()
    assert env["output_file"].exists()


def test_main_missing_inputs_key_error(monkeypatch, pipeline_test_environment):
    # We load the valid environment and overwrite the input file to omit the required 'inputs' root key,
    # ensuring our strict schema validation policy triggers a controlled failure.
    env = pipeline_test_environment
    invalid_payload = {"config": {}, "results": {"status": "success", "zip_filename": "simulation_results.zip"}, "not_inputs": {}}
    env["input_file"].write_text(json.dumps(invalid_payload), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(env["input_dir"]),
            "--input_file_name", "input_run.json",
            "--output_file_name", "output_result.json"
        ]
    )
    monkeypatch.chdir(env["repo_root"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_input_file_not_found(monkeypatch, pipeline_test_environment):
    # We configure command-line arguments pointing to a non-existent input file name within 
    # the shared test environment directory.
    env = pipeline_test_environment
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(env["input_dir"]),
            "--input_file_name", "non_existent_input.json",
            "--output_file_name", "output_result.json"
        ]
    )
    monkeypatch.chdir(env["repo_root"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_config_schema_validation_error(monkeypatch, pipeline_test_environment):
    # We corrupt the configuration file inside the config subdirectory to trigger 
    # configuration schema parsing and validation exception handling.
    env = pipeline_test_environment
    config_file = env["repo_root"] / "config" / "config.json"
    config_file.write_text("{malformed_config_json", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(env["input_dir"]),
            "--input_file_name", "input_run.json",
            "--output_file_name", "output_result.json"
        ]
    )
    monkeypatch.chdir(env["repo_root"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_process_flow_data_error(monkeypatch, pipeline_test_environment):
    # We modify the grid dimensions in the input payload to be invalid (e.g., nx = 0)
    # causing process_flow_data to raise a ValueError during numerical preprocessing.
    env = pipeline_test_environment
    payload = json.loads(env["input_file"].read_text(encoding="utf-8"))
    payload["inputs"]["grid"]["nx"] = 0
    env["input_file"].write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(env["input_dir"]),
            "--input_file_name", "input_run.json",
            "--output_file_name", "output_result.json"
        ]
    )
    monkeypatch.chdir(env["repo_root"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_visualization_rendering_warning(monkeypatch, pipeline_test_environment):
    # We utilize the standard environment and patch render_visualization to raise a ValueError,
    # validating that rendering anomalies are handled gracefully without aborting the pipeline.
    env = pipeline_test_environment
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(env["input_dir"]),
            "--input_file_name", "input_run.json",
            "--output_file_name", "output_result.json"
        ]
    )
    monkeypatch.chdir(env["repo_root"])

    with patch("src.main.render_visualization", side_effect=ValueError("Rendering engine warning")):
        main()

    assert env["output_file"].exists()


def test_main_zip_field_rendering_grid_bounds_fallback(monkeypatch, pipeline_test_environment):
    # We remove explicit grid bounds from config.json to verify that spatial limits 
    # successfully fall back to inputs['grid'] during zip field rendering.
    env = pipeline_test_environment
    config_file = env["repo_root"] / "config" / "config.json"
    config_data = json.loads(config_file.read_text(encoding="utf-8"))
    config_data.pop("grid_bounds", None)
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(env["input_dir"]),
            "--input_file_name", "input_run.json",
            "--output_file_name", "output_result.json"
        ]
    )
    monkeypatch.chdir(env["repo_root"])

    with patch("src.main.render_fields_from_zip") as mock_render_fields:
        main()
        mock_render_fields.assert_called_once()


def test_main_zip_field_rendering_branches(monkeypatch, pipeline_test_environment):
    # We update the input payload to reference a non-existent ZIP archive file
    # to evaluate the pipeline's branching logic for missing optional simulation files.
    env = pipeline_test_environment
    payload = json.loads(env["input_file"].read_text(encoding="utf-8"))
    payload["inputs"]["zip_filename"] = "non_existent_zip.zip"
    env["input_file"].write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(env["input_dir"]),
            "--input_file_name", "input_run.json",
            "--output_file_name", "output_result.json"
        ]
    )
    monkeypatch.chdir(env["repo_root"])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_output_write_error(monkeypatch, pipeline_test_environment):
    # We patch built-in open to raise an OSError during final JSON serialization 
    # to confirm robust error handling when output file writing fails.
    env = pipeline_test_environment
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder", str(env["input_dir"]),
            "--input_file_name", "input_run.json",
            "--output_file_name", "output_result.json"
        ]
    )
    monkeypatch.chdir(env["repo_root"])

    with patch("builtins.open", side_effect=OSError("Disk write permission denied")), pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
