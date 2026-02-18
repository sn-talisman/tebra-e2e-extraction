import sys
import os
import pytest
import importlib.util

# Paths
pipeline_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
extraction_dir = os.path.join(pipeline_root, 'extraction')
core_dir = os.path.join(pipeline_root, 'core')
loading_dir = os.path.join(pipeline_root, 'loading')
data_dir = os.path.join(pipeline_root, 'data')

def test_critical_scripts_exist():
    # Check that key scripts are present in their new locations
    assert os.path.exists(os.path.join(core_dir, 'orchestrator.py')), "Orchestrator missing"
    assert os.path.exists(os.path.join(extraction_dir, 'extract_batch_optimized.py')), "Extract batch script missing"
    assert os.path.exists(os.path.join(loading_dir, 'load_to_postgres.py')), "Loader script missing"

def test_data_directory_structure():
    # Ensure data directory exists
    assert os.path.exists(data_dir), "Data directory missing in data-pipeline"
    
def test_db_config_loadable():
    # Try to import DB_CONFIG to verify it's accessible
    sys.path.append(loading_dir)
    try:
        from load_to_postgres import DB_CONFIG
        assert isinstance(DB_CONFIG, dict)
        assert "dbname" in DB_CONFIG
    except ImportError as e:
        pytest.fail(f"Failed to import DB_CONFIG: {e}")
    finally:
        sys.path.pop()
