import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))

from app.db.connection import get_db_cursor

def debug_crash():
    with get_db_cursor() as cur:
        # Test GREATEST
        cur.execute("SELECT GREATEST(NULL, 5), GREATEST(5, NULL), GREATEST(NULL, NULL)")
        print(f"GREATEST Test: {cur.fetchone()}")

        print("Executing ERA List Query...")
        
        # Copy-paste the SQL from eras.py
        sql = """
            SELECT 
                r.era_report_id,
                r.received_date,
                r.payer_name,
                r.check_number,
                -- Calculated Total Paid (Header is unreliable)
                COALESCE(
                    (SELECT SUM(cl.paid_amount) 
                     FROM tebra.fin_era_bundle b 
                     JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                     WHERE b.era_report_id = r.era_report_id), 
                    r.total_paid, 
                    0
                ) as total_paid,
                
                -- Calculated Total Billed
                COALESCE(
                    (SELECT SUM(cl.billed_amount) 
                     FROM tebra.fin_era_bundle b 
                     JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                     WHERE b.era_report_id = r.era_report_id), 
                    0
                ) as total_billed,
                
                -- Practice Name
                COALESCE(loc.name, 'Unknown Practice') as practice_name,
                
                -- Source Metrics (Use Line Count if Source is 0 or less than calculated)
                GREATEST(
                    r.claim_count_source,
                    (SELECT COUNT(cl.tebra_claim_id) 
                     FROM tebra.fin_era_bundle b 
                     JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                     WHERE b.era_report_id = r.era_report_id)
                ) as claim_count,
                
                -- Calculated Status Counts
                COUNT(CASE 
                    WHEN (cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%')
                      OR (cl.billed_amount > 0 AND cl.paid_amount = 0)
                    THEN 1 
                    ELSE NULL 
                END) as denied_count,
                
                COUNT(CASE 
                    WHEN cl.payer_status ILIKE '%%Rejected%%' OR cl.claim_status ILIKE '%%Rejected%%' THEN 1 
                    ELSE NULL 
                END) as rejected_count,

                -- Denial Reasons (Aggregate Distinct Codes)
                STRING_AGG(DISTINCT cl.adjustments_json, ', ') FILTER (WHERE cl.paid_amount = 0) as denial_reasons,

                'Processed' as status_display,

                -- ERA Type Logic
                CASE 
                    WHEN r.total_paid > 0 THEN 'Payment'
                    WHEN COUNT(CASE 
                        WHEN (cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%')
                          OR (cl.billed_amount > 0 AND cl.paid_amount = 0)
                        THEN 1 
                        ELSE NULL 
                    END) > 0 THEN 'Denial'
                    ELSE 'Informational'
                END as era_type
                
            FROM tebra.fin_era_report r
            LEFT JOIN tebra.cmn_practice loc ON r.practice_guid::uuid = loc.practice_guid
            LEFT JOIN tebra.fin_era_bundle b ON r.era_report_id = b.era_report_id
            LEFT JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
            
            
            WHERE r.practice_guid::uuid = 'ee5ed349-d9dd-4bf5-81a5-aa503a261961'
            
            GROUP BY r.era_report_id, r.received_date, r.payer_name, r.check_number, r.total_paid, r.payment_method, loc.name
            
            LIMIT 5
        """
        
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            print("Query executed successfully.")
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Query Failed: {e}")

if __name__ == "__main__":
    debug_crash()
