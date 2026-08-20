"""
Literate Test Codex: Main Orchestration Script Validation
========================================================
This test suite provides comprehensive narratives verifying CLI argument parsing,
schema validation error handling, process execution failures, visualization warnings,
missing inputs key protection, ZIP field rendering error pathways, config fallback 
resolution, and output file write error handling in the main orchestration module,
leveraging the shared zero-mock pipeline test environment fixture.
"""

import json
import sys
import zipfile
from unittest.mock import patch

import pytest

from src.main import main


def test_main_success_pipeline(monkeypatch, pipeline_test_environment):
    # We verify the primary execution pathway of the orchestration pipeline.
    # CLI arguments are injected via monkeypatch to simulate command-line invocation.
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
    
    # We execute the main orchestration entry point and assert that the output JSON is generated.
    main()
    assert env["output_file"].exists()


def test_main_missing_inputs_key_error(monkeypatch, pipeline_test_environment):
    # We test schema validation failure when the input file lacks the required 'inputs' key structure.
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

    # Invoking main() with an invalid input schema must trigger a controlled exit with code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_input_file_not_found(monkeypatch, pipeline_test_environment):
    # We test pipeline reaction when the specified input JSON file does not exist on disk.
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

    # Invoking main() with a non-existent input file triggers exit code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_config_schema_validation_error(monkeypatch, pipeline_test_environment):
    # We verify configuration schema parsing when config.json is corrupted or unparseable.
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

    # Corrupted configuration JSON causes main() to abort with exit code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_process_flow_data_error(monkeypatch, pipeline_test_environment):
    # We verify numerical processing failure handling when grid specifications are invalid.
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

    # Invalid grid dimensions cause process_flow_data to fail, resulting in exit code 1.
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_visualization_rendering_warning(monkeypatch, pipeline_test_environment):
    # We verify that visualization rendering failures produce non-fatal warnings without halting execution.
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

    # Rendering warnings are captured gracefully, allowing output file creation to succeed.
    with patch("src.main.render_visualization", side_effect=ValueError("Rendering engine warning")):
        main()

    assert env["output_file"].exists()


def test_main_zip_field_rendering_grid_bounds_fallback(monkeypatch, pipeline_test_environment):
    # We verify spatial limit resolution when grid_bounds is omitted from config.json.
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

    # The orchestrator falls back to inputs['grid'] bounds and calls render_fields_from_zip.
    with patch("src.main.render_fields_from_zip") as mock_render_fields:
        main()
        mock_render_fields.assert_called_once()


def test_main_zip_field_rendering_missing_zip_warning(monkeypatch, pipeline_test_environment):
    # We verify that referencing a non-existent ZIP archive issues a non-fatal warning.
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

    # We configure zip_filename to point to a non-existent ZIP archive in the results block.
    payload = json.loads(env["input_file"].read_text(encoding="utf-8"))
    payload["results"]["zip_filename"] = "non_existent_archive.zip"
    env["input_file"].write_text(json.dumps(payload), encoding="utf-8")

    # Patching process_flow_data allows execution to reach ZIP field rendering and complete normally.
    with patch("src.main.process_flow_data", return_value={"status": "success"}):
        main()

    assert env["output_file"].exists()


def test_main_missing_inputs_key_direct(monkeypatch, pipeline_test_environment):
    # We verify explicit KeyError raising when the 'inputs' key is missing during ZIP rendering.
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

    from src.core.parser import parse_input_file as original_parse
    def mock_parse(path, schema_path=None):
        if "input_run.json" in str(path):
            return {"results": {}}
        return original_parse(path, schema_path=schema_path)

    with patch("src.main.parse_input_file", side_effect=mock_parse), \
         patch("src.main.process_flow_data", return_value={}), \
         patch("src.main.render_visualization"), \
         pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_zip_field_rendering_exception_handling(monkeypatch, pipeline_test_environment):
    # We verify exception handling when the ZIP archive triggers BadZipFile during field rendering.
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

    # We write invalid content to the configured zip archive path retrieved from results.
    payload = json.loads(env["input_file"].read_text(encoding="utf-8"))
    zip_file_path = env["input_dir"] / payload["results"]["zip_filename"]
    zip_file_path.write_bytes(b"corrupted archive content")

    with patch("src.main.render_fields_from_zip", side_effect=zipfile.BadZipFile("Invalid zip structure")), pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_output_file_write_os_error(monkeypatch, pipeline_test_environment):
    # We verify output file write error handling when disk serialization encounters an OSError.
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

    original_open = open
    def mock_open(file, *args, **kwargs):
        if "output_result.json" in str(file):
            raise OSError("Simulated disk write permission denied")
        return original_open(file, *args, **kwargs)

    with patch("builtins.open", side_effect=mock_open), pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1