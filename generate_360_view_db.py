import psycopg2
import json
import os

# Credentials
DB_CONFIG = {
    "dbname": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password",
    "host": "localhost",
    "port": "5432"
}

TARGET_ENC_ID = '388650' # From candidate search
OUT_FILE = 'Encounter_360_View_DB.md'

def run_report():
    print(f"Generating 360 Report for Encounter {TARGET_ENC_ID}...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 1. Fetch Header Info (Patient, Provider, Location, Insurance, Encounter)
    sql_header = """
    SELECT 
        e.encounter_id, e.encounter_guid, e.start_date, e.status, e.appt_type, e.appt_reason,
        e.appt_subject, e.appt_notes, e.pos_description, e.referring_provider_guid,
        p.patient_id, p.case_id, p.patient_guid, p.full_name, p.dob, p.gender, p.address_line1, p.city, p.state, p.zip,
        pro.name as provider_name, pro.npi as provider_npi,
        ref_pro.name as ref_name, ref_pro.npi as ref_npi,
        loc.name as loc_name, loc.address_block,
        ins.company_name, ins.plan_name, ins.policy_number, ins.group_number, ins.start_date, ins.end_date, ins.copay
    FROM tebra.clin_encounter e
    LEFT JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
    LEFT JOIN tebra.cmn_provider pro ON e.provider_guid = pro.provider_guid
    LEFT JOIN tebra.cmn_provider ref_pro ON e.referring_provider_guid::uuid = ref_pro.provider_guid
    LEFT JOIN tebra.ref_insurance_policy ins ON e.insurance_policy_key = ins.policy_key
    LEFT JOIN tebra.cmn_location loc ON e.location_guid = loc.location_guid
    WHERE e.encounter_id = %s
    """
    cur.execute(sql_header, (TARGET_ENC_ID,))
    header = cur.fetchone()
    
    if not header:
        print("Encounter not found!")
        return

    # Unpack Header
    (enc_id, enc_guid, start_date, status, appt_type, reason,
     appt_subj, appt_notes, pos_desc, ref_guid,
     pat_id, pat_case, pat_guid, pat_name, pat_dob, pat_gender, pat_addr, pat_city, pat_state, pat_zip,
     prov_name, prov_npi,
     ref_name, ref_npi,
     loc_name, loc_addr,
     ins_company, ins_plan, ins_pol, ins_grp, ins_start, ins_end, ins_copay) = header

    # 2. Fetch Diagnoses
    cur.execute("""
        SELECT diag_code, precedence, description FROM tebra.clin_encounter_diagnosis 
        WHERE encounter_id = %s ORDER BY precedence
    """, (TARGET_ENC_ID,))
    diags = cur.fetchall()

    # 3. Fetch Service Lines
    cur.execute("""
        SELECT 
            tebra_claim_id, proc_code, description, date_of_service, billed_amount, paid_amount, units, adjustments_json, claim_reference_id, adjustment_descriptions, modifiers_json,
            claim_status, payer_status, clearinghouse_payer, tracking_number
        FROM tebra.fin_claim_line
        WHERE encounter_id = %s
        ORDER BY date_of_service
    """, (TARGET_ENC_ID,))
    lines = cur.fetchall()

    # 4. Fetch ERA Bundle Info (Parent Payments)
    # Get distinct ref IDs
    refs = list(set([l[8] for l in lines if l[8]]))
    era_bundles = []
    if refs:
        format_strings = ','.join(['%s'] * len(refs))
        cur.execute(f"""
            SELECT claim_reference_id, payer_name, total_paid, total_patient_resp 
            FROM tebra.fin_era_bundle 
            WHERE claim_reference_id IN ({format_strings})
        """, tuple(refs))
        era_bundles = cur.fetchall()

    conn.close()

    # --- RENDER MARKDOWN ---
    md = []
    md.append(f"# Encounter 360 View: {enc_id}")
    md.append(f"**Generated from Postgres Database**\n")
    
    md.append("## 1. Context")
    md.append(f"- **Encounter GUID**: `{enc_guid}`")
    md.append(f"- **Date**: {start_date}")
    md.append(f"- **Status**: {status}")
    md.append(f"- **Type**: {appt_type or 'None'}")
    md.append(f"- **Reason**: {reason or 'None'}")
    if appt_subj: md.append(f"- **Subject**: {appt_subj}")
    if appt_notes: md.append(f"- **Notes**: {appt_notes}")
    
    md.append(f"- **Location**: {loc_name}")
    md.append(f"- **Address**: `{loc_addr}`")
    if pos_desc: md.append(f"- **Place of Service**: {pos_desc}")
    
    md.append("## 2. Entities")
    md.append("### Patient")
    md.append(f"- **Name**: **{pat_name}**")
    md.append(f"- **Case ID**: `{pat_case}`")
    md.append(f"- **Tebra ID**: `{pat_id}`")
    md.append(f"- **Patient GUID**: `{pat_guid}`")
    if pat_dob: md.append(f"- **DOB**: {pat_dob} ({pat_gender or '?'})")
    if pat_addr: md.append(f"- **Address**: {pat_addr}, {pat_city}, {pat_state} {pat_zip}\n")
    
    md.append("### Provider")
    md.append(f"- **Name**: {prov_name}")
    md.append(f"- **NPI**: `{prov_npi}`")
    if ref_name:
        md.append(f"- **Referring Provider**: {ref_name} (NPI: `{ref_npi}`)")
    md.append("")
    
    md.append("### Payer (Insurance)")
    md.append(f"- **Company**: {ins_company}")
    md.append(f"- **Plan**: {ins_plan}")
    md.append(f"- **Policy #**: `{ins_pol}`")
    md.append(f"- **Group #**: `{ins_grp}`")
    if ins_start: md.append(f"- **Effective**: {ins_start} to {ins_end or 'Present'}")
    if ins_copay: md.append(f"- **Copay**: ${float(ins_copay):.2f}\n")
    md.append("")
    
    md.append("## 3. Clinical Data")
    md.append("### Diagnoses")
    if diags:
        for d in diags:
             # d[0]=code, d[1]=prec, d[2]=desc
             desc = d[2] or "No Description"
             md.append(f"- **{d[0]}** - {desc} (Precedence: {d[1]})")
    else:
        md.append("_No Diagnoses Found_")
    md.append("")
        
    md.append("## 4. Financials (Lines)")
    md.append("| Date | Proc | Description | Billed | Paid (Line) | Units | Status | IDs (ERA/Track) | Adjustments |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    
    total_billed = 0.0
    total_paid = 0.0
    
    for l in lines:
        # tebra_claim_id, proc_code, description, date_of_service, billed_amount, paid_amount, units, adjustments_json, claim_reference_id, adj_desc
        billed = float(l[4] or 0)
        paid = float(l[5] or 0)
        adj = l[7] or "{}"
        adj_desc = l[9] or "" 
        mods_json = l[10]
        status = l[11] or ""
        payer_status = l[12] or ""
        track_num = l[14] or ""
        
        # Combine statuses
        status_display = status
        if payer_status and payer_status != status:
             status_display += f"<br>({payer_status})"
        
        # Format ERA Ref + Tracking
        ref_display = f"`{l[8]}`" if l[8] else "-"
        if track_num:
            ref_display += f"<br>Track: `{track_num}`"
        
        # Format adjustment display
        adj_display = f"`{adj}`"
        if adj_desc:
            adj_display += f"<br>_{adj_desc}_"
            
        # Format Modifiers
        proc_display = f"`{l[1]}`"
        if mods_json:
             try:
                 mods = json.loads(str(mods_json))
                 if mods:
                     mod_strs = [f"{k}: {v}" for k, v in mods.items()]
                     proc_display += f"<br>Modifiers: {'; '.join(mod_strs)}"
             except: pass
        
        total_billed += billed
        total_paid += paid
        
        md.append(f"| {l[3]} | {proc_display} | {l[2]} | ${billed:.2f} | ${paid:.2f} | {l[6]} | {status_display} | {ref_display} | {adj_display} |")
    
    md.append(f"\n**Totals**: Billed: **${total_billed:.2f}** | Line Paid: **${total_paid:.2f}**\n")
    
    md.append("## 5. ERA Payment Bundles (Parent Checks)")
    if era_bundles:
         md.append("| Claim Ref ID | Payer Name | Total Check Paid | Patient Resp |")
         md.append("|---|---|---|---|")
         for b in era_bundles:
             md.append(f"| `{b[0]}` | {b[1]} | ${float(b[2] or 0):.2f} | ${float(b[3] or 0):.2f} |")
    else:
        md.append("_No Linked ERA Bundles found in DB._")

    # Write
    with open(OUT_FILE, 'w') as f:
        f.write("\n".join(md))
    
    print(f"Report written to {os.path.abspath(OUT_FILE)}")

if __name__ == "__main__":
    run_report()
