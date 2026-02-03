"""
Step 4: Extract Additional Details (Deterministic Approach)
Linkage: ERA LineID (REF*6R) -> PM_CLAIM.CLAIMID -> PM_ENCOUNTERPROCEDURE -> PM_ENCOUNTER
"""
import csv
import logging
from src.connection import get_connection

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TARGET_PRACTICE_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
INPUT_LINES_FILE = 'service_lines.csv'
OUTPUT_FILE = 'encounters_enriched_deterministic.csv'

def extract_encounter_details_deterministic():
    logger.info("Starting Step 4: Deterministic Encounter Extraction...")
    
    # 1. Load Service Lines (Source of REF*6R)
    # Map: LineID_Ref6R -> {Line Data}
    lines_map = {}
    
    try:
        with open(INPUT_LINES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ref_id = row.get('LineID_Ref6R')
                if ref_id:
                    lines_map[ref_id] = row
    except FileNotFoundError:
        logger.error(f"Input file {INPUT_LINES_FILE} not found.")
        return

    logger.info(f"Loaded {len(lines_map)} service lines to enrich.")

    conn = get_connection()
    cursor = conn.cursor()
    
    enriched_data = []

    # 2. Iterate through each Line ID (ClaimID in DB)
    for line_id, line_data in lines_map.items():
        logger.info(f"Processing Line ID: {line_id}")
        
        # Default empty record
        record = {
            # Claim (3A)
            'DB_ClaimID': line_id,
            'DB_PatientGUID': None,
            'DB_EncounterProcedureID': None,
            
            # EncounterProcedure (3B)
            'Enc_EncounterGUID': None,
            'Enc_ProcDate': None,
            'Enc_WebChargeAmount': None,
            'Enc_ServiceCount': None,
            'Enc_ProcDictID': None,
            
            # ProcedureDict (3C)
            'Proc_Code': None,
            'Proc_Name': None,
            'Proc_TypeDesc': None,
            
            # Diagnosis IDs
            'DiagID_1': None, 'DiagID_2': None, 'DiagID_3': None, 'DiagID_4': None,
            'DiagID_5': None, 'DiagID_6': None, 'DiagID_7': None, 'DiagID_8': None,
            
            # Encounter (3D)
            'EncounterID': None,
            'EncounterDate': None, 
            'EncounterDateTo': None,
            'EncounterStatusID': None,
            'EncounterStatus': None,
            'AppointmentID': None,
            'AppointmentDate': None,
            'Appt_Type': None,
            'Appt_Reason': None,
            'Appt_Start': None,
            'Appt_End': None,
            'PostingDate': None,
            'PlaceOfServiceCode': None,
            
            # Provider/Appt Extras
            'ProviderGUID': None,
            'ProviderName': None,
            'ProviderNPI': None,
            
            # Service Location
            'ServiceLocationGUID': None,
            'FacilityName': None,
            'FacilityAddress': None,
            'FacilityCity': None,
            'FacilityState': None,
            
            # Insurance (3G)
            'InsurancePolicyAuthID': None,
            'PatientCaseID': None,
            'Insurance_Company': None,
            'Insurance_Plan': None,
            'Insurance_PolicyNum': None,
            'Insurance_GroupNum': None,
            
            'LinkStatus': 'Failed'
        }
        
        try:
            # --- 3A. Query PM_CLAIM (Already correct) ---
            q_claim = f"""
            SELECT ENCOUNTERPROCEDUREID, PATIENTGUID
            FROM PM_CLAIM
            WHERE CLAIMID = '{line_id}'
            """
            cursor.execute(q_claim)
            r_claim = cursor.fetchone()
            
            if not r_claim:
                logger.warning(f"  -> No PM_CLAIM match for {line_id}")
                full_rec = {**line_data, **record}
                enriched_data.append(full_rec)
                continue
                
            record['DB_EncounterProcedureID'] = r_claim[0]
            record['DB_PatientGUID'] = r_claim[1]
            record['LinkStatus'] = 'Claim Found'
            
            # --- 3B. Query PM_ENCOUNTERPROCEDURE (Already correct) ---
            if record['DB_EncounterProcedureID']:
                q_ep = f"""
                SELECT 
                    ENCOUNTERGUID,
                    PROCEDURECODEDICTIONARYID,
                    PROCEDUREDATEOFSERVICE,
                    SERVICECHARGEAMOUNT,
                    SERVICEUNITCOUNT,
                    TYPEOFSERVICEDESCRIPTION,
                    ENCOUNTERDIAGNOSISID1, ENCOUNTERDIAGNOSISID2, ENCOUNTERDIAGNOSISID3, ENCOUNTERDIAGNOSISID4,
                    ENCOUNTERDIAGNOSISID5, ENCOUNTERDIAGNOSISID6, ENCOUNTERDIAGNOSISID7, ENCOUNTERDIAGNOSISID8
                FROM PM_ENCOUNTERPROCEDURE
                WHERE ENCOUNTERPROCEDUREID = '{record['DB_EncounterProcedureID']}'
                """
                cursor.execute(q_ep)
                r_ep = cursor.fetchone()
                
                if r_ep:
                    record['Enc_EncounterGUID'] = r_ep[0]
                    record['Enc_ProcDictID'] = r_ep[1]
                    record['Enc_ProcDate'] = str(r_ep[2])[:10]
                    record['Enc_WebChargeAmount'] = r_ep[3]
                    record['Enc_ServiceCount'] = r_ep[4]
                    record['Proc_TypeDesc'] = r_ep[5]
                    
                    record['DiagID_1'] = r_ep[6]
                    record['DiagID_2'] = r_ep[7]
                    record['DiagID_3'] = r_ep[8]
                    record['DiagID_4'] = r_ep[9]
                    record['DiagID_5'] = r_ep[10]
                    record['DiagID_6'] = r_ep[11]
                    record['DiagID_7'] = r_ep[12]
                    record['DiagID_8'] = r_ep[13]
            
            # --- 3C. Query PM_PROCEDURECODEDICTIONARY (Already correct) ---
            if record['Enc_ProcDictID']:
                q_pd = f"""
                SELECT PROCEDURECODE, OFFICIALNAME, TYPEOFSERVICEDESCRIPTION
                FROM PM_PROCEDURECODEDICTIONARY
                WHERE PROCEDURECODEDICTIONARYID = '{record['Enc_ProcDictID']}'
                """
                cursor.execute(q_pd)
                r_pd = cursor.fetchone()
                if r_pd:
                    record['Proc_Code'] = r_pd[0]
                    record['Proc_Name'] = r_pd[1]
                    if r_pd[2]: record['Proc_TypeDesc'] = r_pd[2]

            # --- 3D. Query PM_ENCOUNTER (Expanded) ---
            if record['Enc_EncounterGUID']:
                q_enc = f"""
                SELECT 
                   E.ENCOUNTERID,
                   E.DATEOFSERVICE,
                   E.DATEOFSERVICETO,
                   E.ENCOUNTERSTATUSID,
                   E.ENCOUNTERSTATUSDESCRIPTION,
                   E.APPOINTMENTGUID,
                   E.APPOINTMENTSTARTDATE,
                   E.PROVIDERGUID,
                   E.SERVICELOCATIONGUID,
                   E.PLACEOFSERVICECODE,
                   E.POSTINGDATE,
                   D.FIRSTNAME,
                   D.LASTNAME,
                   D.NPI,
                   E.INSURANCEPOLICYAUTHORIZATIONID,
                   E.PATIENTCASEID
                FROM PM_ENCOUNTER E
                LEFT JOIN PM_DOCTOR D ON E.PROVIDERGUID = D.DOCTORGUID
                WHERE E.ENCOUNTERGUID = '{record['Enc_EncounterGUID']}'
                """
                cursor.execute(q_enc)
                r_enc = cursor.fetchone()
                
                if r_enc:
                    record['EncounterID'] = r_enc[0]
                    record['EncounterDate'] = str(r_enc[1])[:10]
                    record['EncounterDateTo'] = str(r_enc[2])[:10] if r_enc[2] else None
                    record['EncounterStatusID'] = r_enc[3]
                    record['EncounterStatus'] = r_enc[4]
                    record['AppointmentID'] = r_enc[5] # This is GUID actually, logic naming
                    record['AppointmentDate'] = str(r_enc[6])
                    record['ProviderGUID'] = r_enc[7]
                    record['ServiceLocationGUID'] = r_enc[8]
                    record['PlaceOfServiceCode'] = r_enc[9]
                    record['PostingDate'] = str(r_enc[10])[:10] if r_enc[10] else None
                    
                    record['ProviderName'] = f"{r_enc[11] or ''} {r_enc[12] or ''}".strip()
                    record['ProviderNPI'] = r_enc[13]
                    
                    record['InsurancePolicyAuthID'] = r_enc[14]
                    record['PatientCaseID'] = r_enc[15]
                    
                    record['LinkStatus'] = 'Success'
                    
                    # --- 3E. Query PM_SERVICELOCATION (New) ---
                    if record['ServiceLocationGUID']:
                        q_loc = f"""
                        SELECT NAME, ADDRESSLINE1, CITY, STATE
                        FROM PM_SERVICELOCATION
                        WHERE SERVICELOCATIONGUID = '{record['ServiceLocationGUID']}'
                        """
                        cursor.execute(q_loc)
                        r_loc = cursor.fetchone()
                        if r_loc:
                            record['FacilityName'] = r_loc[0]
                            record['FacilityAddress'] = r_loc[1]
                            record['FacilityCity'] = r_loc[2]
                            record['FacilityState'] = r_loc[3]

                    # --- 3F. Query PM_APPOINTMENT (New) ---
                    if record['AppointmentID']: # This holds GUID
                        q_appt = f"""
                        SELECT 
                            APPOINTMENTTYPEDESCRIPTION,
                            SUBJECT,
                            STARTDATE,
                            ENDDATE
                        FROM PM_APPOINTMENT
                        WHERE APPOINTMENTGUID = '{record['AppointmentID']}'
                        """
                        cursor.execute(q_appt)
                        r_appt = cursor.fetchone()
                        if r_appt:
                            record['Appt_Type'] = r_appt[0]
                            record['Appt_Reason'] = r_appt[1]
                            record['Appt_Start'] = str(r_appt[2])
                            record['Appt_End'] = str(r_appt[3])
                            # Overwrite generic date if specific appt date found
                            record['AppointmentDate'] = record['Appt_Start']
                            
                    # --- 3G. Query Insurance (New) ---
                    ins_policy_guid = None
                    
                    # Try via Authorization first
                    if record['InsurancePolicyAuthID']:
                        q_auth = f"""
                        SELECT INSURANCEPOLICYGUID 
                        FROM PM_INSURANCEPOLICYAUTHORIZATION 
                        WHERE INSURANCEPOLICYAUTHORIZATIONID = '{record['InsurancePolicyAuthID']}'
                        """
                        cursor.execute(q_auth)
                        r_auth = cursor.fetchone()
                        if r_auth: ins_policy_guid = r_auth[0]
                    
                    # Fallback: Try via PatientCase (Primary + Active)
                    if not ins_policy_guid and record['PatientCaseID']:
                        q_case = f"""
                        SELECT INSURANCEPOLICYGUID
                        FROM PM_INSURANCEPOLICY
                        WHERE PATIENTCASEID = '{record['PatientCaseID']}'
                          AND ACTIVE = TRUE
                        ORDER BY PRECEDENCE ASC, CREATEDDATE DESC
                        LIMIT 1
                        """
                        cursor.execute(q_case)
                        r_case = cursor.fetchone()
                        if r_case: ins_policy_guid = r_case[0]
                    
                    # If Policy Found -> Get Details (Policy -> Plan -> Company)
                    if ins_policy_guid:
                        q_pol = f"""
                        SELECT 
                            P.POLICYNUMBER,
                            P.GROUPNUMBER,
                            P.INSURANCECOMPANYPLANGUID,
                            PL.PLANNAME,
                            PL.INSURANCECOMPANYID
                        FROM PM_INSURANCEPOLICY P
                        LEFT JOIN PM_INSURANCECOMPANYPLAN PL ON P.INSURANCECOMPANYPLANGUID = PL.INSURANCECOMPANYPLANGUID
                        WHERE P.INSURANCEPOLICYGUID = '{ins_policy_guid}'
                        """
                        cursor.execute(q_pol)
                        r_pol = cursor.fetchone()
                        if r_pol:
                            record['Insurance_PolicyNum'] = r_pol[0]
                            record['Insurance_GroupNum'] = r_pol[1]
                            record['Insurance_Plan'] = r_pol[3]
                            ins_company_id = r_pol[4]
                            
                            if ins_company_id:
                                q_comp = f"""
                                SELECT INSURANCECOMPANYNAME
                                FROM PM_INSURANCECOMPANY
                                WHERE INSURANCECOMPANYID = '{ins_company_id}'
                                """
                                cursor.execute(q_comp)
                                r_comp = cursor.fetchone()
                                if r_comp:
                                    record['Insurance_Company'] = r_comp[0]
                            
                    logger.info(f"  -> Linked to EncID: {r_enc[0]} | Ins: {record['Insurance_Company']}")
                else:
                    logger.warning("  -> Encounter Not Found for GUID")
            
        except Exception as e:
            logger.error(f"  -> Error processing {line_id}: {e}")
            record['LinkStatus'] = f"Error: {str(e)}"
            
        # Merge and Save
        full_rec = {**line_data, **record}
        enriched_data.append(full_rec)

    # Output
    if enriched_data:
        keys = list(enriched_data[0].keys())
        with open(OUTPUT_FILE, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(enriched_data)
        logger.info(f"Saved deterministic enrichment to {OUTPUT_FILE}")
    
    conn.close()

if __name__ == "__main__":
    extract_encounter_details_deterministic()
