import csv
import logging
from src.connection import get_connection

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INPUT_FILE_NAME = 'service_lines.csv'
OUTPUT_FILE_NAME = 'encounters_enriched_deterministic.csv'

def chunk_list(lst, size=1000):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def extract_batch(input_dir='.', output_dir='.'):
    logger.info(f"Starting Batch Extraction (Optimized) in {input_dir}...")
    
    import os
    input_path = os.path.join(input_dir, INPUT_FILE_NAME)
    output_path = os.path.join(output_dir, OUTPUT_FILE_NAME)
    
    # 1. Load Line IDs
    lines_map = {}
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return

    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = row.get('LineID_Ref6R')
            if rid: lines_map[rid] = row
            
    all_line_ids = [k for k in lines_map.keys() if k.isdigit() and len(k) == 6]
    logger.info(f"Loaded {len(lines_map)} total lines. Querying {len(all_line_ids)} valid 6-digit IDs.")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Storage for enrichment
    # map: line_id -> {'DB_ClaimID':..., 'DB_PatientGUID':..., ...}
    enrichment_map = {lid: {'LinkStatus': 'Failed'} for lid in all_line_ids}

    # --- Step 1: Bulk Resolve Claims ---
    # CLAIMID -> (ENC_PROC_ID, PATIENT_GUID)
    claim_matches = {} 
    
    # Query in chunks if needed (though 150 fits in one)
    rows = []
    if all_line_ids:
        id_list_str = ", ".join([f"'{d}'" for d in all_line_ids])
        
        q_claims = """
            SELECT CLAIMID, ENCOUNTERPROCEDUREID, PATIENTGUID, 
                   STATUSNAME, PAYERPROCESSINGSTATUSTYPEDESC, CLEARINGHOUSEPAYER, CLEARINGHOUSETRACKINGNUMBER,
                   PRACTICEGUID
            FROM PM_CLAIM 
            WHERE CLAIMID IN ({id_list_str})
        """.format(id_list_str=id_list_str)
        logger.info("Executing Bulk Claim Query...")
        cursor.execute(q_claims)
        rows = cursor.fetchall()
        logger.info(f"  -> Found {len(rows)} matching Claims.")
    else:
        logger.warning("No valid 6-digit Claim IDs to query. Skipping SQL.")
    
    enc_proc_ids = []
    
    # Initialize sets to avoid UnboundLocalError
    enc_guids = set()
    proc_dict_ids = set()
    ins_auth_ids = set()
    case_ids = set()
    
    for r in rows:
        cid = str(r[0])
        epid = r[1]
        pguid = r[2]
        
        enrichment_map[cid]['DB_ClaimID'] = cid
        enrichment_map[cid]['DB_EncounterProcedureID'] = epid
        enrichment_map[cid]['DB_PatientGUID'] = pguid
        
        enrichment_map[cid]['Claim_Status'] = r[3]
        enrichment_map[cid]['Payer_Status'] = r[4]
        enrichment_map[cid]['CH_Payer'] = r[5]
        enrichment_map[cid]['Tracking_Num'] = r[6]
        enrichment_map[cid]['Claim_PracticeGUID'] = r[7]
        
        enrichment_map[cid]['LinkStatus'] = 'Claim Found'
        
        if epid: enc_proc_ids.append(epid)
        
    # --- Step 2: Bulk Resolve EncounterProcedures ---
    # ENC_PROC_ID -> (ENC_GUID, Details...)
    if enc_proc_ids:
        ep_list_str = ", ".join([f"'{d}'" for d in enc_proc_ids])
        q_ep = f"""
            SELECT 
                ENCOUNTERPROCEDUREID, ENCOUNTERGUID, PROCEDURECODEDICTIONARYID, 
                PROCEDUREDATEOFSERVICE, SERVICECHARGEAMOUNT, SERVICEUNITCOUNT, TYPEOFSERVICEDESCRIPTION,
                ENCOUNTERDIAGNOSISID1, ENCOUNTERDIAGNOSISID2, ENCOUNTERDIAGNOSISID3, ENCOUNTERDIAGNOSISID4,
                ENCOUNTERDIAGNOSISID5, ENCOUNTERDIAGNOSISID6, ENCOUNTERDIAGNOSISID7, ENCOUNTERDIAGNOSISID8,
                PROCEDUREMODIFIER1, PROCEDUREMODIFIER2, PROCEDUREMODIFIER3, PROCEDUREMODIFIER4
            FROM PM_ENCOUNTERPROCEDURE
            WHERE ENCOUNTERPROCEDUREID IN ({ep_list_str})
        """
        logger.info("Executing Bulk EncounterProcedure Query...")
        cursor.execute(q_ep)
        rows_ep = cursor.fetchall()
        logger.info(f"  -> Found {len(rows_ep)} EncounterProcedures.")
        
        enc_guids = set()
        proc_dict_ids = set()
        
        # Map back to lines
        # Problem: We need to know which LineID this EP belongs to.
        # Solution: Use the enrichment_map which has 'DB_EncounterProcedureID'
        
        # Store EP data in lookup: EP_ID -> Data
        ep_lookup = {}
        for r in rows_ep:
            ep_lookup[r[0]] = {
                'Enc_EncounterGUID': r[1],
                'Enc_ProcDictID': r[2],
                'Enc_ProcDate': str(r[3])[:10],
                'Enc_WebChargeAmount': r[4],
                'Enc_ServiceCount': r[5],
                'Proc_TypeDesc': r[6],
                'Diags': [r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14]],
                'ModifierID_1': r[15],
                'ModifierID_2': r[16],
                'ModifierID_3': r[17],
                'ModifierID_4': r[18]
            }
            if r[1]: enc_guids.add(r[1])
            if r[2]: proc_dict_ids.add(r[2])
            
        # Distribute to enrichment map
        for lid, data in enrichment_map.items():
            epid = data.get('DB_EncounterProcedureID')
            if epid and epid in ep_lookup:
                ep_data = ep_lookup[epid]
                data.update(ep_data)
                # Flatten Diags
                for i, d in enumerate(ep_data['Diags']):
                    data[f'DiagID_{i+1}'] = d
                    
    # --- Step 2b: Resolve Procedure Descriptions ---
    if proc_dict_ids:
        ids = ", ".join([f"'{d}'" for d in proc_dict_ids])
        cursor.execute(f"SELECT PROCEDURECODEDICTIONARYID, OFFICIALNAME FROM PM_PROCEDURECODEDICTIONARY WHERE PROCEDURECODEDICTIONARYID IN ({ids})")
        proc_lookup = {r[0]: r[1] for r in cursor.fetchall()}
        
        for lid, data in enrichment_map.items():
            pdid = data.get('Enc_ProcDictID')
            if pdid and pdid in proc_lookup:
                data['Proc_Description'] = proc_lookup[pdid] # Override generic description

    # --- Step 2c: Resolve Diagnoses Descriptions (Complex Linkage) ---
    # The IDs in 'DiagID_x' are actually ENCOUNTERDIAGNOSISID (from PM_ENCOUNTERPROCEDURE)
    # Mapping: EncDiagID -> [PM_ENCOUNTERDIAGNOSIS] -> DiagDictID -> [PM_ICD10...] -> Description
    
    enc_diag_ids = set()
    for lid, data in enrichment_map.items():
        for i in range(1, 9):
            did = data.get(f'DiagID_{i}')
            if did: enc_diag_ids.add(did)
            
    if enc_diag_ids:
        ids_str = ", ".join([f"'{d}'" for d in enc_diag_ids])
        
        # 1. Resolve EncounterDiagID -> DictionaryID
        # Try finding the Dictionary ID column. Based on 'hunt_diag_id.py' output: DIAGNOSISCODEDICTIONARYID
        # But wait, it might be an ICD10 ID. Let's select multiple possibilities.
        # Note: PM_ENCOUNTERDIAGNOSIS has DIAGNOSISCODEDICTIONARYID. 
        # Does it have ICD10DIAGNOSISCODEDICTIONARYID? The output only showed DIAGNOSISCODEDICTIONARYID.
        # Let's assume it links there.
        
        logger.info("Resolving EncounterDiagnosis IDs...")
        q_ed = f"SELECT ENCOUNTERDIAGNOSISID, DIAGNOSISCODEDICTIONARYID FROM PM_ENCOUNTERDIAGNOSIS WHERE ENCOUNTERDIAGNOSISID IN ({ids_str})"
        cursor.execute(q_ed)
        
        ed_map = {} # EncDiagID -> DictID
        dict_ids = set()
        for r in cursor.fetchall():
            if r[1]: 
                ed_map[r[0]] = r[1]
                dict_ids.add(r[1])
                
        # 2. Resolve DictionaryID -> Description
        # Now we have the Dict IDs. These *might* be Legacy or ICD10.
        # Let's try ICD10 first (checking ICD10DIAGNOSISCODEDICTIONARYID column match? Or just query table)
        # If the columns match, great. If not, we check Legacy table.
        # Usually Snowflake IDs are unique across tables or we need to know which table.
        # Let's check PM_ICD10DIAGNOSISCODEDICTIONARY first using ICD10DIAGNOSISCODEDICTIONARYID
        
        final_desc_map = {} # DictID -> Description
        
        if dict_ids:
            d_ids_str = ", ".join([f"'{d}'" for d in dict_ids])
            
            # Try ICD10 Table
            try:
                # Use COALESCE to avoid NULL result if one field is missing
                q_icd10 = f"""
                    SELECT ICD10DIAGNOSISCODEDICTIONARYID, 
                           COALESCE(OFFICIALNAME, OFFICIALDESCRIPTION, LOCALNAME) as Desc 
                    FROM PM_ICD10DIAGNOSISCODEDICTIONARY 
                    WHERE ICD10DIAGNOSISCODEDICTIONARYID IN ({d_ids_str})
                """
                cursor.execute(q_icd10)
                for r in cursor.fetchall():
                    final_desc_map[r[0]] = r[1]
            except Exception as e:
                logger.warning(f"ICD10 lookup failed: {e}")

            # Identify missing
            missing_ids = dict_ids - set(final_desc_map.keys())
            
            # Try Legacy Table if missing
            if missing_ids:
                m_ids_str = ", ".join([f"'{d}'" for d in missing_ids])
                try:
                    cursor.execute(f"SELECT DIAGNOSISCODEDICTIONARYID, OFFICIALNAME FROM PM_DIAGNOSISCODEDICTIONARY WHERE DIAGNOSISCODEDICTIONARYID IN ({m_ids_str})")
                    for r in cursor.fetchall():
                         final_desc_map[r[0]] = r[1]
                except Exception as e:
                    logger.warning(f"Legacy lookup failed: {e}")

        # 3. Populate Map
        for lid, data in enrichment_map.items():
            for i in range(1, 9):
                did = data.get(f'DiagID_{i}') # This is the EncounterDiagID
                if did and did in ed_map:
                    dict_id = ed_map[did]
                    if dict_id in final_desc_map:
                        data[f'DiagDesc_{i}'] = final_desc_map[dict_id]

    # --- Step 2d: Resolve Procedure Modifiers ---
    # Collect modifier IDs
    mod_ids = set()
    for lid, data in enrichment_map.items():
        for i in range(1, 5):
            mid = data.get(f'ModifierID_{i}')
            if mid: mod_ids.add(mid)
            
    if mod_ids:
        ids_str = ", ".join([f"'{d}'" for d in mod_ids])
        # Use PROCEDUREMODIFIERCODE for lookup, as PM_ENCOUNTERPROCEDURE stores codes
        cursor.execute(f"SELECT PROCEDUREMODIFIERID, PROCEDUREMODIFIERCODE, MODIFIERNAME FROM PM_PROCEDUREMODIFIER WHERE PROCEDUREMODIFIERCODE IN ({ids_str})")
        mod_lookup = {r[1]: (r[1], r[2]) for r in cursor.fetchall()} # Code -> (Code, Desc)
        
        for lid, data in enrichment_map.items():
            for i in range(1, 5):
                mid = data.get(f'ModifierID_{i}') # mid is actually the Code here
                if mid and mid in mod_lookup:
                    code, desc = mod_lookup[mid]
                    data[f'ModifierCode_{i}'] = code
                    data[f'ModifierDesc_{i}'] = desc

    # --- Step 3: Bulk Resolve Encounters (Enhanced) ---
    if enc_guids:
        enc_list_str = ", ".join([f"'{d}'" for d in enc_guids])
        q_enc = f"""
            SELECT 
               ENCOUNTERGUID, ENCOUNTERID, DATEOFSERVICE, ENCOUNTERSTATUSDESCRIPTION,
               APPOINTMENTGUID, PROVIDERGUID, SERVICELOCATIONGUID,
               INSURANCEPOLICYAUTHORIZATIONID, PATIENTCASEID, PLACEOFSERVICECODE,
               REFERRINGPHYSICIANGUID, PRACTICEGUID, PATIENTGUID
            FROM PM_ENCOUNTER
            WHERE ENCOUNTERGUID IN ({enc_list_str})
        """
        logger.info("Executing Bulk Encounter Query...")
        cursor.execute(q_enc)
        rows_enc = cursor.fetchall()
        
        enc_lookup = {}
        ins_auth_ids = set()
        case_ids = set()
        
        for r in rows_enc:
            enc_lookup[r[0]] = {
                'EncounterID': r[1],
                'EncounterDate': str(r[2])[:10],
                'EncounterStatus': r[3],
                'Enc_ApptGUID': r[4],
                'ProviderGUID': r[5],
                'ServiceLocationGUID': r[6],
                'InsurancePolicyAuthID': r[7],
                'PatientCaseID': r[8],
                'Enc_POSCode': r[9],
                'ReferringProvGUID': r[10],
                'Enc_PracticeGUID': r[11],
                'Enc_PatientGUID': r[12],
                'LinkStatus': 'Success'
            }
            if r[7]: ins_auth_ids.add(r[7])
            if r[8]: case_ids.add(r[8])
            
        # Distribute
        for lid, data in enrichment_map.items():
            eguid = data.get('Enc_EncounterGUID')
            if eguid and eguid in enc_lookup:
                data.update(enc_lookup[eguid])
                
        # --- Step 3b: Resolve Encounter Details (Appt, POS) ---
        # Appointment Not implemented fully yet?
        # Let's resolve APPOINTMENTGUID -> ApptType, ApptDesc
        appt_guids = {r.get('Enc_ApptGUID') for r in enrichment_map.values() if r.get('Enc_ApptGUID')}
        if appt_guids:
             ids = ", ".join([f"'{g}'" for g in appt_guids])
             cursor.execute(f"SELECT APPOINTMENTGUID, APPOINTMENTTYPE, APPOINTMENTTYPEDESCRIPTION, SUBJECT, NOTES FROM PM_APPOINTMENT WHERE APPOINTMENTGUID IN ({ids})")
             appt_map = {r[0]: r[1:] for r in cursor.fetchall()}
             for lid, data in enrichment_map.items():
                 ag = data.get('Enc_ApptGUID')
                 if ag and ag in appt_map:
                     res = appt_map[ag]
                     data['Appt_Type'] = res[0]
                     data['Appt_Desc'] = res[1]
                     data['Appt_Subject'] = res[2]
                     data['Appt_Notes'] = res[3]

        # Place of Service Desc
        pos_codes = {r.get('Enc_POSCode') for r in enrichment_map.values() if r.get('Enc_POSCode')}
        if pos_codes:
            ids = ", ".join([f"'{c}'" for c in pos_codes])
            cursor.execute(f"SELECT PLACEOFSERVICECODE, DESCRIPTION FROM PM_PLACEOFSERVICE WHERE PLACEOFSERVICECODE IN ({ids})")
            pos_map = {r[0]: r[1] for r in cursor.fetchall()}
            for lid, data in enrichment_map.items():
                 pc = data.get('Enc_POSCode')
                 if pc and pc in pos_map:
                     data['POS_Desc'] = pos_map[pc]

    # --- Step 4: Bulk Resolve Metadata (Patient, Provider, Location) ---
    # Collect GUIDs
    pat_guids = set()
    prov_guids = set()
    loc_guids = set()

    for lid, data in enrichment_map.items():
        if data.get('DB_PatientGUID'): pat_guids.add(data['DB_PatientGUID'])
        if data.get('ProviderGUID'): prov_guids.add(data['ProviderGUID'])
        if data.get('ReferringProvGUID'): prov_guids.add(data['ReferringProvGUID']) # Add Referrer
        if data.get('ServiceLocationGUID'): loc_guids.add(data['ServiceLocationGUID'])

    # 4a. Resolve Patients
    if pat_guids:
        ids = ", ".join([f"'{d}'" for d in pat_guids])
        # PM_PATIENT: PATIENTGUID, PATIENTID, FIRSTNAME, LASTNAME, DOB, GENDER, ADDRESSLINE1, CITY, STATE, ZIPCODE,
        #             PRACTICEGUID, PRIMARYPROVIDERGUID, DEFAULTSERVICELOCATIONGUID, REFERRINGPHYSICIANGUID, ACTIVE
        cursor.execute(f"""SELECT PATIENTGUID, PATIENTID, FIRSTNAME, LASTNAME, DOB, GENDER, ADDRESSLINE1, CITY, STATE, ZIPCODE,
                                  PRACTICEGUID, PRIMARYPROVIDERGUID, DEFAULTSERVICELOCATIONGUID, REFERRINGPHYSICIANGUID, ACTIVE
                           FROM PM_PATIENT WHERE PATIENTGUID IN ({ids})""")
        pat_lookup = {}
        for r in cursor.fetchall():
            pat_lookup[r[0]] = {
                'PatientID': r[1],
                'PatientName': f"{r[2] or ''} {r[3] or ''}".strip(),
                'PatientDOB': str(r[4])[:10] if r[4] else None,
                'PatientGender': r[5],
                'PatientAddress': r[6],
                'PatientCity': r[7],
                'PatientState': r[8],
                'PatientZip': r[9],
                'Patient_PracticeGUID': r[10],
                'Patient_PrimaryProvGUID': r[11],
                'Patient_DefaultLocGUID': r[12],
                'Patient_ReferringProvGUID': r[13],
                'Patient_Active': r[14]
            }
        # Distribute
        for lid, data in enrichment_map.items():
            pg = data.get('DB_PatientGUID')
            if pg and pg in pat_lookup:
                data.update(pat_lookup[pg])

    # 4b. Resolve Providers
    if prov_guids:
        ids = ", ".join([f"'{d}'" for d in prov_guids])
        # PM_DOCTOR: DOCTORGUID, NPI, FIRSTNAME, LASTNAME, PRACTICEGUID, DOCTORID, TAXONOMYCODE
        cursor.execute(f"""SELECT DOCTORGUID, NPI, FIRSTNAME, LASTNAME, PRACTICEGUID, DOCTORID, TAXONOMYCODE
                           FROM PM_DOCTOR WHERE DOCTORGUID IN ({ids})""")
        prov_lookup = {}
        for r in cursor.fetchall():
            prov_lookup[r[0]] = {
                'ProviderNPI': r[1],
                'ProviderName': f"{r[2] or ''} {r[3] or ''}".strip(),
                'Provider_PracticeGUID': r[4],
                'Provider_ID': r[5],
                'Provider_TaxonomyCode': r[6]
            }
        for lid, data in enrichment_map.items():
            pg = data.get('ProviderGUID')
            if pg and pg in prov_lookup:
                 data.update(prov_lookup[pg])
                 
            rpg = data.get('ReferringProvGUID')
            if rpg and rpg in prov_lookup:
                 # Map to distinct keys
                 data['ReferringProviderNPI'] = prov_lookup[rpg]['ProviderNPI']
                 data['ReferringProviderName'] = prov_lookup[rpg]['ProviderName']

    # 4c. Resolve Locations
    if loc_guids:
        ids = ", ".join([f"'{d}'" for d in loc_guids])
        # PM_SERVICELOCATION: SERVICELOCATIONGUID, NAME, ADDRESSLINE1, CITY, STATE, PRACTICEGUID, NPI, PLACEOFSERVICECODE, SERVICELOCATIONID
        cursor.execute(f"""SELECT SERVICELOCATIONGUID, NAME, ADDRESSLINE1, CITY, STATE,
                                  PRACTICEGUID, NPI, PLACEOFSERVICECODE, SERVICELOCATIONID
                           FROM PM_SERVICELOCATION WHERE SERVICELOCATIONGUID IN ({ids})""")
        loc_lookup = {}
        for r in cursor.fetchall():
             loc_lookup[r[0]] = {
                 'FacilityName': r[1],
                 'FacilityAddress': r[2],
                 'FacilityCity': r[3],
                 'FacilityState': r[4],
                 'Location_PracticeGUID': r[5],
                 'Location_NPI': r[6],
                 'Location_POSCode': r[7],
                 'Location_ID': r[8]
             }
        for lid, data in enrichment_map.items():
             lg = data.get('ServiceLocationGUID')
             if lg and lg in loc_lookup:
                 data.update(loc_lookup[lg])

    # --- Step 5: Bulk Resolve Insurance (Simplified for Speed) ---
    policy_guids = set()

    if ins_auth_ids:
        ids = ", ".join([f"'{d}'" for d in ins_auth_ids])
        cursor.execute(f"SELECT INSURANCEPOLICYAUTHORIZATIONID, INSURANCEPOLICYGUID FROM PM_INSURANCEPOLICYAUTHORIZATION WHERE INSURANCEPOLICYAUTHORIZATIONID IN ({ids})")
        auth_map = {r[0]: r[1] for r in cursor.fetchall()}
        
        for lid, data in enrichment_map.items():
            auth_id = data.get('InsurancePolicyAuthID')
            if auth_id and auth_id in auth_map:
                data['Calculated_PolicyGUID'] = auth_map[auth_id]
                policy_guids.add(auth_map[auth_id])

    # 4b. Patient Case (if auth missing)
    # This is tricky in bulk (Group by Case). We will skip for fallback for now or just grab all active policies for cases.
    if case_ids:
        ids = ", ".join([f"'{d}'" for d in case_ids])
        # Get PRIMARY ACTIVE policy for each case
        q_case = f"""
            SELECT PATIENTCASEID, INSURANCEPOLICYGUID 
            FROM PM_INSURANCEPOLICY 
            WHERE PATIENTCASEID IN ({ids}) AND ACTIVE = TRUE
            ORDER BY PRECEDENCE ASC
        """ 
        # Note: In bulk, ORDER BY PRECEDENCE limits us. We'll just grab all and pick in python.
        cursor.execute(q_case)
        case_map = {}
        for r in cursor.fetchall():
            if r[0] not in case_map: case_map[r[0]] = r[1] # First one wins
            
        for lid, data in enrichment_map.items():
            if 'Calculated_PolicyGUID' not in data:
                cid = data.get('PatientCaseID')
                if cid and cid in case_map:
                    data['Calculated_PolicyGUID'] = case_map[cid]
                    policy_guids.add(case_map[cid])

    # 4c. Resolve Policy Details
    if policy_guids:
        ids = ", ".join([f"'{d}'" for d in policy_guids])
        q_pol = f"""
            SELECT P.INSURANCEPOLICYGUID, P.POLICYNUMBER, P.GROUPNUMBER, PL.PLANNAME, C.INSURANCECOMPANYNAME,
                   P.POLICYSTARTDATE, P.POLICYENDDATE, P.COPAY,
                   P.PRACTICEGUID, P.PATIENTCASEID, P.PRECEDENCE
            FROM PM_INSURANCEPOLICY P
            LEFT JOIN PM_INSURANCECOMPANYPLAN PL ON P.INSURANCECOMPANYPLANGUID = PL.INSURANCECOMPANYPLANGUID
            LEFT JOIN PM_INSURANCECOMPANY C ON PL.INSURANCECOMPANYID = C.INSURANCECOMPANYID
            WHERE P.INSURANCEPOLICYGUID IN ({ids})
        """
        logger.info("Executing Bulk Policy Query...")
        cursor.execute(q_pol)
        pol_lookup = {}
        for r in cursor.fetchall():
            pol_lookup[r[0]] = {
                'Insurance_PolicyNum': r[1],
                'Insurance_GroupNum': r[2],
                'Insurance_Plan': r[3],
                'Insurance_Company': r[4],
                'Policy_Start': str(r[5])[:10] if r[5] else None,
                'Policy_End': str(r[6])[:10] if r[6] else None,
                'Policy_Copay': r[7],
                'Policy_PracticeGUID': r[8],
                'Policy_PatientCaseID': r[9],
                'Policy_Precedence': r[10],
                'Policy_GUID': r[0]  # Snowflake native GUID
            }
            
        for lid, data in enrichment_map.items():
             pguid = data.get('Calculated_PolicyGUID')
             if pguid and pguid in pol_lookup:
                 data.update(pol_lookup[pguid])

             if pguid and pguid in pol_lookup:
                 data.update(pol_lookup[pguid])

    # --- Step 6: Resolve Adjustment Codes (Global Dictionary) ---
    # CARC
    cursor.execute("SELECT ADJUSTMENTREASONCODE, DESCRIPTION FROM PM_ADJUSTMENTREASON")
    carc_map = {r[0]: r[1] for r in cursor.fetchall()}
    
    # RARC
    cursor.execute("SELECT REMITTANCECODE, REMITTANCEDESCRIPTION FROM PM_REMITTANCEREMARK")
    rarc_map = {r[0]: r[1] for r in cursor.fetchall()}
    
    # Enrich Adjustments JSON
    import json
    for lid, data in enrichment_map.items():
        original_row = lines_map.get(lid) 
        if not original_row: continue
        
        adj_str = original_row.get('Adjustments', '')
        if not adj_str: continue
        
        # Parse: "CO-45:10.00; PR-3:5.00"
        # Output format: JSON with details? Or just keep simple JSON for DB and enrich in Report?
        # User asked for descriptions. Let's create a new column 'Adjustments_Rich' or enrich the reporting layer.
        # Actually, simpler to create a map of code -> desc and pass it to DB or just leave it for report generation?
        # The prompt says "I am not getting... here", implying the view/report is missing it.
        # Let's add a 'Adjustment_Descriptions' column to csv.
        
        parts = adj_str.split(';')
        descs = []
        for p in parts:
             if ':' in p:
                 code_full = p.split(':')[0].strip() # "CO-45"
                 # Split Group/Reason
                 if '-' in code_full:
                     grp, rsn = code_full.split('-', 1)
                     # Check CARC
                     if rsn in carc_map:
                         descs.append(f"{code_full}: {carc_map[rsn]}")
                     # Check RARC (usually just code like M15, or maybe N425) - ERAs often mix them or use separate segments.
                     # Our parser puts them in same list. 
                     elif code_full in rarc_map: # Try full code first
                          descs.append(f"{code_full}: {rarc_map[code_full]}")
                     elif rsn in rarc_map:
                          descs.append(f"{code_full}: {rarc_map[rsn]}")
        
        if descs:
            data['Adjustment_Descriptions'] = " | ".join(descs)

    
    # Write Output
    logger.info("Writing results...")
    final_output = []
    
    # Merge original CSV data with enrichment data
    # We loop through lines_map to preserve original CSV columns
    keys = set()
    for lid, original_row in lines_map.items():
        enriched = enrichment_map.get(lid, {})
        merged = {**original_row, **enriched}
        
        # Ensure calculated fields are strings if needed, clean up
        if 'Diags' in merged: del merged['Diags']
        if 'Calculated_PolicyGUID' in merged: del merged['Calculated_PolicyGUID']
        
        final_output.append(merged)
        keys.update(merged.keys())
        
    with open(output_path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=list(keys))
        writer.writeheader()
        writer.writerows(final_output)
        
    logger.info(f"Done! Saved {len(final_output)} rows to {output_path}")

if __name__ == "__main__":
    extract_batch()
