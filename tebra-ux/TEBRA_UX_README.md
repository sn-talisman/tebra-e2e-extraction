# Tebra UX - System Architecture & Developer Guide

This document provides a comprehensive overview of the Tebra UX system, focusing on the schema relationships, API architecture, and frontend components. It is designed to help new developers (and AI agents) quickly understand the critical aspects of the codebase.

## 1. Core Schema & Data Linking (CRITICAL)

The most critical aspect of this system is the relationship between `cmn_practice` and `cmn_location`.

### The GUID Mismatch
*   **Problem:** The `cmn_practice` table contains high-level practice info with a `practice_guid`. However, operational data (payments, encounters, claims) is often linked to `cmn_location` via a `location_guid` (sometimes also called `practice_guid` in other tables like `dbt_tables`).
*   **Resolution (The "Name Match" Link):** We link `cmn_practice` to `cmn_location` by matching the absolute **Name** string.
    *   `cmn_practice.name` <==> `cmn_location.name`
    *   Once linked, we use the `cmn_location.location_guid` to query all downstream tables.

### Key Queries
When fetching data for a practice, always:
1.  Receive `practice_guid` (from frontend).
2.  Resolve it to `location_guid`(s) via name match:
    ```sql
    SELECT l.location_guid 
    FROM tebra.cmn_practice p
    JOIN tebra.cmn_location l ON p.name = l.name
    WHERE p.practice_guid = %s
    ```
3.  Use the resolved `location_guid` to query data tables (e.g., `clin_encounter`, `fin_claim_line`, `fin_era_report`) using `ANY(%s::uuid[])`.

## 2. Backend Architecture (`backend/app/api`)

### `practices.py`
This module handles the main dashboard and tab data.
*   **`get_practices` (Performance Optimized)**:
    *   Uses a **Multi-Step Query Strategy** instead of a single giant join.
    *   Step 1: Fetch base practice list.
    *   Step 2: Fetch ERA counts & locations in a separate aggregation.
    *   Step 3: Fetch Encounter counts via name match.
    *   *Result:* Reduces load time from >15s to ~0.1s.
*   **Tab Endpoints**:
    *   `/{guid}/patients`: Links via `clin_encounter.location_guid`.
    *   `/{guid}/encounters`: Links via `clin_encounter.location_guid`.
    *   `/{guid}/claims`: Links via `fin_claim_line.practice_guid` (which is actually a location GUID). 
        *   Supports `paid_only=True` filter to show only `paid_amount > 0`.

### `financial_metrics.py`
*   Calculates key KPIs (AR Days, Net Collection Rate, Denial Rate).
*   Correctly uses the "Name Match" strategy to resolve GUIDs before calculation.

## 3. Frontend Architecture (`frontend/src/pages`)

### `Practices.jsx`
The main dashboard controller.
*   **State Management**: Manages `selectedPractice`, `activeTab` (Patients, Encounters, Claims, Financial), and modal visibility.
*   **Claims Filter**: Implements "Show only paid claims" checkbox, passing `paid_only=true` to the API.
*   **Modals**:
    *   `PatientDetailsModal`: Fetches full patient history. **Note:** Parent passes `patientGuid`, modal fetches its own data.
    *   `ClaimDetailsModal`: Shows claim lines + ERA payments (deductibles shown as Patient Resp).
    *   `EncounterDetailsModal`: Shows diagnosis and procedure codes.

## 4. Notable Implementation Details

### Claims "Paid Amount" Logic
*   **Issue:** Users reported "Paid as $0" for claims.
*   **Cause:** Many claims are fully applied to Deductible (Insurance Paid = 0, Patient Resp > 0).
*   **UX Solution:** 
    1.  The "Paid" column strictly shows Insurance Paid.
    2.  The "Show only paid claims" filter allows users to hide deductible-only claims.
    3.  The **Claim Details Modal** explicitly breaks down Insurance Paid vs. Patient Responsibility.

## 5. Deployment / Verification
*   **Backend**: `uvicorn app.main:app --reload`
*   **Frontend**: `npm run dev`
*   **Database**: PostgreSQL (`tebra_dw` database, schema `tebra`).

---
**Tag:** `UX - base functionality complete`
**Date:** 2026-02-07
