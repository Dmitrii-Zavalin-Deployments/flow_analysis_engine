"""
Main orchestration script for the flow analysis and visualization engine.
Handles CLI arguments, schema validation, numerical processing, headless rendering,
in-memory ZIP field visualization, and merged output generation.
"""

import argparse
import json
import logging
import sys
import zipfile
from pathlib import Path

# Configure root logger to output INFO-level logs to stderr
logging.basicConfig(level=logging.INFO, format="%(message)s")

from src.core.parser import parse_input_file
from src.core.processor import process_flow_data
from src.visualization.renderer import render_visualization
from src.visualization.zip_field_renderer import render_fields_from_zip

# Configure structured module logger
logger = logging.getLogger("flow_engine.main")


def main() -> None:
    parser = argparse.ArgumentParser(description="Flow Analysis & Visualization Engine CLI")
    parser.add_argument(
        "--input_output_folder",
        required=True,
        help="Path to the directory containing input data and output targets."
    )
    parser.add_argument(
        "--input_file_name",
        required=True,
        help="Name of the input JSON file."
    )
    parser.add_argument(
        "--output_file_name",
        required=True,
        help="Name of the output JSON result file."
    )

    args = parser.parse_args()

    input_dir = Path(args.input_output_folder)
    input_path = input_dir / args.input_file_name
    output_path = input_dir / args.output_file_name

    repo_root = Path(__file__).resolve().parent.parent

    # Dynamically resolve root: support temporary pytest fixture roots and production repos
    base_dir = input_dir.parent if (input_dir.parent / "schema").exists() else repo_root
    schema_dir = base_dir / "schema"

    # Optional configuration validation against flow_analysis_engine_config_schema.json
    config_path = base_dir / "config" / "config.json"
    config_schema_path = schema_dir / "flow_analysis_engine_config_schema.json"
    config_data = {}
    if config_path.exists() and config_schema_path.exists():
        logger.info("Initializing configuration parsing and schema validation.")
        try:
            config_data = parse_input_file(config_path, schema_path=config_schema_path)
            logger.info("Configuration file validated successfully.")
        except (FileNotFoundError, ValueError, json.JSONDecodeError, OSError) as e:
            logger.error("Error validating config file against schema: %s", e)
            sys.exit(1)

    if not input_path.exists():
        logger.error("Input file not found at target path.")
        sys.exit(1)

    logger.info("Initializing input parsing and schema validation module.")
    try:
        schema_path = schema_dir / "flow_analysis_engine_input_schema.json"

        raw_data = parse_input_file(input_path, schema_path=schema_path)
        logger.info("Successfully parsed and validated input data.")
    except (FileNotFoundError, ValueError, json.JSONDecodeError, OSError) as e:
        logger.error("Error validating input file against schema: %s", e)
        sys.exit(1)

    logger.info("Initializing flow analysis processor and ZIP inspection module.")
    try:
        processed_results = process_flow_data(raw_data, input_dir=input_dir)
        logger.info("Successfully executed flow processing and spatial probing.")
    except (FileNotFoundError, ValueError, KeyError, OSError) as e:
        logger.error("Error during flow processing: %s", e)
        sys.exit(1)

    logger.info("Initializing headless rendering and visualization pipeline.")
    try:
        render_visualization(raw_data, processed_results, output_dir=input_dir)
        logger.info("Voxel visualization rendered successfully.")
    except (ValueError, OSError, RuntimeError) as e:
        logger.warning("Voxel visualization rendering encountered an issue: %s", e)

    # In-memory ZIP field rendering for simulation .npy results
    try:
        inputs_dict = raw_data.get("inputs", raw_data)

        # Prioritize dynamic input grid bounds over static config.json template values
        grid_bounds = None
        if isinstance(inputs_dict, dict) and "grid" in inputs_dict:
            g = inputs_dict["grid"]
            try:
                grid_bounds = (
                    float(g["x_min"]), float(g["x_max"]),
                    float(g["y_min"]), float(g["y_max"]),
                    float(g["z_min"]), float(g["z_max"])
                )
                config_data["grid_bounds"] = list(grid_bounds)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning("Failed to parse grid bounds from inputs.grid: %s", e)

        if grid_bounds is None and "grid_bounds" in config_data:
            gb = config_data["grid_bounds"]
            grid_bounds = tuple(float(v) for v in gb)

        if grid_bounds is None:
            raise KeyError("No valid 'grid' in inputs or 'grid_bounds' in config_data found.")

        # Check 'results' first, then fallback to 'inputs' for zip_filename location
        results_dict = raw_data.get("results", {}) if isinstance(raw_data, dict) else {}
        zip_filename = results_dict.get("zip_filename")
        if not zip_filename and isinstance(inputs_dict, dict):
            zip_filename = inputs_dict.get("zip_filename")

        if zip_filename:
            zip_path = input_dir / zip_filename
            if zip_path.exists():
                logger.info("Initializing in-memory ZIP field renderer for archive.")
                render_fields_from_zip(zip_path, output_dir=input_dir, grid_bounds=grid_bounds)
                logger.info("ZIP field rendering completed successfully.")
            else:
                logger.warning("Configured zip archive path does not exist.")
    except (FileNotFoundError, KeyError, zipfile.BadZipFile, OSError, ValueError) as e:
        logger.error("Error during ZIP field rendering or strict grid boundary resolution: %s", e)
        sys.exit(1)

    # Construct merged output structure without double-nesting inputs
    final_output = {
        "inputs": raw_data.get("inputs", raw_data),
        "results": processed_results
    }

    logger.info("Writing merged output results to target destination.")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2)
        logger.info("Successfully wrote final output file.")
    except (OSError, TypeError, ValueError) as e:
        logger.error("Error writing output file: %s", e)
        sys.exit(1)

    logger.info("Pipeline execution completed successfully.")


if __name__ == "__main__":  # pragma: no cover
    main()
