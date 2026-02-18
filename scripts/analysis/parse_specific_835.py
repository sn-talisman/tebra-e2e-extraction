"""
Parse specific 835 ERA.
Target File: P05536D260228494U1932-26026B100008811300.RMT
Method: Parse Tebra's XML representation of 835 segments.
Granularity: Finest level (all segments).
"""
import json
import logging
import xml.etree.ElementTree as ET
from collections import defaultdict

# Segment Descriptions
SEGMENT_DESC = {
    'ST': 'Transaction Set Header',
    'BPR': 'Financial Information',
    'TRN': 'Reassociation Trace Number',
    'CUR': 'Currency',
    'REF': 'Reference Information',
    'DTM': 'Date/Time Reference',
    'N1': 'Party Identification',
    'N3': 'Party Address',
    'N4': 'Party Geographic Location',
    'PER': 'Administrative Communications Contact',
    'LX': 'Header Number',
    'TS3': 'Provider Summary Information',
    'TS2': 'Provider Supplemental Summary Information',
    'CLP': 'Claim Payment Information',
    'NM1': 'Individual or Organizational Name',
    'MIA': 'Inpatient Adjudication',
    'MOA': 'Outpatient Adjudication',
    'SVC': 'Service Payment Information',
    'CAS': 'Claim Adjustment',
    'PLB': 'Provider Level Adjustment',
    'SE': 'Transaction Set Trailer',
    'GE': 'Functional Group Trailer',
    'IEA': 'Interchange Control Trailer',
    'ISA': 'Interchange Control Header',
    'GS': 'Functional Group Header',
    'AMT': 'Monetary Amount',
    'QTY': 'Quantity',
    'LQ': 'Industry Code',
}

TARGET_FILENAME = "P05536D260228494U1932-26026B100008811300.RMT"

def get_element(segment_node, tag_name):
    """Retrieve text from a specific XML tag within a segment."""
    node = segment_node.find(tag_name)
    return node.text if node is not None else ""

def get_all_elements(segment_node, seg_name):
    """Retrieve all data elements for a segment in order."""
    elements = []
    # Assuming elements are named SEG01, SEG02...
    # We will search for 01 to 30 (arbitrary max)
    for i in range(1, 40):
        tag = f"{seg_name}{i:02d}"
        node = segment_node.find(tag)
        if node is not None:
            # Check for composite children? 
            # If text is None, might have children like <Comp>...
            text = node.text
            if text is None:
                # Naive composite check: just grab all text
                 text = "".join(node.itertext())
            elements.append((tag, text))
        else:
            # If we miss one, checking if we missed a gap or end of segment.
            # Some XMLs skip empty tags. We continue checking a few more just in case.
            # But usually they are sequential.
            pass
    return elements

def parse_835_full_xml(content):
    wrapped_content = f"<root>{content}</root>"
    try:
        root = ET.fromstring(wrapped_content)
    except ET.ParseError as e:
        print(f"Failed to parse XML content: {e}")
        return None

    # We will build a structured object for "Easy Read" and a list for "Granular Dump"
    parsed_data = {
        'segments': [], # Linear list of all segments
        'payer': {},
        'payee': {},
        'claims': []
    }
    
    current_loop_type = None # 'PAYER', 'PAYEE', 'CLAIM'
    current_claim = None
    current_svc = None
    
    # Iterate all segments
    for segment in root.iter('segment'):
        seg_id = segment.get('name')
        seg_desc = SEGMENT_DESC.get(seg_id, "Unknown Segment")
        
        # Get elements
        elements = get_all_elements(segment, seg_id)
        
        # Add to granular list
        parsed_data['segments'].append({
            'id': seg_id,
            'desc': seg_desc,
            'elements': elements
        })
        
        # --- Structured Logic ---
        
        # Identify Loop Context
        if seg_id == 'N1':
            entity_id = get_element(segment, 'N101')
            if entity_id == 'PR':
                current_loop_type = 'PAYER'
                parsed_data['payer']['name'] = get_element(segment, 'N102')
                parsed_data['payer']['id'] = get_element(segment, 'N104')
            elif entity_id == 'PE':
                current_loop_type = 'PAYEE'
                parsed_data['payee']['name'] = get_element(segment, 'N102')
                parsed_data['payee']['id'] = get_element(segment, 'N104')
            elif entity_id == 'QC': # Patient
                if current_claim:
                    current_claim['patient'] = {
                        'id': get_element(segment, 'N104') # Often NM1 is used for patient name, but N1 can occur
                    }
                    
        elif seg_id == 'N3':
            addr = get_element(segment, 'N301')
            if current_loop_type == 'PAYER':
                parsed_data['payer']['address'] = addr
            elif current_loop_type == 'PAYEE':
                parsed_data['payee']['address'] = addr
                
        elif seg_id == 'N4':
            city = get_element(segment, 'N401')
            state = get_element(segment, 'N402')
            zip_code = get_element(segment, 'N403')
            loc = f"{city}, {state} {zip_code}"
            if current_loop_type == 'PAYER':
                parsed_data['payer']['location'] = loc
            elif current_loop_type == 'PAYEE':
                parsed_data['payee']['location'] = loc
                
        elif seg_id == 'CLP':
            current_loop_type = 'CLAIM'
            
            # Save previous claim context
            if current_claim:
                if current_svc: current_claim['service_lines'].append(current_svc)
                parsed_data['claims'].append(current_claim)
            
            current_claim = {
                'claim_id': get_element(segment, 'CLP01'), # Patient Control Number
                'payer_control_number': get_element(segment, 'CLP07'),
                'status_code': get_element(segment, 'CLP02'),
                'charge_amount': get_element(segment, 'CLP03'),
                'paid_amount': get_element(segment, 'CLP04'),
                'patient_resp': get_element(segment, 'CLP05'),
                'patient': {},
                'provider': {},
                'service_lines': [],
                'adjustments': []
            }
            current_svc = None
            


        elif seg_id == 'SVC':
            if current_claim:
                if current_svc: current_claim['service_lines'].append(current_svc)
                current_svc = {
                     'proc_code': get_element(segment, 'SVC01'),
                     'charge': get_element(segment, 'SVC02'),
                     'paid': get_element(segment, 'SVC03'),
                     'date': '',
                     'units': get_element(segment, 'SVC05'),
                     'adjustments': [],
                     'refs': []
                }
        
        elif seg_id == 'DTM':
             code = get_element(segment, 'DTM01')
             date_val = get_element(segment, 'DTM02')
             if code == '472' and current_svc:
                 current_svc['date'] = date_val
             elif code == '405' and current_loop_type == 'PAYER':
                 parsed_data['payer']['effective_date'] = date_val

        elif seg_id == 'CAS':
             group = get_element(segment, 'CAS01')
             code = get_element(segment, 'CAS02')
             amt = get_element(segment, 'CAS03')
             adj_str = f"{group}-{code}:{amt}"
             
             if current_svc:
                 current_svc['adjustments'].append(adj_str)
             elif current_claim:
                 current_claim['adjustments'].append(adj_str)

        elif seg_id == 'REF':
             # Reference Information
             qual = get_element(segment, 'REF01')
             val = get_element(segment, 'REF02')
             
             if current_svc:
                 current_svc['refs'].append({'type': qual, 'value': val})
        
        elif seg_id == 'NM1':
            entity_id = get_element(segment, 'NM101')
            if entity_id == 'QC' and current_claim: # Patient
                lname = get_element(segment, 'NM103')
                fname = get_element(segment, 'NM104')
                mid = get_element(segment, 'NM105')
                current_claim['patient']['name'] = f"{lname}, {fname} {mid}".strip()
                current_claim['patient']['id'] = get_element(segment, 'NM109')
            elif entity_id == '82' and current_claim: # Rendering Provider
                lname = get_element(segment, 'NM103')
                fname = get_element(segment, 'NM104')
                current_claim['provider'] = {'name': f"{fname} {lname}".strip()}

    # Final Save
    if current_claim:
        if current_svc: current_claim['service_lines'].append(current_svc)
        parsed_data['claims'].append(current_claim)

    return parsed_data

def process_specific_era():
    # Fetch specific ERA by filename
    try:
        from src.connection import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        target_file_pattern = "%26026B100008811300.RMT" # Row 8 from summary
        print(f"Searching for ERA matching: {target_file_pattern}...")
        
        query = f"""
        SELECT FILENAME, FILECONTENTS 
        FROM PM_CLEARINGHOUSERESPONSE 
        WHERE PRACTICEGUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
          AND FILENAME LIKE '{target_file_pattern}'
          AND CLEARINGHOUSERESPONSEREPORTTYPENAME = 'ERA'
        LIMIT 1
        """
        cursor.execute(query)
        row = cursor.fetchone()
        
        if not row:
            print("Target ERA not found in DB.")
            return

        target_filename = row[0]
        content = row[1]
        
    except Exception as e:
        print(f"DB Error: {e}")
        return
        
    # Skip JSON loading, use direct DB content
    parsed = parse_835_full_xml(content)
    if not parsed:
        return

    print(f"### ERA Full Analysis: `{target_filename}`\n")
    
    # 1. Header Info
    payer = parsed['payer']
    payee = parsed['payee']
    print("#### Entities")
    print("| Role | Name | ID | Address |")
    print("|---|---|---|---|")
    print(f"| **Payer** | {payer.get('name','')} | {payer.get('id','')} | {payer.get('address','')} {payer.get('location','')} |")
    print(f"| **Payee** | {payee.get('name','')} | {payee.get('id','')} | {payee.get('address','')} {payee.get('location','')} |")
    print("")

    # Generate Full Markdown Report
    report_file = "ERA_Row8_Report.md"
    with open(report_file, "w") as f:
        f.write(f"# ERA Report: `{target_filename}`\n\n")
        
        # 1. Header
        payer = parsed['payer']
        payee = parsed['payee']
        f.write("## Entities\n")
        f.write("| Role | Name | ID | Address |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| **Payer** | {payer.get('name','')} | {payer.get('id','')} | {payer.get('address','')} {payer.get('location','')} |\n")
        f.write(f"| **Payee** | {payee.get('name','')} | {payee.get('id','')} | {payee.get('address','')} {payee.get('location','')} |\n\n")
        
        # 2. Claims Table
        f.write("## Claims Detail\n")
        f.write("Note: 'Line ID' from REF*6R.\n\n")
        f.write("| Claim/Line ID | Patient | Provider | Date | Proc | Billed | Paid | PatResp | Adjs/Remarks |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        
        distinct_patients = set()
        
        for c in parsed['claims']:
            # Claim Info
            raw_cid = c['claim_id']
            payer_cn = c['payer_control_number']
            pat_name = c['patient'].get('name','Unknown')
            pat_id = c['patient'].get('id','')
            distinct_patients.add(pat_name)
            
            provider_info = c.get('provider', {}).get('name', 'Unknown')
            c_adjs = ", ".join(c['adjustments']) if c['adjustments'] else "-"
            
            f.write(f"| **{raw_cid}**<br>({payer_cn}) | {pat_name}<br>ID:{pat_id} | {provider_info} | Claim | - | {c['charge_amount']} | {c['paid_amount']} | {c['patient_resp']} | {c_adjs} |\n")
            
            for svc in c['service_lines']:
                 s_adjs = ", ".join(svc['adjustments']) if svc['adjustments'] else "-"
                 ref_str = ""
                 if 'refs' in svc:
                     for r in svc['refs']:
                         if r['type'] == '6R':
                             import re
                             match = re.search(r'K(\d{6})[A-Z0-9]*$', r['value'])
                             ref_str = f"**{match.group(1)}**" if match else r['value']
                 
                 f.write(f"| {ref_str} | | | {svc['date']} | `{svc['proc_code']}` | {svc['charge']} | {svc['paid']} | - | {s_adjs} |\n")

    print(f"Report generated: {report_file}")
    print(f"Total Claims: {len(parsed['claims'])}")
    print(f"Distinct Patients found: {len(distinct_patients)}")
    for p in distinct_patients:
        print(f" - {p}")

if __name__ == "__main__":
    process_specific_era()
