"""
Script to upsert ERA reports from INACTIVE practices.
"""
import psycopg2
from src.connection import get_connection
import hashlib

# Inactive practices with data
INACTIVE_PRACTICES = [
    ('6C6D879A-1C44-413B-A4C1-2038BF509CC1', 'SERAPHIC HEARTS LLC'),
    ('4A5D8523-EAAF-416B-BE37-F96803A7207F', 'Best Care Pediatrics'),
    ('51DF7D13-F57C-4CAC-84AE-CCE941722C63', 'Advanced Therapy Center, INC.'),
    ('CE358E9F-CFE4-4CDE-90A1-C08654B969C8', 'Royal Quest, LLC'),
    ('0515F295-A55E-4F6A-ACA8-B357BB47B924', 'Renewed Mind Therapy LLC'),
    ('34FCAD29-A565-4722-91CB-8E3B7604B05B', 'Behavioral Healthcare Services'),
    ('60F73E49-36E7-4EFF-B1CC-245C05C425B4', 'Bright futures wellness center'),
    ('0E9610F3-4F90-45F4-99D2-0B6B919A1BEC', 'Maxillofacial Surgery Innv Servc'),
    ('55D40C15-8E5C-4572-9E96-8887F509A8D7', 'NEW NARRATIVES, LLC'),
]

def upsert_inactive_practices():
    sf_conn = get_connection()
    sf_cur = sf_conn.cursor()
    
    pg_conn = psycopg2.connect(
        host='localhost', database='tebra_dw', 
        user='tebra_user', password='tebra_password'
    )
    pg_cur = pg_conn.cursor()
    
    total_inserted = 0
    
    for guid, name in INACTIVE_PRACTICES:
        print(f"\n=== Processing {name} ({guid}) ===")
        
        sf_cur.execute(f"""
            SELECT 
                CUSTOMERID, CLEARINGHOUSERESPONSEID, CLEARINGHOUSERESPONSEREPORTTYPEID,
                CLEARINGHOUSERESPONSEREPORTTYPENAME, CLEARINGHOUSERESPONSESOURCETYPEID,
                CLEARINGHOUSERESPONSESOURCETYPENAME, DENIED, FILENAME, FILERECEIVEDATE,
                ITEMCOUNT, PAYMENTID, PRACTICEGUID, PROCESSEDFLAG, REJECTED,
                RESPONSETYPE, CLEARINGHOUSERESPONSETYPENAME, REVIEWEDFLAG,
                SOURCEADDRESS, SOURCENAME, TITLE, TOTALAMOUNT
            FROM PM_CLEARINGHOUSERESPONSE 
            WHERE PRACTICEGUID = '{guid}'
              AND FILERECEIVEDATE >= '2025-08-08'
        """)
        
        rows = sf_cur.fetchall()
        print(f"  Found {len(rows)} records")
        
        inserted = 0
        for row in rows:
            (customer_id, ch_response_id, report_type_id, report_type_name,
             source_type_id, source_type_name, denied_cnt, filename,
             date_recv, item_count, payment_id, prac_guid, processed_flag,
             rejected_cnt, response_type, response_type_name, reviewed_flag,
             source_address, source_name, title, total_amount) = row
            
            rid = ch_response_id if ch_response_id else hashlib.md5(f"{filename}{date_recv}".encode()).hexdigest()
            
            try:
                pg_cur.execute("""
                    INSERT INTO tebra.fin_era_report (
                        era_report_id, file_name, received_date, payer_name, payer_id,
                        check_number, check_date, total_paid, payment_method, practice_guid,
                        denied_count, rejected_count, claim_count_source,
                        customer_id, clearinghouse_response_id, report_type_id, report_type_name,
                        source_type_id, source_type_name, payment_id, processed_flag,
                        response_type, response_type_name, reviewed_flag, source_address, title, total_amount
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (era_report_id) DO UPDATE
                    SET received_date = EXCLUDED.received_date,
                        payer_name = EXCLUDED.payer_name
                """, (
                    rid, filename, date_recv, source_name, '',
                    '', None, total_amount or 0, '', prac_guid,
                    denied_cnt or 0, rejected_cnt or 0, item_count or 0,
                    customer_id, ch_response_id, report_type_id, report_type_name,
                    source_type_id, source_type_name, payment_id, processed_flag,
                    response_type, response_type_name, reviewed_flag, source_address, title, total_amount
                ))
                inserted += 1
            except Exception as e:
                print(f"  Error: {e}")
        
        pg_conn.commit()
        print(f"  Inserted/Updated {inserted} records")
        total_inserted += inserted
    
    print(f"\n=== TOTAL: Inserted/Updated {total_inserted} records ===")
    
    sf_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    upsert_inactive_practices()
