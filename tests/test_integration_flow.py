# ==============================================================================
# LITERATE INTEGRATION TEST: FLOW ANALYSIS ENGINE SUCCESS PATH
# ==============================================================================
# This test verifies the end-to-end execution of the Flow Analysis & Visualization
# Engine without mocking. It triggers main.py via standard Python execution,
# captures emitted stderr logging output, asserts that log entries occur in exact
# chronological sequence across modules, and confirms output file generation.
# ==============================================================================

import json
import os
import subprocess
import sys
from pathlib import Path


def test_full_pipeline_integration_success_path(testing_environment):
    # We retrieve the target working directory and file names prepared by the test environment.
    input_output_folder = testing_environment["folder"]
    input_file_name = testing_environment["input_file_name"]
    output_file_name = testing_environment["output_file_name"]

    # We construct the CLI execution command matching standard CLI usage:
    # python src/main.py --input_output_folder <folder> --input_file_name <input> --output_file_name <output>
    cmd = [
        sys.executable,
        "-m",
        "src.main",
        "--input_output_folder",
        str(input_output_folder),
        "--input_file_name",
        input_file_name,
        "--output_file_name",
        output_file_name,
    ]

    # We ensure PYTHONPATH includes the repository root directory for clean module imports.
    repo_root = Path(__file__).parent.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)

    # We run main.py in a process to capture stdout and stderr streams,
    # specifying check=False to satisfy Ruff rule PLW1510.
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(repo_root),
        check=False,
    )

    # The pipeline execution exit code must be zero, indicating error-free completion.
    assert result.returncode == 0, f"Process failed with stderr:\n{result.stderr}"

    # We define the sequence of required log messages expected from every system module
    # in chronological order along the success path execution.
    expected_log_sequence = [
        "Initializing input parsing and schema validation module.",
        "Opening and parsing input JSON file.",
        "Validating input data against the provided JSON schema.",
        "Input file parsed and validated successfully.",
        "Successfully parsed and validated input data.",
        "Initializing flow analysis processor and ZIP inspection module.",
        "Extracting and validating configuration from input data.",
        "Executing simulation ZIP inspection and spatial interval analysis.",
        "Inspecting simulation ZIP archive contents in memory.",
        "ZIP inspection and Bernoulli boundary verification completed successfully.",
        "Executing spatial interval slicing and statistics computation.",
        "Spatial interval analysis completed successfully.",
        "Flow data processing completed successfully.",
        "Successfully executed flow processing and spatial probing.",
        "Initializing headless rendering and visualization pipeline.",
        "Initializing 3D voxel mask and mesh rendering pipeline.",
        "Generated 3D Voxel Verification snapshot: voxel_mask_verification.png",
        "Generated Mesh Snapshot: mesh_snapshot.png",
        "Generated STEP Geometry Snapshot: step_snapshot.png",
        "Voxel visualization rendered successfully.",
        "Initializing in-memory ZIP field renderer for archive.",
        "Opening ZIP archive for in-memory field rendering: simulation_data.zip",
        "Found 2 field file(s) inside simulation_data.zip",
        "Generated 3D field snapshot:",
        "ZIP field rendering completed successfully.",
        "Writing merged output results to target destination.",
        "Successfully wrote final output file.",
        "Pipeline execution completed successfully."
    ]

    # We examine the captured stderr output where logger entries are written.
    stderr_output = result.stderr

    # We verify that each expected log string appears in stderr in chronological order.
    last_found_index = -1
    for log_msg in expected_log_sequence:
        pos = stderr_output.find(log_msg)
        # Each log message must exist within the stderr execution log.
        assert pos != -1, f"Expected log message missing: '{log_msg}'\nFull Stderr:\n{stderr_output}"
        # Each log message must be located after the position of the preceding log message.
        assert pos > last_found_index, f"Log message arrived out of sequence order: '{log_msg}'"
        last_found_index = pos

    # We confirm that the final merged JSON output file was written to disk.
    output_path = input_output_folder / output_file_name
    assert output_path.exists(), f"Target output JSON missing at path: {output_path}"

    # We parse and inspect the generated final output JSON.
    with open(output_path, "r", encoding="utf-8") as f:
        output_data = json.load(f)

    # The merged output structure must contain both 'inputs' and 'results' top-level keys.
    assert "inputs" in output_data, "Merged JSON missing 'inputs' section."
    assert "results" in output_data, "Merged JSON missing 'results' section."

    # The status field in the processing results section must report 'success'.
    assert output_data["results"]["status"] == "success", "Results status is not 'success'."

    # We confirm that Bernoulli boundary physical checks passed without violation.
    bernoulli_check = output_data["results"]["bernoulli_boundary_check"]
    assert bernoulli_check["verified"] is True, f"Bernoulli check failed: {bernoulli_check}"

    # We verify that all diagnostic visualization images were saved and are non-empty.
    expected_generated_pngs = [
        "voxel_mask_verification.png",
        "mesh_snapshot.png",
        "step_snapshot.png",
        "u_step_000005_3d_verification.png",
        "p_step_000005_3d_verification.png"
    ]

    for png_filename in expected_generated_pngs:
        png_path = input_output_folder / png_filename
        # Each expected PNG file must exist as a regular file.
        assert png_path.is_file(), f"Expected diagnostic PNG missing: {png_filename}"
        # Each image file size must be greater than zero bytes.
        assert png_path.stat().st_size > 0, f"Rendered PNG image file is empty: {png_filename}"
