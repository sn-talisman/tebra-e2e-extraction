import csv
import json
import os

CLAIMS_FILE = 'claims_extracted.csv'
DETAILS_FILE = 'encounters_enriched_deterministic.csv'
OUTPUT_FILE = 'Encounter_360_View.md'

import csv
import json
import os

CLAIMS_FILE = 'claims_extracted.csv'
DETAILS_FILE = 'encounters_enriched_deterministic.csv'
OUTPUT_FILE = 'Encounter_360_View.md'

import csv
import json
import os
import collections

CLAIMS_FILE = 'claims_extracted.csv'
DETAILS_FILE = 'encounters_enriched_deterministic.csv'
OUTPUT_FILE = 'Encounter_360_View.md'

TARGET_ENCOUNTER_ID = '388506'

def load_claims():
    claims = {}
    if os.path.exists(CLAIMS_FILE):
        with open(CLAIMS_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                claims[row['ClaimID']] = row
    return claims

def load_encounter_groups():
    encounters = {}
    if os.path.exists(DETAILS_FILE):
        with open(DETAILS_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                enc_id = row.get('EncounterID')
                if not enc_id: continue
                
                if enc_id not in encounters:
                    encounters[enc_id] = []
                encounters[enc_id].append(row)
    return encounters

def format_currency(val):
    try:
        if not val: return "$0.00"
        return f"${float(val):.2f}"
    except:
        return val

def generate_360_report(enc_id, rows, all_claims):
    if not rows: return "No details found."
    
    root = rows[0]
    md = []
    md.append(f"# Encounter 360 View: {enc_id}")
    
    # 1. & 2. & 3. (Demographics, Appointment, Clinical - Same as before)
    # --- Demographics ---
    md.append("## 1. Demographics & Context")
    pat_name = "N/A"
    for r in rows:
        c = all_claims.get(r['ClaimID']) # ClaimID here is ERA Ref ID
        if c and c.get('PatientName'):
            pat_name = c.get('PatientName')
            break
            
    prov_name = root.get('ProviderName') or "N/A"
    loc_name = root.get('FacilityName') or "N/A"
    md.append(f"**Patient**: {pat_name} (Case: {root.get('PatientCaseID', 'N/A')})")
    md.append(f"**Provider**: {prov_name} (NPI: {root.get('ProviderNPI', 'N/A')})")
    md.append(f"**Location**: {loc_name}")
    md.append("")

    # --- Appointment/Insurance ---
    md.append("## 2. Appointment & Insurance")
    md.append(f"- **Date**: {root.get('EncounterDate', 'N/A')}")
    md.append(f"- **Appointment**: {root.get('Appt_Type', 'N/A')} ({root.get('Appt_Start', 'N/A')} - {root.get('Appt_End', 'N/A')})")
    md.append(f"- **Insurance**: **{root.get('Insurance_Company', 'N/A')}**")
    md.append(f"  - Plan: {root.get('Insurance_Plan', 'N/A')}")
    md.append(f"  - Policy: `{root.get('Insurance_PolicyNum', 'N/A')}`")
    md.append("")

    # --- Clinical ---
    md.append("## 3. Clinical")
    diags = set()
    for r in rows:
        for i in range(1, 9):
            d = r.get(f'DiagID_{i}')
            if d: diags.add(d)
    if diags:
        md.append(f"**Diagnoses**: {', '.join([f'`{d}`' for d in sorted(list(diags))])}")
    else:
        md.append("*No diagnoses found.*")
    md.append("")

    # 4. Financials (Hierarchy: ERA Ref ID -> Tebra Claim ID -> Lines)
    md.append("## 4. Financials & Claims Bundle")
    
    # Group by ERA Reference ID (ClaimID column in CSV)
    ref_map = collections.defaultdict(list)
    for r in rows:
        ref_map[r['ClaimID']].append(r)
        
    for ref_id, ref_rows in ref_map.items():
        claim_meta = all_claims.get(ref_id, {})
        
        md.append(f"### ERA Reference ID: `{ref_id}`")
        if claim_meta:
            md.append(f"> **Payer**: {claim_meta.get('PayerName')} | **Status**: {claim_meta.get('Status')} | **Received**: {claim_meta.get('ReceivedDate')}")
            md.append(f"> **Total Patient Resp**: {format_currency(claim_meta.get('PatResp'))}")
        
        # Inner Group by Tebra Claim ID (DB_ClaimID)
        tebra_map = collections.defaultdict(list)
        for r in ref_rows:
            tebra_map[r['DB_ClaimID']].append(r)
            
        for tebra_id, lines in tebra_map.items():
            md.append(f"#### Tebra Claim ID: `{tebra_id}`")
            
            md.append("| Date | Code | Description | Billed | Paid | Adjustments |")
            md.append("|---|---|---|---|---|---|")
            
            t_billed = 0.0
            t_paid = 0.0
            
            for line in lines:
                b = float(line.get('Billed', 0) or 0)
                p = float(line.get('Paid', 0) or 0)
                t_billed += b
                t_paid += p
                
                desc = line.get('Proc_Name') or line.get('Proc_TypeDesc') or "N/A"
                if len(desc) > 30: desc = desc[:27] + "..."
                adj = line.get('Adjustments', '').replace(';', '<br>')
                
                md.append(f"| {line.get('Date')} | **{line.get('ProcCode')}** | {desc} | {format_currency(b)} | {format_currency(p)} | {adj} |")
            
            md.append(f"| | | **Subtotal** | **{format_currency(t_billed)}** | **{format_currency(t_paid)}** | |")
            md.append("")
            
    return "\n".join(md)

def main():
    all_claims = load_claims()
    enc_groups = load_encounter_groups()
    
    if TARGET_ENCOUNTER_ID not in enc_groups:
        print(f"Encounter {TARGET_ENCOUNTER_ID} not found.")
        return
        
    group_rows = enc_groups[TARGET_ENCOUNTER_ID]
    report = generate_360_report(TARGET_ENCOUNTER_ID, group_rows, all_claims)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(report)
    
    print(f"Generated {OUTPUT_FILE} for Encounter {TARGET_ENCOUNTER_ID}")

if __name__ == "__main__":
    main()
