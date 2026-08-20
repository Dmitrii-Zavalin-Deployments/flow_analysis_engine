"""
Literate Test Codex: Parser Module Validation
=============================================
This module provides comprehensive test narratives verifying input parsing,
schema enforcement, error resilience, and strict adherence to the no-default policy.
"""

import json
from pathlib import Path
import pytest

from src.core.parser import parse_input_file


# ==============================================================================
# Scenario 1: Handling Missing Input Files
# ==============================================================================
# When an input file path points to a non-existent location, the parser must 
# strictly catch the filesystem error and raise a FileNotFoundError.

def test_parse_input_file_not_found(tmp_path):
    # We specify a target input path that does not exist on disk.
    non_existent_input = tmp_path / "non_existent.json"
    
    # We provide a valid auxiliary schema file to isolate the input check.
    schema_file = tmp_path / "schema.json"
    schema_file.write_text('{"type": "object"}')

    # Asserting that a FileNotFoundError is raised with appropriate diagnostics.
    with pytest.raises(FileNotFoundError, match="is not a valid file"):
        parse_input_file(non_existent_input, schema_file)


# ==============================================================================
# Scenario 2: Handling Malformed JSON Input
# ==============================================================================
# If the input file is structurally corrupted or contains invalid JSON syntax,
# the JSON decoder failure must be caught and re-raised as a ValueError.

def test_parse_input_file_invalid_json(tmp_path):
    # We write malformed JSON data to our test input file.
    bad_input = tmp_path / "bad.json"
    bad_input.write_text("{ invalid json content")
    
    schema_file = tmp_path / "schema.json"
    schema_file.write_text('{"type": "object"}')

    # Asserting that a ValueError is raised detailing the decoding failure.
    with pytest.raises(ValueError, match="Failed to decode JSON from input file"):
        parse_input_file(bad_input, schema_file)


# ==============================================================================
# Scenario 3: Enforcing the No-Default Schema Policy (None Check)
# ==============================================================================
# Under the strict no-default policy, schema paths cannot be omitted or set to None;
# providing None must immediately trigger a configuration ValueError.

def test_parse_input_file_schema_none(tmp_path):
    # We create a valid input payload file.
    good_input = tmp_path / "input.json"
    good_input.write_text('{"key": "value"}')

    # Asserting that passing None for the schema path raises a ValueError.
    with pytest.raises(ValueError, match="Schema path must be explicitly provided"):
        parse_input_file(good_input, None)


# ==============================================================================
# Scenario 4: Handling Missing Schema Files
# ==============================================================================
# If an explicit schema path is provided but points to a missing file,
# the parser must raise a FileNotFoundError.

def test_parse_input_file_schema_not_found(tmp_path):
    good_input = tmp_path / "input.json"
    good_input.write_text('{"key": "value"}')
    
    # We point to a schema file path that has not been created on disk.
    non_existent_schema = tmp_path / "non_existent_schema.json"

    # Asserting that a FileNotFoundError is raised.
    with pytest.raises(FileNotFoundError, match="is not a valid file"):
        parse_input_file(good_input, non_existent_schema)


# ==============================================================================
# Scenario 5: Schema Validation Enforcement
# ==============================================================================
# When input data violates the type constraints defined in the JSON schema,
# a schema validation error must be caught and raised as a descriptive ValueError.

def test_parse_input_file_validation_error(tmp_path):
    good_input = tmp_path / "input.json"
    # We supply an integer where the schema expects a string.
    good_input.write_text('{"key": 123}')

    schema_file = tmp_path / "schema.json"
    schema = {
        "type": "object",
        "properties": {
            "key": {"type": "string"}
        },
        "required": ["key"]
    }
    schema_file.write_text(json.dumps(schema))

    # Asserting that a schema validation ValueError is raised.
    with pytest.raises(ValueError, match="Invalid configuration schema"):
        parse_input_file(good_input, schema_file)


# ==============================================================================
# Scenario 6: Successful Parsing and Validation (Happy Path)
# ==============================================================================
# When both the input payload and schema are valid and well-formed, the parser
# successfully loads and returns the parsed dictionary.

def test_parse_input_file_success(tmp_path):
    good_input = tmp_path / "input.json"
    payload = {"key": "valid_string"}
    good_input.write_text(json.dumps(payload))

    schema_file = tmp_path / "schema.json"
    schema = {
        "type": "object",
        "properties": {
            "key": {"type": "string"}
        },
        "required": ["key"]
    }
    schema_file.write_text(json.dumps(schema))

    # Executing the parser on valid inputs.
    result = parse_input_file(good_input, schema_file)
    
    # Verifying that the returned dictionary matches the expected payload.
    assert result == payload
