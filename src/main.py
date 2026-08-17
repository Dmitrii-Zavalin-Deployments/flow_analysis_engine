"""
Main orchestration script for the flow analysis and visualization engine.
Handles CLI arguments, coordinates input parsing, numerical processing,
headless rendering, and output generation.
"""

import argparse
import json
import sys
from pathlib import Path

from src.core.parser import parse_input_file
from src.core.processor import process_flow_data
from src.visualization.renderer import render_visualization


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
        print(f"❌ Error: Input file not found at {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"🚀 Loading input data from: {input_path}")
    try:
        raw_data = parse_input_file(input_path)
    except Exception as e:
        print(f"❌ Error parsing input file: {e}", file=sys.stderr)
        sys.exit(1)

    print("⚙️ Running flow analysis processor...")
    try:
        processed_results = process_flow_data(raw_data)
    except Exception as e:
        print(f"❌ Error during flow processing: {e}", file=sys.stderr)
        sys.exit(1)

    print("🎨 Executing headless rendering and visualization pipeline...")
    try:
        render_visualization(raw_data, processed_results, output_dir=input_dir)
    except Exception as e:
        print(f"⚠️ Warning: Visualization rendering encountered an issue: {e}", file=sys.stderr)

    print(f"💾 Writing output results to: {output_path}")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(processed_results, f, indent=2)
    except Exception as e:
        print(f"❌ Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    print("✅ Pipeline execution completed successfully.")


if __name__ == "__main__":
    main()
