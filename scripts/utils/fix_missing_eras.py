"""
Script to upsert missing ERA reports directly from Snowflake to Postgres.
These are 4 practices that had only non-ERA records (no ERA-type files).
"""
import psycopg2
from src.connection import get_connection
import hashlib

# Missing practices
MISSING_PRACTICES = [
    ('F003DC4E-DD5E-4A0F-92BD-5A4A3D563D39', 'DENICE MATEO-DELHALL LMSW'),
    ('5BF08C9F-352F-4914-9CB8-705481C80258', 'Family & Lifestyle Medicine'),
    ('1D32FD5B-6B9C-4422-90A0-51E3DF84CE72', 'Premier Pediatrics of Connecticut'),
    ('6512F562-5786-43C0-B38F-67F8152F0235', 'SALT AND LIGHT WELLNESS PLLC'),
]

def upsert_missing_eras():
    # Connect to Snowflake
    sf_conn = get_connection()
    sf_cur = sf_conn.cursor()
    
    # Connect to Postgres
    pg_conn = psycopg2.connect(
        host='localhost', 
        database='tebra_dw', 
        user='tebra_user', 
        password='tebra_password'
    )
    pg_cur = pg_conn.cursor()
    
    total_inserted = 0
    
    for guid, name in MISSING_PRACTICES:
        print(f"\n=== Processing {name} ({guid}) ===")
        
        # Query all columns from Snowflake
        sf_cur.execute(f"""
            SELECT 
                CUSTOMERID,
                CLEARINGHOUSERESPONSEID,
                CLEARINGHOUSERESPONSEREPORTTYPEID,
                CLEARINGHOUSERESPONSEREPORTTYPENAME,
                CLEARINGHOUSERESPONSESOURCETYPEID,
                CLEARINGHOUSERESPONSESOURCETYPENAME,
                DENIED,
                FILENAME,
                FILERECEIVEDATE,
                ITEMCOUNT,
                PAYMENTID,
                PRACTICEGUID,
                PROCESSEDFLAG,
                REJECTED,
                RESPONSETYPE,
                CLEARINGHOUSERESPONSETYPENAME,
                REVIEWEDFLAG,
                SOURCEADDRESS,
                SOURCENAME,
                TITLE,
                TOTALAMOUNT
            FROM PM_CLEARINGHOUSERESPONSE 
            WHERE PRACTICEGUID = '{guid}'
              AND FILERECEIVEDATE >= '2025-08-08'
            ORDER BY FILERECEIVEDATE DESC
        """)
        
        rows = sf_cur.fetchall()
        print(f"  Found {len(rows)} records in Snowflake")
        
        inserted = 0
        for row in rows:
            (customer_id, ch_response_id, report_type_id, report_type_name,
             source_type_id, source_type_name, denied_cnt, filename,
             date_recv, item_count, payment_id, prac_guid, processed_flag,
             rejected_cnt, response_type, response_type_name, reviewed_flag,
             source_address, source_name, title, total_amount) = row
            
            # Generate ID
            rid = ch_response_id if ch_response_id else hashlib.md5(f"{filename}{date_recv}".encode()).hexdigest()
            
            # Upsert to Postgres
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
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (era_report_id) DO UPDATE
                    SET received_date = EXCLUDED.received_date,
                        payer_name = EXCLUDED.payer_name,
                        denied_count = EXCLUDED.denied_count,
                        rejected_count = EXCLUDED.rejected_count,
                        claim_count_source = EXCLUDED.claim_count_source
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
                print(f"  Error inserting {filename}: {e}")
        
        pg_conn.commit()
        print(f"  Inserted/Updated {inserted} records")
        total_inserted += inserted
    
    print(f"\n=== TOTAL: Inserted/Updated {total_inserted} records ===")
    
    sf_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    upsert_missing_eras()
