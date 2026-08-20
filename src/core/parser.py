"""
Input parsing and schema validation module.
"""

import json
from pathlib import Path

import jsonschema


def parse_input_file(input_path: Path, schema_path: Path = None) -> dict:
    """
    Loads, parses, and validates the input JSON file against the JSON schema.
    """
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input path {input_path} is not a valid file.")

    with open(input_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode JSON from {input_path}: {e}")

    # Validate against schema if available
    if schema_path is None:
        schema_path = Path("schema/flow_analysis_engine_input_schema.json")

    if schema_path.is_file():
        with open(schema_path, "r", encoding="utf-8") as sf:
            schema_data = json.load(sf)
            jsonschema.validate(instance=data, schema=schema_data)

    return data
