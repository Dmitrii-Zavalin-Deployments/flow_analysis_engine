"""
Input parsing module for loading and validating configuration and input JSON files.
"""

import json
from pathlib import Path


def parse_input_file(input_path: Path) -> dict:
    """
    Loads and parses the input JSON file for the flow analysis engine.
    
    Args:
        input_path (Path): Path to the target input JSON file.
        
    Returns:
        dict: Parsed dictionary containing the input parameters and simulation data.
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Input path {input_path} is not a valid file.")

    with open(input_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode JSON from {input_path}: {e}")

    return data
