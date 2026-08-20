"""
Main orchestration script for the flow analysis and visualization engine.
Handles CLI arguments, schema validation, numerical processing, headless rendering,
in-memory ZIP field visualization, and merged output generation.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from src.core.parser import parse_input_file
from src.core.processor import process_flow_data
from src.visualization.renderer import render_visualization
from src.visualization.zip_field_renderer import render_fields_from_zip

# Configure structured module logger
logger = logging.getLogger("flow_engine.main")


def main():
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

    if not input_path.exists():
        logger.error("Input file not found at target path.")
        sys.exit(1)

    logger.info("Initializing input parsing and schema validation module.")
    try:
        raw_data = parse_input_file(input_path)
        logger.info("Successfully parsed and validated input data.")
    except Exception as e:
        logger.error("Error validating input file against schema: %s", e)
        sys.exit(1)

    logger.info("Initializing flow analysis processor and ZIP inspection module.")
    try:
        processed_results = process_flow_data(raw_data, input_dir=input_dir)
        logger.info("Successfully executed flow processing and spatial probing.")
    except Exception as e:
        logger.error("Error during flow processing: %s", e)
        sys.exit(1)

    logger.info("Initializing headless rendering and visualization pipeline.")
    try:
        render_visualization(raw_data, processed_results, output_dir=input_dir)
        logger.info("Voxel visualization rendered successfully.")
    except Exception as e:
        logger.warning("Voxel visualization rendering encountered an issue: %s", e)

    # In-memory ZIP field rendering for simulation .npy results
    zip_filename = (
        raw_data.get("inputs", raw_data).get("zip_filename")
        or raw_data.get("zip_filename")
    )
    if zip_filename:
        zip_path = input_dir / zip_filename
        if zip_path.exists():
            logger.info("Initializing in-memory ZIP field renderer for archive.")
            try:
                render_fields_from_zip(zip_path, output_dir=input_dir)
                logger.info("ZIP field rendering completed successfully.")
            except Exception as e:
                logger.warning("ZIP field rendering encountered an issue: %s", e)
        else:
            logger.warning("Configured zip archive path does not exist.")

    # Construct merged output structure: {"inputs": ..., "results": ...}
    final_output = {
        "inputs": raw_data,
        "results": processed_results
    }

    logger.info("Writing merged output results to target destination.")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2)
        logger.info("Successfully wrote final output file.")
    except Exception as e:
        logger.error("Error writing output file: %s", e)
        sys.exit(1)

    logger.info("Pipeline execution completed successfully.")


if __name__ == "__main__":  # pragma: no cover
    main()
