"""
Integration tests for the main orchestration script (src/main.py).
Verifies complete pipeline execution, error handling, and structured logging outputs.
"""

import json
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

from src.main import main


def test_main_success_flow(tmp_path, caplog):
    """Test successful execution of the main orchestration pipeline with valid inputs."""
    input_dir = tmp_path / "data"
    input_dir.mkdir()
    
    input_filename = "input.json"
    output_filename = "output.json"
    
    input_data = {
        "inputs": {
            "grid": {"nx": 3, "ny": 3, "nz": 3},
            "mask": [0] * 27
        }
    }
    
    input_path = input_dir / input_filename
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(input_data, f)
        
    with patch("sys.argv", [
        "main.py",
        "--input_output_folder", str(input_dir),
        "--input_file_name", input_filename,
        "--output_file_name", output_filename
    ]), caplog.at_level("INFO"):
        main()
        
    # Verify file output was generated
    assert (input_dir / output_filename).exists()
    
    # Verify expected log messages confirming module call sequence
    assert "Initializing input parsing and schema validation module." in caplog.text
    assert "Successfully parsed and validated input data." in caplog.text
    assert "Initializing flow analysis processor and ZIP inspection module." in caplog.text
    assert "Successfully executed flow processing and spatial probing." in caplog.text
    assert "Initializing headless rendering and visualization pipeline." in caplog.text
    assert "Successfully wrote final output file." in caplog.text
    assert "Pipeline execution completed successfully." in caplog.text


def test_main_input_file_not_found(tmp_path, caplog):
    """Test error handling and logging when the input file does not exist."""
    input_dir = tmp_path / "data"
    input_dir.mkdir()
    
    with patch("sys.argv", [
        "main.py",
        "--input_output_folder", str(input_dir),
        "--input_file_name", "non_existent.json",
        "--output_file_name", "output.json"
    ]), caplog.at_level("ERROR"), pytest.raises(SystemExit) as exc_info:
        main()
        
    assert exc_info.value.code == 1
    assert "Input file not found at target path." in caplog.text


def test_main_parser_exception(tmp_path, caplog):
    """Test error handling and logging when input file JSON decoding/validation fails."""
    input_dir = tmp_path / "data"
    input_dir.mkdir()
    
    input_filename = "bad_input.json"
    input_path = input_dir / input_filename
    input_path.write_text("invalid json payload content")
    
    with patch("sys.argv", [
        "main.py",
        "--input_output_folder", str(input_dir),
        "--input_file_name", input_filename,
        "--output_file_name", "output.json"
    ]), caplog.at_level("ERROR"), pytest.raises(SystemExit) as exc_info:
        main()
        
    assert exc_info.value.code == 1
    assert "Error validating input file against schema:" in caplog.text


def test_main_processor_exception(tmp_path, caplog):
    """Test error handling and logging when flow processing encounters an exception."""
    input_dir = tmp_path / "data"
    input_dir.mkdir()
    
    input_filename = "input.json"
    input_data = {
        "inputs": {
            "grid": {"nx": 3, "ny": 3, "nz": 3},
            "mask": [0] * 27
        }
    }
    input_path = input_dir / input_filename
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(input_data, f)
        
    with patch("src.main.process_flow_data", side_effect=Exception("Simulated processing failure")), \
         patch("sys.argv", [
             "main.py",
             "--input_output_folder", str(input_dir),
             "--input_file_name", input_filename,
             "--output_file_name", "output.json"
         ]), caplog.at_level("ERROR"), pytest.raises(SystemExit) as exc_info:
        main()
        
    assert exc_info.value.code == 1
    assert "Error during flow processing: Simulated processing failure" in caplog.text
