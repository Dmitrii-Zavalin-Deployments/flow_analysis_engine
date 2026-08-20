"""
Conftest Module: Shared Pytest Fixtures and Environment Setup
==============================================================

Description:
    Provides shared fixtures for patching module signatures and establishing 
    complete zero-mock integration test environments, including schemas, 
    configurations, simulation ZIP archives, and input payloads.
"""

import io
import json
import zipfile

import numpy as np
import pytest

import src.core.spatial_probe
import src.visualization.zip_field_renderer


@pytest.fixture(autouse=True)
def setup_module_signature_defaults():
    """
    Provides default patching for core sub-modules where
    functions are invoked under strict signatures.
    """
    orig_spatial = src.core.spatial_probe.analyze_spatial_intervals
    orig_zip_render = src.visualization.zip_field_renderer.render_fields_from_zip

    def patched_spatial(zip_path, grid_cfg, config_path):
        return orig_spatial(zip_path, grid_cfg, config_path)

    def patched_zip_render(zip_p, output_dir, grid_bounds=(0.0, 10.0, 0.0, 10.0, 0.0, 10.0), colormap_name="viridis"):
        return orig_zip_render(zip_p, output_dir, grid_bounds, colormap_name)

    src.core.spatial_probe.analyze_spatial_intervals = patched_spatial
    src.visualization.zip_field_renderer.render_fields_from_zip = patched_zip_render

    yield

    src.core.spatial_probe.analyze_spatial_intervals = orig_spatial
    src.visualization.zip_field_renderer.render_fields_from_zip = orig_zip_render


@pytest.fixture
def pipeline_test_environment(tmp_path):
    """
    Prepares the complete test environment and file hierarchy on disk,
    including schemas, config files, simulation binary archives, and input payloads.
    """
    # We construct the real project directory hierarchy on disk to mirror production layout.
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    schema_dir = repo_root / "schema"
    schema_dir.mkdir()
    config_dir = repo_root / "config"
    config_dir.mkdir()
    input_dir = repo_root / "data_run"
    input_dir.mkdir()

    # We write the required JSON schema files for input validation and configuration compliance.
    input_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["config", "inputs"],
        "properties": {
            "config": {"type": "object"},
            "inputs": {
                "type": "object",
                "required": ["grid", "mask", "physical_constraints", "zip_filename"]
            }
        }
    }
    (schema_dir / "flow_analysis_engine_input_schema.json").write_text(json.dumps(input_schema))

    config_schema = {"type": "object"}
    (schema_dir / "flow_analysis_engine_config_schema.json").write_text(json.dumps(config_schema))

    # We define and write the spatial configuration file containing grid bounds and coordinate ranges.
    config_data = {
        "grid_bounds": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
        "x_range": [0.0, 0.5],
        "y_range": [0.0, 0.5],
        "z_range": [0.0, 0.5]
    }
    (config_dir / "config.json").write_text(json.dumps(config_data))

    # We generate a real simulation ZIP archive containing valid NumPy binary arrays (.npy) with proper headers.
    zip_path = input_dir / "simulation_results.zip"
    u_field = np.ones((2, 2, 2), dtype=float) * 2.5
    p_field = np.full((2, 2, 2), 101325.0, dtype=float)

    with zipfile.ZipFile(zip_path, "w") as zf:
        u_buffer = io.BytesIO()
        np.save(u_buffer, u_field)
        zf.writestr("u_step_000005.npy", u_buffer.getvalue())

        p_buffer = io.BytesIO()
        np.save(p_buffer, p_field)
        zf.writestr("p_step_000005.npy", p_buffer.getvalue())

    # We formulate and write the input payload JSON containing config, grid parameters, fluid masks, and constraints.
    input_payload = {
        "config": {
            "mode": "production",
            "version": "2.0"
        },
        "inputs": {
            "grid": {
                "nx": 2, "ny": 2, "nz": 2,
                "x_min": 0.0, "x_max": 1.0,
                "y_min": 0.0, "y_max": 1.0,
                "z_min": 0.0, "z_max": 1.0
            },
            "mask": [1, -1, 0, 1, 1, 0, -1, 1],
            "physical_constraints": {
                "min_velocity": 0.0,
                "max_velocity": 10.0,
                "min_pressure": 0.0,
                "max_pressure": 200000.0
            },
            "zip_filename": "simulation_results.zip"
        }
    }
    input_file = input_dir / "input_run.json"
    output_file = input_dir / "output_result.json"
    input_file.write_text(json.dumps(input_payload))

    return {
        "input_dir": input_dir,
        "input_file": input_file,
        "output_file": output_file,
        "repo_root": repo_root
    }
