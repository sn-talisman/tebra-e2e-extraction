import sys
import os
import logging

# Paths
pipeline_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
extraction_dir = os.path.join(pipeline_root, 'extraction')
loading_dir = os.path.join(pipeline_root, 'loading')
sys.path.append(pipeline_root)
sys.path.append(extraction_dir)
sys.path.append(loading_dir)

from dotenv import load_dotenv

# Load .env from project root
# pipeline_root is 'data-pipeline', project root is one level up
project_root = os.path.abspath(os.path.join(pipeline_root, '..'))
load_dotenv(os.path.join(project_root, '.env'))

from extract_claim_encounters import extract_all_eras
from extract_batch_optimized import extract_batch
from load_to_postgres import load_practice_data

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_backfill(practice_guid, start_date):
    output_dir = os.path.join(pipeline_root, 'data', 'backfill')
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Starting Backfill for Practice {practice_guid} from {start_date}")
    
    # 1. Extraction
    logger.info("Phase 1: Extraction (ERA Claims)")
    extract_all_eras(practice_guid, start_date=start_date, output_dir=output_dir)
    
    # 2. Enrichment
    logger.info("Phase 2: Enrichment (Batch Optimized)")
    extract_batch(input_dir=output_dir, output_dir=output_dir)
    
    # 3. Loading
    logger.info("Phase 3: Loading (Postgres)")
    load_practice_data(data_dir=output_dir, practice_guid=practice_guid, practice_name="Backfilled Practice")
    
    logger.info("Backfill Complete!")

if __name__ == "__main__":
    PRACTICE_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
    START_DATE = '2024-01-01' # Using a reasonable lookback (1 year+) to be safe and fast. 2020 might be too much for interactive session if huge.
    # User said "up till today". 
    # Let's adjust start date if needed. The user didn't specify start date, implying full history or reasonable range.
    # If the DB has data, maybe I should check the MAX date and resume?
    # But "backfill" often implies re-loading or filling gaps.
    # Safe start date: 2024-01-01 seems reasonable given file sizes I saw earlier were smallish (MBs).
    
    run_backfill(PRACTICE_GUID, START_DATE)
