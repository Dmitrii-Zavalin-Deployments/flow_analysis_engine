"""
Input parsing and schema validation module.
"""

import json
import logging
from pathlib import Path

import jsonschema

logger = logging.getLogger("flow_engine.parser")


def parse_input_file(input_path: Path, schema_path: Path) -> dict:
    """
    Loads, parses, and validates the input JSON file against the JSON schema.
    Adheres to the no-default policy: both input and schema paths must be explicitly provided.
    """
    logger.info("Initializing input parsing and schema validation module.")
    input_path = Path(input_path)
    if not input_path.is_file():
        logger.error("Input path is not a valid file.")
        raise FileNotFoundError(f"Input path {input_path} is not a valid file.")

    logger.info("Opening and parsing input JSON file.")
    with open(input_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON from input file.")
            raise ValueError(f"Failed to decode JSON from input file: {e}")

    # No-default policy: schema_path must be explicitly provided
    if schema_path is None:
        logger.error("Schema path was not provided (no-default policy enforced).")
        raise ValueError("Schema path must be explicitly provided.")

    schema_path = Path(schema_path)
    if not schema_path.is_file():
        logger.error("Schema path is not a valid file.")
        raise FileNotFoundError(f"Schema path {schema_path} is not a valid file.")

    logger.info("Validating input data against the provided JSON schema.")
    with open(schema_path, "r", encoding="utf-8") as sf:
        schema_data = json.load(sf)
        jsonschema.validate(instance=data, schema=schema_data)

    logger.info("Input file parsed and validated successfully.")
    return data
