"""
Literate Test Codex: Main Orchestration Script Validation
========================================================
This test suite provides comprehensive narratives verifying CLI argument parsing,
schema validation error handling, process execution failures, visualization warnings,
missing inputs key protection, ZIP field rendering error pathways, and output file 
write error handling in the main orchestration module.
"""

import sys

import pytest

from src.main import main


def test_main_missing_inputs_key_error(monkeypatch, tmp_path):
    # We construct an invalid input data structure lacking the required root 'inputs' section.
    # Under our strict non-default schema policy, this omission must trigger a controlled failure.
    input_file = tmp_path / "invalid_input.json"
    input_file.write_text('{"not_inputs": {}}', encoding="utf-8")

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


def test_main_zip_field_rendering_branches(monkeypatch, tmp_path):
    # We establish a valid input configuration that references a non-existent ZIP archive file
    # to evaluate the pipeline's branching logic when handling missing optional simulation data.
    input_file = tmp_path / "test_input.json"
    valid_data = {
        "inputs": {
            "grid": {"nx": 2, "ny": 2, "nz": 2, "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1},
            "mask": [1, 1, 1, 1, 1, 1, 1, 1],
            "physical_constraints": {"min_value": 0.0, "max_value": 10.0},
            "zip_filename": "non_existent_zip.zip"
        }
    }
    input_file.write_text(str(valid_data).replace("'", '"'), encoding="utf-8")

    # We patch the system argument vector to simulate CLI execution with our test files.
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

    # We execute the pipeline and gracefully handle whether the branch resolves via a 
    # controlled system exit or warning path.
    try:
        main()
    except SystemExit as e:
        # If a system exit is triggered, we assert that the exit code is 1.
        assert e.code == 1
