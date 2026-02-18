"""
ERA Parser Module (XML-wrapped 835).
Refactored from verified logic in pase_specific_835.py.
"""
import xml.etree.ElementTree as ET

class EraParser:
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

    @staticmethod
    def get_element(segment_node, tag_name):
        """Retrieve text from a specific XML tag within a segment."""
        node = segment_node.find(tag_name)
        return node.text if node is not None else ""

    @staticmethod
    def get_all_elements(segment_node, seg_name):
        """Retrieve all data elements for a segment in order."""
        elements = []
        for i in range(1, 40):
            tag = f"{seg_name}{i:02d}"
            node = segment_node.find(tag)
            if node is not None:
                text = node.text
                if text is None:
                     text = "".join(node.itertext())
                elements.append((tag, text))
        return elements

    def parse(self, content):
        """Parse 835 XML content into structured dictionary."""
        wrapped_content = f"<root>{content}</root>"
        try:
            root = ET.fromstring(wrapped_content)
        except ET.ParseError as e:
            return {'error': str(e)}

        parsed_data = {
            'segments': [], 
            'payer': {},
            'payee': {},
            'claims': []
        }
        
        current_loop_type = None
        current_claim = None
        current_svc = None
        
        # Iterate all segments
        for segment in root.iter('segment'):
            seg_id = segment.get('name')
            seg_desc = self.SEGMENT_DESC.get(seg_id, "Unknown Segment")
            
            # Granular elements (optional, can be disabled for speed if needed)
            elements = self.get_all_elements(segment, seg_id)
            parsed_data['segments'].append({
                'id': seg_id,
                'desc': seg_desc,
                'elements': elements
            })
            
            # --- Business Logic ---
            # --- Business Logic ---
            if seg_id == 'BPR':
                 parsed_data['payment'] = {
                     'total_paid': self.get_element(segment, 'BPR02'),
                     'method': self.get_element(segment, 'BPR04'),
                     'format': self.get_element(segment, 'BPR05')
                 }
                 
            elif seg_id == 'TRN':
                 trace_type = self.get_element(segment, 'TRN01')
                 if trace_type == '1': # Current Transaction Trace Numbers
                     parsed_data['payment']['check_number'] = self.get_element(segment, 'TRN02')
                     parsed_data['payment']['origin_company'] = self.get_element(segment, 'TRN03')
                     
            elif seg_id == 'N1':
                entity_id = self.get_element(segment, 'N101')
                if entity_id == 'PR':
                    current_loop_type = 'PAYER'
                    parsed_data['payer']['name'] = self.get_element(segment, 'N102')
                    parsed_data['payer']['id'] = self.get_element(segment, 'N104')
                elif entity_id == 'PE':
                    current_loop_type = 'PAYEE'
                    parsed_data['payee']['name'] = self.get_element(segment, 'N102')
                    parsed_data['payee']['id'] = self.get_element(segment, 'N104')
                elif entity_id == 'QC': # Patient
                     # Usually QC comes in NM1, but handling just in case
                     if current_claim:
                         current_claim['patient']['id'] = self.get_element(segment, 'N104')
                        
            elif seg_id == 'N3':
                addr = self.get_element(segment, 'N301')
                if current_loop_type == 'PAYER':
                    parsed_data['payer']['address'] = addr
                elif current_loop_type == 'PAYEE':
                    parsed_data['payee']['address'] = addr
                    
            elif seg_id == 'N4':
                city = self.get_element(segment, 'N401')
                state = self.get_element(segment, 'N402')
                zip_code = self.get_element(segment, 'N403')
                loc = f"{city}, {state} {zip_code}"
                if current_loop_type == 'PAYER':
                    parsed_data['payer']['location'] = loc
                elif current_loop_type == 'PAYEE':
                    parsed_data['payee']['location'] = loc
                    
            elif seg_id == 'CLP':
                current_loop_type = 'CLAIM'
                # Save previous
                if current_claim:
                    if current_svc: current_claim['service_lines'].append(current_svc)
                    parsed_data['claims'].append(current_claim)
                
                current_claim = {
                    'claim_id': self.get_element(segment, 'CLP01'),
                    'payer_control_number': self.get_element(segment, 'CLP07'),
                    'status_code': self.get_element(segment, 'CLP02'),
                    'charge_amount': self.get_element(segment, 'CLP03'),
                    'paid_amount': self.get_element(segment, 'CLP04'),
                    'patient_resp': self.get_element(segment, 'CLP05'),
                    'patient': {},
                    'provider': {},
                    'service_lines': [],
                    'adjustments': []
                }
                current_svc = None
            
            elif seg_id == 'NM1':
                 entity_id = self.get_element(segment, 'NM101')
                 if entity_id == 'QC' and current_claim: # Patient
                     lname = self.get_element(segment, 'NM103')
                     fname = self.get_element(segment, 'NM104')
                     mid = self.get_element(segment, 'NM105')
                     current_claim['patient']['name'] = f"{lname}, {fname} {mid}".strip()
                     current_claim['patient']['id'] = self.get_element(segment, 'NM109')
                 elif entity_id == '82' and current_claim: # Rendering Provider
                     lname = self.get_element(segment, 'NM103')
                     fname = self.get_element(segment, 'NM104')
                     current_claim['provider'] = {'name': f"{fname} {lname}".strip()}

            elif seg_id == 'SVC':
                if current_claim:
                    if current_svc: current_claim['service_lines'].append(current_svc)
                    current_svc = {
                         'proc_code': self.get_element(segment, 'SVC01'),
                         'charge': self.get_element(segment, 'SVC02'),
                         'paid': self.get_element(segment, 'SVC03'),
                         'date': '',
                         'units': self.get_element(segment, 'SVC05'),
                         'adjustments': [],
                         'refs': []
                    }
            
            elif seg_id == 'DTM':
                 code = self.get_element(segment, 'DTM01')
                 date_val = self.get_element(segment, 'DTM02')
                 if code == '472' and current_svc:
                     current_svc['date'] = date_val
                 elif code == '405':
                     # Production Date (Header) or Effective Date
                     if current_loop_type == 'PAYER':
                         parsed_data['payer']['effective_date'] = date_val
                     elif current_loop_type is None: # Header DTM
                         parsed_data['payment']['date'] = date_val
                 elif code == '150' or code == '151':
                     # Check or Service Period Start/End
                     pass

            elif seg_id == 'CAS':
                 group = self.get_element(segment, 'CAS01')
                 code = self.get_element(segment, 'CAS02')
                 amt = self.get_element(segment, 'CAS03')
                 adj_str = f"{group}-{code}:{amt}"
                 
                 if current_svc:
                     current_svc['adjustments'].append(adj_str)
                 elif current_claim:
                     current_claim['adjustments'].append(adj_str)

            elif seg_id == 'REF':
                 qual = self.get_element(segment, 'REF01')
                 val = self.get_element(segment, 'REF02')
                 if current_svc:
                     current_svc['refs'].append({'type': qual, 'value': val})
        
        # Final Save
        if current_claim:
            if current_svc: current_claim['service_lines'].append(current_svc)
            parsed_data['claims'].append(current_claim)

        return parsed_data
