-- ============================================================
-- Schema Definition for Tebra E2E Extraction
-- Mirrors Snowflake KAREO.TALISMANSOLUTIONS.PM_* GUID linkages
-- ============================================================

CREATE SCHEMA IF NOT EXISTS tebra;

-- ==========================================
-- 1. Common Entities (cmn_)
-- ==========================================

CREATE TABLE IF NOT EXISTS tebra.cmn_practice (
    practice_guid UUID PRIMARY KEY,
    name VARCHAR(200),
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS tebra.cmn_patient (
    patient_guid UUID PRIMARY KEY,
    patient_id VARCHAR(50),              -- Display ID (e.g. 108301)
    full_name VARCHAR(150),              -- "LAST, FIRST"
    case_id VARCHAR(50),                 -- Link to Insurance Case
    dob DATE,
    gender TEXT,
    address_line1 TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,

    -- FK linkages (from PM_PATIENT)
    practice_guid UUID REFERENCES tebra.cmn_practice(practice_guid),
    primary_provider_guid UUID,          -- → cmn_provider (deferred, circular)
    default_location_guid UUID,          -- → cmn_location (deferred, circular)
    referring_provider_guid UUID,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS tebra.cmn_provider (
    provider_guid UUID PRIMARY KEY,
    npi VARCHAR(20),
    name VARCHAR(150),

    -- FK linkages (from PM_DOCTOR)
    practice_guid UUID REFERENCES tebra.cmn_practice(practice_guid),
    provider_id INTEGER,                 -- Snowflake DOCTORID
    taxonomy_code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS tebra.cmn_location (
    location_guid UUID PRIMARY KEY,
    name VARCHAR(150),
    address_block JSONB,                 -- {address: "...", city: "...", state: "..."}

    -- FK linkages (from PM_SERVICELOCATION)
    practice_guid UUID REFERENCES tebra.cmn_practice(practice_guid),
    npi VARCHAR(20),
    place_of_service_code VARCHAR(10),
    location_id INTEGER                  -- Snowflake SERVICELOCATIONID
);

-- After cmn_provider and cmn_location exist, add deferred FKs on cmn_patient
ALTER TABLE tebra.cmn_patient
    ADD CONSTRAINT fk_patient_primary_provider
    FOREIGN KEY (primary_provider_guid) REFERENCES tebra.cmn_provider(provider_guid)
    NOT VALID;

ALTER TABLE tebra.cmn_patient
    ADD CONSTRAINT fk_patient_default_location
    FOREIGN KEY (default_location_guid) REFERENCES tebra.cmn_location(location_guid)
    NOT VALID;

-- ==========================================
-- 2. Reference Data (ref_)
-- ==========================================

CREATE TABLE IF NOT EXISTS tebra.ref_insurance_policy (
    policy_key VARCHAR(100) PRIMARY KEY, -- MD5(Policy+Group) or similar unique string
    company_name VARCHAR(150),
    plan_name VARCHAR(150),
    policy_number VARCHAR(50),
    group_number VARCHAR(50),
    start_date DATE,
    end_date DATE,
    copay NUMERIC(18,2),

    -- FK linkages (from PM_INSURANCEPOLICY)
    practice_guid UUID REFERENCES tebra.cmn_practice(practice_guid),
    patient_case_id BIGINT,
    policy_guid UUID,                    -- Snowflake INSURANCEPOLICYGUID
    precedence INTEGER
);

-- ==========================================
-- 3. Clinical Data (clin_)
-- ==========================================

CREATE TABLE IF NOT EXISTS tebra.clin_encounter (
    encounter_id BIGINT PRIMARY KEY,     -- Tebra Integer ID
    encounter_guid UUID,                 -- Tebra GUID
    start_date DATE,
    status VARCHAR(50),
    appt_type VARCHAR(100),
    appt_reason TEXT,
    appt_subject TEXT,
    appt_notes TEXT,
    pos_description TEXT,

    -- Core FK linkages (from PM_ENCOUNTER)
    patient_guid UUID REFERENCES tebra.cmn_patient(patient_guid),
    provider_guid UUID REFERENCES tebra.cmn_provider(provider_guid),
    location_guid UUID REFERENCES tebra.cmn_location(location_guid),
    insurance_policy_key VARCHAR(100) REFERENCES tebra.ref_insurance_policy(policy_key),
    referring_provider_guid UUID,

    -- New FK linkages
    practice_guid UUID REFERENCES tebra.cmn_practice(practice_guid),
    appointment_guid UUID,
    patient_case_id BIGINT,
    place_of_service_code VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS tebra.clin_encounter_diagnosis (
    encounter_id BIGINT REFERENCES tebra.clin_encounter(encounter_id),
    diag_code VARCHAR(20),
    precedence INTEGER,                  -- 1=Primary, 2=Secondary...
    description TEXT,

    -- FK linkages
    practice_guid UUID REFERENCES tebra.cmn_practice(practice_guid),
    encounter_diagnosis_id BIGINT,
    encounter_guid UUID,
    diagnosis_dict_id BIGINT,

    PRIMARY KEY (encounter_id, diag_code)
);

-- ==========================================
-- 4. Financial Data (fin_)
-- ==========================================

CREATE TABLE IF NOT EXISTS tebra.fin_era_report (
    era_report_id VARCHAR(100) PRIMARY KEY,
    file_name TEXT,
    received_date DATE,
    payer_name VARCHAR(200),
    payer_id VARCHAR(100),
    check_number VARCHAR(100),
    check_date DATE,
    total_paid DECIMAL(18, 2),
    payment_method VARCHAR(50),
    practice_guid UUID REFERENCES tebra.cmn_practice(practice_guid),
    denied_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    claim_count_source INTEGER DEFAULT 0
);

-- The "Check" / ERA Bundle
CREATE TABLE IF NOT EXISTS tebra.fin_era_bundle (
    claim_reference_id VARCHAR(100) PRIMARY KEY,
    payer_name VARCHAR(150),
    received_date TIMESTAMP,
    total_paid DECIMAL(18, 2),
    total_patient_resp DECIMAL(18, 2),
    era_report_id VARCHAR(100) REFERENCES tebra.fin_era_report(era_report_id),

    -- FK linkages
    practice_guid UUID REFERENCES tebra.cmn_practice(practice_guid)
);

-- The Tebra Service Line (Child of Bundle)
CREATE TABLE IF NOT EXISTS tebra.fin_claim_line (
    tebra_claim_id BIGINT PRIMARY KEY,   -- The Line ID

    -- Core linkage
    encounter_id BIGINT REFERENCES tebra.clin_encounter(encounter_id),
    claim_reference_id VARCHAR(100),

    -- Details
    proc_code VARCHAR(20),
    description TEXT,
    date_of_service DATE,

    -- Amounts
    billed_amount DECIMAL(18, 2),
    paid_amount DECIMAL(18, 2),
    units INTEGER,

    -- Adjustments
    adjustments_json JSONB,
    adjustment_descriptions TEXT,

    -- Status
    claim_status TEXT,
    payer_status TEXT,

    -- FK linkages
    practice_guid UUID REFERENCES tebra.cmn_practice(practice_guid),
    patient_guid UUID REFERENCES tebra.cmn_patient(patient_guid),
    encounter_procedure_id BIGINT,
    tracking_number TEXT,
    clearinghouse_payer TEXT
);

-- ==========================================
-- 5. Indexes
-- ==========================================

-- Core encounter FKs
CREATE INDEX IF NOT EXISTS idx_enc_patient ON tebra.clin_encounter(patient_guid);
CREATE INDEX IF NOT EXISTS idx_enc_provider ON tebra.clin_encounter(provider_guid);
CREATE INDEX IF NOT EXISTS idx_enc_location ON tebra.clin_encounter(location_guid);
CREATE INDEX IF NOT EXISTS idx_enc_insurance ON tebra.clin_encounter(insurance_policy_key);

-- Claim line FKs
CREATE INDEX IF NOT EXISTS idx_claim_encounter ON tebra.fin_claim_line(encounter_id);
CREATE INDEX IF NOT EXISTS idx_claim_era ON tebra.fin_claim_line(claim_reference_id);

-- Search
CREATE INDEX IF NOT EXISTS idx_pat_name ON tebra.cmn_patient(full_name);
CREATE INDEX IF NOT EXISTS idx_era_payer ON tebra.fin_era_bundle(payer_name);
CREATE INDEX IF NOT EXISTS idx_enc_date ON tebra.clin_encounter(start_date);

-- JSONB
CREATE INDEX IF NOT EXISTS idx_claim_adj ON tebra.fin_claim_line USING GIN (adjustments_json);

-- New FK indexes (practice_guid on all tables)
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
