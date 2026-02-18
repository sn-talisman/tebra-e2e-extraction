import psycopg2


# DB Connection Config (Embedded for reliability)
DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

def generate_360_view():
    print("--- Generating 360-Degree Encounter View ---")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Find a "rich" bundle (has lines, encounter, and diagnosis)
        sql_find = """
            SELECT b.claim_reference_id
            FROM tebra.fin_era_bundle b
            JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
            JOIN tebra.clin_encounter e ON cl.encounter_id = e.encounter_id
            JOIN tebra.clin_encounter_diagnosis d ON e.encounter_id = d.encounter_id
            WHERE b.total_paid > 0
            LIMIT 1
        """
        cur.execute(sql_find)
        res = cur.fetchone()
        
        if not res:
            print("No linked bundles found to generate view.")
            return

        target_ref_id = res[0]
        print(f"Target Bundle: {target_ref_id}")
        
        # 2. Fetch Data
        # Bundle Info
        cur.execute("SELECT * FROM tebra.fin_era_bundle WHERE claim_reference_id = %s", (target_ref_id,))
        bundle = cur.fetchone()
        colnames_bundle = [desc[0] for desc in cur.description]
        bundle_dict = dict(zip(colnames_bundle, bundle))
        
        # Claim Lines
        cur.execute("SELECT * FROM tebra.fin_claim_line WHERE claim_reference_id = %s", (target_ref_id,))
        lines = cur.fetchall()
        colnames_lines = [desc[0] for desc in cur.description]
        
        # Encounter (via first line connection)
        enc_id = lines[0][colnames_lines.index('encounter_id')]
        cur.execute("SELECT * FROM tebra.clin_encounter WHERE encounter_id = %s", (enc_id,))
        encounter = cur.fetchone()
        colnames_enc = [desc[0] for desc in cur.description]
        enc_dict = dict(zip(colnames_enc, encounter))
        
        # Patient
        pat_guid = enc_dict['patient_guid']
        cur.execute("SELECT * FROM tebra.cmn_patient WHERE patient_guid = %s", (pat_guid,))
        patient = cur.fetchone()
        colnames_pat = [desc[0] for desc in cur.description]
        pat_dict = dict(zip(colnames_pat, patient))
        
        # Diagnoses
        cur.execute("SELECT * FROM tebra.clin_encounter_diagnosis WHERE encounter_id = %s ORDER BY precedence", (enc_id,))
        diags = cur.fetchall()
        
        # 3. Format as Markdown
        md = f"""# 360-Degree Encounter View (Generated from Live DB)

## 1. Financial Bundle (ERA)
*   **Claim Reference ID**: `{bundle_dict['claim_reference_id']}`
*   **Payer**: {bundle_dict['payer_name']}
*   **Total Paid**: ${bundle_dict['total_paid']}
*   **Patient Resp**: ${bundle_dict['total_patient_resp']}
*   **ERA Report ID**: `{bundle_dict['era_report_id']}`

## 2. Clinical Context
*   **Encounter Date**: {enc_dict['start_date']}
*   **Reason**: {enc_dict['appt_reason']}
*   **Notes**: {enc_dict['appt_notes']}
*   **Subject**: {enc_dict['appt_subject']}
*   **Location**: {enc_dict['location_guid']}

## 3. Patient Demographics & Insurance
*   **Name**: **{pat_dict['full_name']}**
*   **DOB**: {pat_dict['dob']}
*   **Gender**: {pat_dict['gender']}
*   **Address**: {pat_dict['address_line1']}, {pat_dict['city']}, {pat_dict['state']} {pat_dict['zip']}
*   **Policy Key**: `{enc_dict['insurance_policy_key']}`

## 4. Diagnosis Codes (ICD-10)
| Seq | Code | Description |
| :--- | :--- | :--- |
"""
        for d in diags:
             # structure: encounter_id, diag_code, precedence, description
             md += f"| {d[2]} | **{d[1]}** | {d[3]} |\n"

        md += """
## 5. Financial Service Lines (Procedures)
| Proc | Date | Billed | Paid | Adjustments | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for l in lines:
            d = dict(zip(colnames_lines, l))
            md += f"| **{d['proc_code']}** | {d['date_of_service']} | ${d['billed_amount']} | ${d['paid_amount']} | `{d['adjustments_json']}` | {d['claim_status']} |\n"

        # Save
        with open('encounter_view_enriched.md', 'w') as f:
            f.write(md)
            
        print("Report generated: encounter_view_enriched.md")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error generating view: {e}")

if __name__ == "__main__":
    generate_360_view()
