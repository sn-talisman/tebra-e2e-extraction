"""
Generate 360-degree encounter views from PostgreSQL to verify data integrity.
This mirrors the format in encounter_view_enriched.md
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def generate_360_view(encounter_id):
    """Generate a 360-degree view for a specific encounter."""
    conn = get_connection()
    cur = conn.cursor()
    
    view = {
        "encounter_id": encounter_id,
        "context": None,
        "entities": {"patient": None, "provider": None, "payer": None},
        "clinical": {"diagnoses": []},
        "financials": {"lines": [], "totals": {"billed": 0, "paid": 0}},
        "era_bundles": []
    }
    
    # 1. Context (Encounter & Location)
    cur.execute("""
        SELECT 
            e.encounter_guid,
            e.start_date,
            e.status,
            e.appt_type,
            e.appt_reason,
            e.pos_description,
            l.name as location_name,
            l.address_block,
            e.location_guid
        FROM tebra.clin_encounter e
        LEFT JOIN tebra.cmn_location l ON e.location_guid = l.location_guid
        WHERE e.encounter_id = %s
    """, (encounter_id,))
    context = cur.fetchone()
    if context:
        view["context"] = dict(context)
    
    # 2. Patient
    cur.execute("""
        SELECT 
            p.full_name,
            p.patient_id,
            p.case_id,
            p.patient_guid,
            p.dob,
            p.gender,
            p.address_line1,
            p.city,
            p.state,
            p.zip
        FROM tebra.clin_encounter e
        JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
        WHERE e.encounter_id = %s
    """, (encounter_id,))
    patient = cur.fetchone()
    if patient:
        view["entities"]["patient"] = dict(patient)
    
    # 3. Provider
    cur.execute("""
        SELECT 
            pr.name,
            pr.npi
        FROM tebra.clin_encounter e
        LEFT JOIN tebra.cmn_provider pr ON e.provider_guid = pr.provider_guid
        WHERE e.encounter_id = %s
    """, (encounter_id,))
    provider = cur.fetchone()
    if provider:
        view["entities"]["provider"] = dict(provider)
    
    # 4. Insurance/Payer - from insurance policy linked to encounter
    cur.execute("""
        SELECT 
            ip.company_name,
            ip.plan_name,
            ip.policy_number,
            ip.group_number
        FROM tebra.clin_encounter e
        LEFT JOIN tebra.ref_insurance_policy ip ON e.insurance_policy_key = ip.policy_key
        WHERE e.encounter_id = %s
        LIMIT 1
    """, (encounter_id,))
    payer = cur.fetchone()
    if payer:
        view["entities"]["payer"] = dict(payer)
    
    # 5. Diagnoses
    cur.execute("""
        SELECT diag_code, description, precedence
        FROM tebra.clin_encounter_diagnosis
        WHERE encounter_id = %s
        ORDER BY precedence ASC
    """, (encounter_id,))
    diagnoses = cur.fetchall()
    view["clinical"]["diagnoses"] = [dict(d) for d in diagnoses]
    
    # 6. Claim Lines (Financials)
    cur.execute("""
        SELECT 
            cl.date_of_service,
            cl.proc_code,
            cl.description,
            cl.billed_amount,
            cl.paid_amount,
            cl.units,
            cl.claim_reference_id,
            cl.adjustments_json,
            cl.claim_status,
            cl.payer_status
        FROM tebra.fin_claim_line cl
        WHERE cl.encounter_id = %s
        ORDER BY cl.date_of_service ASC
    """, (encounter_id,))
    lines = cur.fetchall()
    view["financials"]["lines"] = [dict(l) for l in lines]
    view["financials"]["totals"]["billed"] = sum(float(l.get('billed_amount') or 0) for l in lines)
    view["financials"]["totals"]["paid"] = sum(float(l.get('paid_amount') or 0) for l in lines)
    
    # 7. ERA Payment Bundles
    if lines:
        claim_refs = list(set([l['claim_reference_id'] for l in lines if l.get('claim_reference_id')]))
        if claim_refs:
            placeholders = ', '.join(['%s'] * len(claim_refs))
            cur.execute(f"""
                SELECT 
                    claim_reference_id,
                    payer_name,
                    total_paid,
                    total_patient_resp
                FROM tebra.fin_era_bundle
                WHERE claim_reference_id IN ({placeholders})
            """, tuple(claim_refs))
            era_bundles = cur.fetchall()
            view["era_bundles"] = [dict(e) for e in era_bundles]
    
    cur.close()
    conn.close()
    return view

def format_view_as_markdown(view):
    """Format the 360-degree view as markdown."""
    enc_id = view["encounter_id"]
    md = f"# Encounter 360 View: {enc_id}\n"
    md += "**Generated from PostgreSQL Database**\n\n"
    
    # 1. Context
    md += "## 1. Context\n"
    ctx = view.get("context")
    if ctx:
        md += f"- **Encounter GUID**: `{ctx.get('encounter_guid')}`\n"
        md += f"- **Date**: {ctx.get('start_date')}\n"
        md += f"- **Status**: {ctx.get('status')}\n"
        md += f"- **Type**: {ctx.get('appt_type')}\n"
        md += f"- **Reason**: {ctx.get('appt_reason')}\n"
        md += f"- **Location**: {ctx.get('location_name')}\n"
        md += f"- **Address**: `{ctx.get('address_block')}`\n"
        md += f"- **Place of Service**: {ctx.get('pos_description')}\n"
    else:
        md += "- **ERROR**: Encounter not found!\n"
    
    # 2. Entities
    md += "\n## 2. Entities\n"
    
    # Patient
    md += "### Patient\n"
    pt = view["entities"].get("patient")
    if pt:
        md += f"- **Name**: **{pt.get('full_name')}**\n"
        md += f"- **Case ID**: `{pt.get('case_id')}`\n"
        md += f"- **Tebra ID**: `{pt.get('patient_id')}`\n"
        md += f"- **Patient GUID**: `{pt.get('patient_guid')}`\n"
        md += f"- **DOB**: {pt.get('dob')} ({pt.get('sex')})\n"
        md += f"- **Address**: {pt.get('address_line1')}, {pt.get('city')}, {pt.get('state')} {pt.get('zip')}\n"
    else:
        md += "- **ERROR**: No patient found!\n"
    
    # Provider
    md += "\n### Provider\n"
    prov = view["entities"].get("provider")
    if prov:
        md += f"- **Name**: {prov.get('name')}\n"
        md += f"- **NPI**: `{prov.get('npi')}`\n"
    else:
        md += "- **ERROR**: No provider found!\n"
    
    # Payer
    md += "\n### Payer (Insurance)\n"
    payer = view["entities"].get("payer")
    if payer and any(payer.values()):
        md += f"- **Company**: {payer.get('company_name')}\n"
        md += f"- **Plan**: {payer.get('plan_name')}\n"
        md += f"- **Policy #**: `{payer.get('policy_number')}`\n"
        md += f"- **Group #**: `{payer.get('group_number')}`\n"
    else:
        md += "- **ERROR**: No insurance policy found!\n"
    
    # 3. Clinical Data
    md += "\n## 3. Clinical Data\n"
    md += "### Diagnoses\n"
    if view["clinical"]["diagnoses"]:
        for d in view["clinical"]["diagnoses"]:
            md += f"- **{d.get('diag_code')}** - {d.get('description')} (Precedence: {d.get('precedence')})\n"
    else:
        md += "- **ERROR**: No diagnoses found!\n"
    
    # 4. Financials
    md += "\n## 4. Financials (Claim Lines)\n"
    lines = view["financials"]["lines"]
    if lines:
        md += "| Date | Proc | Description | Billed | Paid | Units | Claim Ref | Adjustments |\n"
        md += "|---|---|---|---|---|---|---|---|\n"
        for l in lines:
            desc = l.get('description') or 'N/A'
            desc = desc[:50] + "..." if len(desc) > 50 else desc
            md += f"| {l.get('date_of_service')} | `{l.get('proc_code')}` | {desc} | ${float(l.get('billed_amount') or 0):.2f} | ${float(l.get('paid_amount') or 0):.2f} | {l.get('units')} | `{l.get('claim_reference_id')}` | {l.get('adjustments_json')} |\n"
        
        md += f"\n**Totals**: Billed: **${view['financials']['totals']['billed']:.2f}** | Paid: **${view['financials']['totals']['paid']:.2f}**\n"
    else:
        md += "- **ERROR**: No claim lines found for this encounter!\n"
    
    # 5. ERA Bundles
    md += "\n## 5. ERA Payment Bundles\n"
    if view["era_bundles"]:
        md += "| Claim Ref ID | Payer Name | Total Paid | Patient Resp |\n"
        md += "|---|---|---|---|\n"
        for e in view["era_bundles"]:
            md += f"| `{e.get('claim_reference_id')}` | {e.get('payer_name')} | ${float(e.get('total_paid') or 0):.2f} | ${float(e.get('total_patient_resp') or 0):.2f} |\n"
    else:
        md += "- **No ERA bundles found** (or no claim lines to link)\n"
    
    return md

def check_data_integrity():
    """Check data integrity across all tables and report gaps."""
    conn = get_connection()
    cur = conn.cursor()
    
    print("=" * 60)
    print("DATA INTEGRITY CHECK")
    print("=" * 60)
    
    # Table counts
    tables = [
        ("tebra.clin_encounter", "Encounters"),
        ("tebra.cmn_patient", "Patients"),
        ("tebra.cmn_provider", "Providers"),
        ("tebra.cmn_location", "Locations"),
        ("tebra.ref_insurance_policy", "Insurance Policies"),
        ("tebra.clin_encounter_diagnosis", "Diagnoses"),
        ("tebra.fin_claim_line", "Claim Lines"),
        ("tebra.fin_era_bundle", "ERA Bundles"),
        ("tebra.fin_era_report", "ERA Reports")
    ]
    
    print("\n### Table Counts:")
    for table, name in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()['count']
            print(f"  {name}: {count:,}")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")
    
    # Check linkages
    print("\n### Linkage Analysis:")
    
    # Encounters with patients
    cur.execute("""
        SELECT 
            COUNT(*) as total_enc,
            SUM(CASE WHEN p.patient_guid IS NOT NULL THEN 1 ELSE 0 END) as with_patient
        FROM tebra.clin_encounter e
        LEFT JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
    """)
    row = cur.fetchone()
    print(f"  Encounters → Patients: {row['with_patient']}/{row['total_enc']}")
    
    # Encounters with providers
    cur.execute("""
        SELECT 
            COUNT(*) as total_enc,
            SUM(CASE WHEN pr.provider_guid IS NOT NULL THEN 1 ELSE 0 END) as with_provider
        FROM tebra.clin_encounter e
        LEFT JOIN tebra.cmn_provider pr ON e.provider_guid = pr.provider_guid
    """)
    row = cur.fetchone()
    print(f"  Encounters → Providers: {row['with_provider']}/{row['total_enc']}")
    
    # Encounters with diagnoses
    cur.execute("""
        SELECT 
            (SELECT COUNT(DISTINCT encounter_id) FROM tebra.clin_encounter) as total_enc,
            (SELECT COUNT(DISTINCT encounter_id) FROM tebra.clin_encounter_diagnosis) as with_diag
    """)
    row = cur.fetchone()
    print(f"  Encounters → Diagnoses: {row['with_diag']}/{row['total_enc']}")
    
    # Encounters with claim lines
    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM tebra.clin_encounter) as total_enc,
            (SELECT COUNT(DISTINCT encounter_id) FROM tebra.fin_claim_line WHERE encounter_id IS NOT NULL) as with_claims
    """)
    row = cur.fetchone()
    print(f"  Encounters → Claim Lines: {row['with_claims']}/{row['total_enc']}")
    
    # Claims with ERA bundles
    cur.execute("""
        SELECT 
            COUNT(*) as total_claims,
            SUM(CASE WHEN eb.claim_reference_id IS NOT NULL THEN 1 ELSE 0 END) as with_era
        FROM tebra.fin_claim_line cl
        LEFT JOIN tebra.fin_era_bundle eb ON cl.claim_reference_id = eb.claim_reference_id
    """)
    row = cur.fetchone()
    print(f"  Claim Lines → ERA Bundles: {row['with_era']}/{row['total_claims']}")
    
    # Encounters with insurance
    cur.execute("""
        SELECT 
            COUNT(*) as total_enc,
            SUM(CASE WHEN ip.policy_key IS NOT NULL THEN 1 ELSE 0 END) as with_ins
        FROM tebra.clin_encounter e
        LEFT JOIN tebra.ref_insurance_policy ip ON e.insurance_policy_key = ip.policy_key
    """)
    row = cur.fetchone()
    print(f"  Encounters → Insurance: {row['with_ins']}/{row['total_enc']}")
    
    cur.close()
    conn.close()

def main():
    print("\n" + "=" * 60)
    print("360-DEGREE ENCOUNTER VIEW GENERATOR")
    print("=" * 60)
    
    # First, run integrity check
    check_data_integrity()
    
    # Get 3 sample encounters with the most complete data
    conn = get_connection()
    cur = conn.cursor()
    
    # Find encounters that have claims (to verify 360 view completeness)
    cur.execute("""
        SELECT DISTINCT e.encounter_id, e.start_date, l.name as location
        FROM tebra.clin_encounter e
        JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
        JOIN tebra.cmn_location l ON e.location_guid = l.location_guid
        JOIN tebra.fin_claim_line cl ON e.encounter_id = cl.encounter_id
        ORDER BY e.start_date DESC
        LIMIT 3
    """)
    encounters = cur.fetchall()
    cur.close()
    conn.close()
    
    print(f"\n### Generating 360-Degree Views for {len(encounters)} Encounters:\n")
    
    all_views_md = ""
    for enc in encounters:
        print(f"- Encounter {enc['encounter_id']} ({enc['start_date']} @ {enc['location']})")
        view = generate_360_view(enc['encounter_id'])
        md = format_view_as_markdown(view)
        all_views_md += md + "\n\n---\n\n"
    
    # Write to file
    output_file = "encounter_360_views_verification.md"
    with open(output_file, 'w') as f:
        f.write("# 360-Degree Encounter Views - Data Verification\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write("---\n\n")
        f.write(all_views_md)
    
    print(f"\n✅ Views saved to: {output_file}")

if __name__ == "__main__":
    main()
