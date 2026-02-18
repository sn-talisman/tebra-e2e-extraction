import sys
import os
import pytest
from unittest.mock import MagicMock, patch, mock_open

# Paths
pipeline_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
extraction_dir = os.path.join(pipeline_root, 'extraction')
loading_dir = os.path.join(pipeline_root, 'loading')
sys.path.append(extraction_dir)
sys.path.append(loading_dir)

from extract_claim_encounters import extract_all_eras
from extract_batch_optimized import extract_batch
from load_to_postgres import load_practice_data, load_service_lines

# --- Mocks ---



@pytest.fixture
def mock_postgres_conn():
    with patch('load_to_postgres.get_db') as mock_db:
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        yield mock_cursor

@pytest.fixture
def mock_csv_writer():
    with patch('csv.DictWriter') as mock_writer:
        yield mock_writer

# Helper for Selective Open Mocking
original_open = open

def selective_open(filename, mode='r', *args, **kwargs):
    # Only mock files in current/subdirectories or specific project files
    # System files (like /System/Library/...) used by plistlib should use real open
    if 'output' in str(filename) or 'input' in str(filename) or '.csv' in str(filename) or '.jsonl' in str(filename):
        if 'service_lines.csv' in str(filename) and 'r' in mode:
             return mock_open(read_data="LineID_Ref6R,LineID\n123456,1\n").return_value
        return mock_open().return_value
    return original_open(filename, mode, *args, **kwargs)

# --- Tests ---

def test_extract_all_eras(mock_csv_writer):
    # Setup Snowflake Mock Data
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (
            'CUST-1', 'CH-1', 'RPT-1', 'ERA', 'SRC-1', 'Tebra', 0, 
            '<ERA>Content</ERA>', 'file1.835', '2025-01-01', 1, 'PAY-1', 
            'PRAC-1', True, 0, 'RESP', 'Payment', False, 'Addr', 'Payer', 'Title', 100.00
        )
    ]
    
    # Mock connection in the MODULE
    with patch('extract_claim_encounters.get_connection') as mock_conn_func:
        mock_conn_func.return_value.cursor.return_value = mock_cursor
        
        # Mock open with side_effect
        with patch('builtins.open', side_effect=selective_open):
            # Run Extraction
            result = extract_all_eras('PRAC-1', start_date='2025-01-01', output_dir='test_output')
            
            # Verify Snowflake Query
            assert mock_cursor.execute.called
            query_arg = mock_cursor.execute.call_args[0][0]
            assert "FROM PM_CLEARINGHOUSERESPONSE" in query_arg
            assert "PRACTICEGUID = 'PRAC-1'" in query_arg

def test_extract_batch_enrichment():
    mock_cursor = MagicMock()
    
    with patch('extract_batch_optimized.get_connection') as mock_conn_func:
        mock_conn_func.return_value.cursor.return_value = mock_cursor
        
        with patch('builtins.open', side_effect=selective_open):
            with patch('os.path.exists', return_value=True):
                 extract_batch(input_dir='test_input', output_dir='test_output')
                 
    # Verify Enrichment Queries
    assert mock_cursor.execute.called
    queries = [call[0][0] for call in mock_cursor.execute.call_args_list]
    
    # Check if we queried PM_CLAIM with the ID
    claim_query_found = any("FROM PM_CLAIM" in q and "123456" in q for q in queries)
    assert claim_query_found, "Did not query PM_CLAIM for LineID 123456"

def test_load_practice_data(mock_postgres_conn):
     with patch('os.path.exists', return_value=True):
        with patch('builtins.open', side_effect=selective_open):
            # We need to mock csv.DictReader too, because our mock file returns empty or basic string
            # But the 'selective_open' returns a MagicMock which iterates? No.
            # mock_open().return_value is an iterator that yields lines. 
            
            # Let's mock DictReader explicitly to return list of dicts
            with patch('csv.DictReader', return_value=[{'EraReportID': 'R1', 'PracticeGUID': 'P1', 'ClaimID': 'C1'}]): 
                 load_practice_data(data_dir='test_data', practice_guid='P1', practice_name='Test Practice')
                 
    # Verify SQL Execution
     assert mock_postgres_conn.execute.called or mock_postgres_conn.cursor.return_value.execute.called

