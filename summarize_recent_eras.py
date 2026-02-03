"""
Summarize Recent ERAs.
Fetch last 10 ERAs for the target practice and display high-level summary.
"""
import json
import logging
import xml.etree.ElementTree as ET
from src.connection import get_connection

# Reusing simplified XML parsing logic
def get_element(segment_node, tag_name):
    node = segment_node.find(tag_name)
    return node.text if node is not None else ""

def parse_era_summary(content):
    """Parse key summary fields from 835 XML content."""
    wrapped_content = f"<root>{content}</root>"
    try:
        root = ET.fromstring(wrapped_content)
    except ET.ParseError:
        return {'payer': 'XML_ERROR', 'amount': '0.00', 'claims': 0}

    summary = {
        'payer': 'Unknown',
        'amount': '0.00',
        'claims': 0,
        'check_date': ''
    }
    
    # Iterate segments
    for segment in root.iter('segment'):
        seg_id = segment.get('name')
        
        if seg_id == 'N1':
            entity_id = get_element(segment, 'N101')
            if entity_id == 'PR':
                summary['payer'] = get_element(segment, 'N102')
        
        elif seg_id == 'BPR':
            summary['amount'] = get_element(segment, 'BPR02')
            summary['check_date'] = get_element(segment, 'BPR16') # Check Issue Date often here or BPR09/10 depending on version
            # Actually BPR16 is check date? Standard says BPR16 is date.
            
        elif seg_id == 'CLP':
            summary['claims'] += 1
            
    return summary

def summarize_recent_eras():
    conn = get_connection()
    cursor = conn.cursor()
    
    TARGET_GUID = 'EE5ED349-D9DD-4BF5-81A5-AA503A261961'
    
    print(f"Fetching last 10 ERAs for Practice GUID: {TARGET_GUID}...")
    
    query = f"""
    SELECT FILERECEIVEDATE, FILENAME, FILECONTENTS, SOURCENAME
    FROM PM_CLEARINGHOUSERESPONSE 
    WHERE PRACTICEGUID = '{TARGET_GUID}'
      AND CLEARINGHOUSERESPONSEREPORTTYPENAME = 'ERA'
    ORDER BY FILERECEIVEDATE DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    rows = cursor.fetchall() # List of tuples
    
    print(f"Found {len(rows)} ERAs. Analyzing...\n")
    
    print("| # | Received Date | Payer (Parsed) | Source (DB) | Claims | Amount | Filename |")
    print("|---|---|---|---|---|---|---|")
    
    for i, row in enumerate(rows, 1):
        date_recv = row[0]
        fname = row[1]
        content = row[2]
        source_db = row[3]
        
        summ = parse_era_summary(content)
        
        # Truncate filename for display
        fname_short = fname if len(fname) < 30 else "..." + fname[-27:]
        
        print(f"| {i} | {date_recv} | {summ['payer']} | {source_db} | {summ['claims']} | {summ['amount']} | `{fname_short}` |")

if __name__ == "__main__":
    summarize_recent_eras()
