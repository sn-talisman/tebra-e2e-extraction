# Tebra E2E Extraction

This repository contains the ETL pipeline for extracting patient, encounter, and financial data from Tebra's Snowflake Data Warehouse and mapping it to a 360-degree patient view.

## Project Structure

*   **/src**: Helper modules for connections and parsing.
*   `extract_*.py`: The core sequential extraction scripts (Steps 1-4).
*   `generate_360_view.py`: Generates the Markdown report for an encounter.
*   `schema_architecture.md`: Visual diagram of the table relationships.

## How to Run (Phase 1)

1.  **Environment**: Ensure `.env` contains your Snowflake credentials.
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run Extraction** (Sequential):
    ```bash
    python extract_active_practices.py
    python extract_eras_rejections.py
    python extract_claim_encounters.py
    python extract_encounter_details.py
    ```
4.  **Generate Report**:
    ```bash
    python generate_360_view.py
    ```

## Phase 2 (Coming Soon)
We are moving to a localized Postgres staging database. See `implementation_plan.md` for details.
