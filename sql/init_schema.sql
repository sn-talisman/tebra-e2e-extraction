-- Schema Definition for Tebra E2E Extraction (Final Version)
-- Optimized for 360-View, Normalization, and Speed

CREATE SCHEMA IF NOT EXISTS tebra;

-- ==========================================
-- 1. Common Entities (cmn_)
-- ==========================================

CREATE TABLE tebra.cmn_patient (
    patient_guid UUID PRIMARY KEY,
    patient_id VARCHAR(50),      -- Display ID (e.g. 108301)
    full_name VARCHAR(150),      -- "LAST, FIRST"
    case_id VARCHAR(50)          -- Link to Insurance Case
);

CREATE TABLE tebra.cmn_provider (
    provider_guid UUID PRIMARY KEY,
    npi VARCHAR(20),
    name VARCHAR(150)
);

CREATE TABLE tebra.cmn_location (
    location_guid UUID PRIMARY KEY,
    name VARCHAR(150),
    address_block JSONB           -- {address: "...", city: "...", state: "..."}
);

-- ==========================================
-- 2. Reference Data (ref_)
-- ==========================================

CREATE TABLE tebra.ref_insurance_policy (
    policy_key VARCHAR(100) PRIMARY KEY, -- MD5(Policy+Group) or similar unique string
    company_name VARCHAR(150),
    plan_name VARCHAR(150),
    policy_number VARCHAR(50),
    group_number VARCHAR(50)
);

-- ==========================================
-- 3. Clinical Data (clin_)
-- ==========================================

CREATE TABLE tebra.clin_encounter (
    encounter_id BIGINT PRIMARY KEY, -- Tebra Integer ID
    encounter_guid UUID,             -- Tebra GUID
    start_date DATE,
    status VARCHAR(50),
    appt_type VARCHAR(100),
    appt_reason TEXT,
    
    -- Foreign Keys
    patient_guid UUID REFERENCES tebra.cmn_patient(patient_guid),
    provider_guid UUID REFERENCES tebra.cmn_provider(provider_guid),
    location_guid UUID REFERENCES tebra.cmn_location(location_guid),
    
    -- Insurance at time of encounter
    insurance_policy_key VARCHAR(100) REFERENCES tebra.ref_insurance_policy(policy_key) 
);

CREATE TABLE tebra.clin_encounter_diagnosis (
    encounter_id BIGINT REFERENCES tebra.clin_encounter(encounter_id),
    diag_code VARCHAR(20),
    precedence INTEGER,       -- 1=Primary, 2=Secondary...
    
    PRIMARY KEY (encounter_id, diag_code)
);

-- ==========================================
-- 4. Financial Data (fin_)
-- ==========================================

-- The "Check" / ERA Bundle
CREATE TABLE tebra.fin_era_bundle (
    claim_reference_id VARCHAR(100) PRIMARY KEY, -- Payer Control Number / Check #
    payer_name VARCHAR(150),
    received_date TIMESTAMP,
    total_paid DECIMAL(10, 2),
    total_patient_resp DECIMAL(10, 2)
);

-- The Tebra Service Line (Child of Bundle)
CREATE TABLE tebra.fin_claim_line (
    tebra_claim_id BIGINT PRIMARY KEY, -- The Line ID (e.g. 600408)
    
    -- Linkage
    encounter_id BIGINT REFERENCES tebra.clin_encounter(encounter_id),
    claim_reference_id VARCHAR(100) REFERENCES tebra.fin_era_bundle(claim_reference_id),
    
    -- Details
    proc_code VARCHAR(20),
    description TEXT,
    date_of_service DATE,
    
    -- Amounts
    billed_amount DECIMAL(10, 2),
    paid_amount DECIMAL(10, 2),
    units INTEGER,
    
    -- Adjustments (JSONB for querying: {"CO-45": 10.50})
    adjustments_json JSONB
);

-- ==========================================
-- 5. Indexes
-- ==========================================

-- Foreign Keys (Manual indexing often good practice in Postgres if not auto-created for FKs)
CREATE INDEX idx_enc_patient ON tebra.clin_encounter(patient_guid);
CREATE INDEX idx_enc_provider ON tebra.clin_encounter(provider_guid);
CREATE INDEX idx_enc_location ON tebra.clin_encounter(location_guid);
CREATE INDEX idx_enc_insurance ON tebra.clin_encounter(insurance_policy_key);

CREATE INDEX idx_claim_encounter ON tebra.fin_claim_line(encounter_id);
CREATE INDEX idx_claim_era ON tebra.fin_claim_line(claim_reference_id);

-- Search
CREATE INDEX idx_pat_name ON tebra.cmn_patient(full_name);
CREATE INDEX idx_era_payer ON tebra.fin_era_bundle(payer_name);
CREATE INDEX idx_enc_date ON tebra.clin_encounter(start_date);

-- JSONB Indexing (GIN)
CREATE INDEX idx_claim_adj ON tebra.fin_claim_line USING GIN (adjustments_json);
