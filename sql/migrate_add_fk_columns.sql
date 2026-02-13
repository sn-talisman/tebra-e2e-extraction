-- ============================================================
-- Migration: Add missing FK-linkage columns to tebra.* schema
-- Aligns local Postgres with Snowflake PM_* GUID linkages
-- Idempotent: uses ADD COLUMN IF NOT EXISTS
-- ============================================================

-- ── 1. cmn_location ── (← PM_SERVICELOCATION) ──────────────
ALTER TABLE tebra.cmn_location
    ADD COLUMN IF NOT EXISTS practice_guid UUID,
    ADD COLUMN IF NOT EXISTS npi VARCHAR(20),
    ADD COLUMN IF NOT EXISTS place_of_service_code VARCHAR(10),
    ADD COLUMN IF NOT EXISTS location_id INTEGER;

-- ── 2. cmn_patient ── (← PM_PATIENT) ───────────────────────
ALTER TABLE tebra.cmn_patient
    ADD COLUMN IF NOT EXISTS practice_guid UUID,
    ADD COLUMN IF NOT EXISTS primary_provider_guid UUID,
    ADD COLUMN IF NOT EXISTS default_location_guid UUID,
    ADD COLUMN IF NOT EXISTS referring_provider_guid UUID,
    ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;

-- ── 3. cmn_provider ── (← PM_DOCTOR) ───────────────────────
ALTER TABLE tebra.cmn_provider
    ADD COLUMN IF NOT EXISTS practice_guid UUID,
    ADD COLUMN IF NOT EXISTS provider_id INTEGER,
    ADD COLUMN IF NOT EXISTS taxonomy_code VARCHAR(20);

-- ── 4. clin_encounter ── (← PM_ENCOUNTER) ──────────────────
ALTER TABLE tebra.clin_encounter
    ADD COLUMN IF NOT EXISTS practice_guid UUID,
    ADD COLUMN IF NOT EXISTS appointment_guid UUID,
    ADD COLUMN IF NOT EXISTS patient_case_id BIGINT,
    ADD COLUMN IF NOT EXISTS place_of_service_code VARCHAR(10);

-- Fix referring_provider_guid type: text → UUID
-- (only runs if the column is currently text)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'tebra'
          AND table_name = 'clin_encounter'
          AND column_name = 'referring_provider_guid'
          AND data_type = 'text'
    ) THEN
        ALTER TABLE tebra.clin_encounter
            ALTER COLUMN referring_provider_guid TYPE UUID
            USING CASE
                WHEN referring_provider_guid IS NOT NULL
                     AND referring_provider_guid <> ''
                THEN referring_provider_guid::UUID
                ELSE NULL
            END;
    END IF;
END $$;

-- ── 5. clin_encounter_diagnosis ── (← PM_ENCOUNTERDIAGNOSIS) 
ALTER TABLE tebra.clin_encounter_diagnosis
    ADD COLUMN IF NOT EXISTS practice_guid UUID,
    ADD COLUMN IF NOT EXISTS encounter_diagnosis_id BIGINT,
    ADD COLUMN IF NOT EXISTS encounter_guid UUID,
    ADD COLUMN IF NOT EXISTS diagnosis_dict_id BIGINT;

-- ── 6. fin_claim_line ── (← PM_CLAIM) ──────────────────────
ALTER TABLE tebra.fin_claim_line
    ADD COLUMN IF NOT EXISTS patient_guid UUID,
    ADD COLUMN IF NOT EXISTS encounter_procedure_id BIGINT;

-- ── 7. fin_era_bundle ── ────────────────────────────────────
ALTER TABLE tebra.fin_era_bundle
    ADD COLUMN IF NOT EXISTS practice_guid UUID;

-- ── 8. fin_era_report ── ────────────────────────────────────
-- Fix practice_guid type: text → UUID
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'tebra'
          AND table_name = 'fin_era_report'
          AND column_name = 'practice_guid'
          AND data_type = 'text'
    ) THEN
        ALTER TABLE tebra.fin_era_report
            ALTER COLUMN practice_guid TYPE UUID
            USING CASE
                WHEN practice_guid IS NOT NULL
                     AND practice_guid <> ''
                THEN practice_guid::UUID
                ELSE NULL
            END;
    END IF;
END $$;

-- ── 9. ref_insurance_policy ── (← PM_INSURANCEPOLICY) ──────
ALTER TABLE tebra.ref_insurance_policy
    ADD COLUMN IF NOT EXISTS practice_guid UUID,
    ADD COLUMN IF NOT EXISTS patient_case_id BIGINT,
    ADD COLUMN IF NOT EXISTS policy_guid UUID,
    ADD COLUMN IF NOT EXISTS precedence INTEGER;


-- ============================================================
-- FK CONSTRAINTS
-- Using NOT VALID to skip checking existing rows (backfill may
-- not be complete yet). Run VALIDATE CONSTRAINT after backfill.
-- ============================================================

-- cmn_location → cmn_practice
DO $$ BEGIN
    ALTER TABLE tebra.cmn_location
        ADD CONSTRAINT fk_location_practice
        FOREIGN KEY (practice_guid) REFERENCES tebra.cmn_practice(practice_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- cmn_patient → cmn_practice
DO $$ BEGIN
    ALTER TABLE tebra.cmn_patient
        ADD CONSTRAINT fk_patient_practice
        FOREIGN KEY (practice_guid) REFERENCES tebra.cmn_practice(practice_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- cmn_patient → cmn_provider (primary)
DO $$ BEGIN
    ALTER TABLE tebra.cmn_patient
        ADD CONSTRAINT fk_patient_primary_provider
        FOREIGN KEY (primary_provider_guid) REFERENCES tebra.cmn_provider(provider_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- cmn_patient → cmn_location (default)
DO $$ BEGIN
    ALTER TABLE tebra.cmn_patient
        ADD CONSTRAINT fk_patient_default_location
        FOREIGN KEY (default_location_guid) REFERENCES tebra.cmn_location(location_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- cmn_provider → cmn_practice
DO $$ BEGIN
    ALTER TABLE tebra.cmn_provider
        ADD CONSTRAINT fk_provider_practice
        FOREIGN KEY (practice_guid) REFERENCES tebra.cmn_practice(practice_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- clin_encounter → cmn_practice
DO $$ BEGIN
    ALTER TABLE tebra.clin_encounter
        ADD CONSTRAINT fk_encounter_practice
        FOREIGN KEY (practice_guid) REFERENCES tebra.cmn_practice(practice_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- clin_encounter_diagnosis → cmn_practice
DO $$ BEGIN
    ALTER TABLE tebra.clin_encounter_diagnosis
        ADD CONSTRAINT fk_encdiag_practice
        FOREIGN KEY (practice_guid) REFERENCES tebra.cmn_practice(practice_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- fin_claim_line → cmn_practice
DO $$ BEGIN
    ALTER TABLE tebra.fin_claim_line
        ADD CONSTRAINT fk_claim_practice
        FOREIGN KEY (practice_guid) REFERENCES tebra.cmn_practice(practice_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- fin_claim_line → cmn_patient
DO $$ BEGIN
    ALTER TABLE tebra.fin_claim_line
        ADD CONSTRAINT fk_claim_patient
        FOREIGN KEY (patient_guid) REFERENCES tebra.cmn_patient(patient_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- fin_era_bundle → cmn_practice
DO $$ BEGIN
    ALTER TABLE tebra.fin_era_bundle
        ADD CONSTRAINT fk_era_bundle_practice
        FOREIGN KEY (practice_guid) REFERENCES tebra.cmn_practice(practice_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- fin_era_bundle → fin_era_report
DO $$ BEGIN
    ALTER TABLE tebra.fin_era_bundle
        ADD CONSTRAINT fk_era_bundle_report
        FOREIGN KEY (era_report_id) REFERENCES tebra.fin_era_report(era_report_id)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ref_insurance_policy → cmn_practice
DO $$ BEGIN
    ALTER TABLE tebra.ref_insurance_policy
        ADD CONSTRAINT fk_policy_practice
        FOREIGN KEY (practice_guid) REFERENCES tebra.cmn_practice(practice_guid)
        NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ============================================================
-- INDEXES on new FK columns
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_location_practice ON tebra.cmn_location(practice_guid);
CREATE INDEX IF NOT EXISTS idx_patient_practice ON tebra.cmn_patient(practice_guid);
CREATE INDEX IF NOT EXISTS idx_patient_primary_prov ON tebra.cmn_patient(primary_provider_guid);
CREATE INDEX IF NOT EXISTS idx_provider_practice ON tebra.cmn_provider(practice_guid);
CREATE INDEX IF NOT EXISTS idx_encounter_practice ON tebra.clin_encounter(practice_guid);
CREATE INDEX IF NOT EXISTS idx_encdiag_practice ON tebra.clin_encounter_diagnosis(practice_guid);
CREATE INDEX IF NOT EXISTS idx_claim_practice ON tebra.fin_claim_line(practice_guid);
CREATE INDEX IF NOT EXISTS idx_claim_patient ON tebra.fin_claim_line(patient_guid);
CREATE INDEX IF NOT EXISTS idx_era_bundle_practice ON tebra.fin_era_bundle(practice_guid);
CREATE INDEX IF NOT EXISTS idx_era_bundle_report ON tebra.fin_era_bundle(era_report_id);
CREATE INDEX IF NOT EXISTS idx_policy_practice ON tebra.ref_insurance_policy(practice_guid);

-- Done!
