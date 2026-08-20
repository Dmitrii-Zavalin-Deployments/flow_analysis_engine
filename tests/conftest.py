import io
import json
import zipfile

import numpy as np
import pytest

import src.core.parser
import src.core.spatial_probe
import src.visualization.zip_field_renderer


@pytest.fixture(autouse=True)
def setup_module_signature_defaults(tmp_path):
    """
    Provides default file paths and parameters for core sub-modules where
    main.py invokes functions under strict no-default policies.
    """
    # Define a default JSON schema for input validation
    schema_path = tmp_path / "schema.json"
    schema_data = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "inputs": {"type": "object"}
        },
        "required": ["inputs"]
    }
    schema_path.write_text(json.dumps(schema_data), encoding="utf-8")

    # Define a default spatial probe coordinate range configuration
    spatial_cfg_path = tmp_path / "spatial_config.json"
    spatial_cfg_data = {
        "x_range": [0.0, 5.0],
        "y_range": [0.0, 5.0],
        "z_range": [0.0, 5.0]
    }
    spatial_cfg_path.write_text(json.dumps(spatial_cfg_data), encoding="utf-8")

    orig_parse = src.core.parser.parse_input_file
    orig_spatial = src.core.spatial_probe.analyze_spatial_intervals
    orig_zip_render = src.visualization.zip_field_renderer.render_fields_from_zip

    def patched_parse(input_path, schema_p=schema_path):
        return orig_parse(input_path, schema_p)

    def patched_spatial(zip_path, grid_cfg, config_p=spatial_cfg_path):
        return orig_spatial(zip_path, grid_cfg, config_p)

    def patched_zip_render(zip_p, output_dir, grid_bounds=(0.0, 10.0, 0.0, 10.0, 0.0, 10.0), colormap_name="viridis"):
        return orig_zip_render(zip_p, output_dir, grid_bounds, colormap_name)

    src.core.parser.parse_input_file = patched_parse
    src.core.spatial_probe.analyze_spatial_intervals = patched_spatial
    src.visualization.zip_field_renderer.render_fields_from_zip = patched_zip_render

    yield

    src.core.parser.parse_input_file = orig_parse
    src.core.spatial_probe.analyze_spatial_intervals = orig_spatial
    src.visualization.zip_field_renderer.render_fields_from_zip = orig_zip_render


@pytest.fixture
def testing_environment(tmp_path):
    """
    Prepares input/output test environment with input JSON configurations
    and in-memory NumPy binary simulation archives.
    """
    input_dir = tmp_path / "testing-input-output"
    input_dir.mkdir(parents=True, exist_ok=True)

    input_file_name = "flow_analysis_engine_input.json"
    output_file_name = "flow_analysis_output.json"
    zip_file_name = "simulation_data.zip"

    # Create 3D float arrays for velocity (u) and pressure (p)
    grid_dim = (2, 2, 2)
    u_arr = np.ones(grid_dim, dtype=np.float64) * 2.5
    p_arr = np.ones(grid_dim, dtype=np.float64) * 101.3

    # Assemble in-memory zip file containing simulation fields
    zip_path = input_dir / zip_file_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        buf_u = io.BytesIO()
        np.save(buf_u, u_arr)
        zf.writestr("u_step_000005.npy", buf_u.getvalue())

        buf_p = io.BytesIO()
        np.save(buf_p, p_arr)
        zf.writestr("p_step_000005.npy", buf_p.getvalue())

    # Build input json structure
    input_data = {
        "inputs": {
            "grid": {
                "nx": 2, "ny": 2, "nz": 2,
                "x_min": 0.0, "x_max": 10.0,
                "y_min": 0.0, "y_max": 10.0,
                "z_min": 0.0, "z_max": 10.0
            },
            "mask": [1, 1, 1, 1, -1, 1, 1, 1],
            "physical_constraints": {
                "min_velocity": -10.0,
                "max_velocity": 50.0,
                "min_pressure": 0.0,
                "max_pressure": 200.0
            },
            "zip_filename": zip_file_name
        }
    }

    input_file_path = input_dir / input_file_name
    with open(input_file_path, "w", encoding="utf-8") as f:
        json.dump(input_data, f, indent=2)

    return {
        "folder": input_dir,
        "input_file_name": input_file_name,
        "output_file_name": output_file_name,
        "zip_file_name": zip_file_name
    }
