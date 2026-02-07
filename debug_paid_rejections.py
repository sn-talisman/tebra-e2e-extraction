import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'tebra-ux/backend'))

from app.db.connection import get_db_cursor

async def inspect_paid_rejections():
    print("Searching for Paid claims that might be flagged as Rejected...")
    
    with get_db_cursor() as cur:
        # Find claims with Paid > 0 but 'Rejected' in status
        cur.execute("""
            SELECT 
                cl.tebra_claim_id, 
                cl.paid_amount, 
                cl.claim_status, 
                cl.payer_status
            FROM tebra.fin_claim_line cl
            WHERE cl.paid_amount > 0 
            AND (cl.claim_status ILIKE '%Rejected%' OR cl.payer_status ILIKE '%Rejected%')
            LIMIT 10
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("No paid claims found with 'Rejected' in status.")
            # Let's check for 'Denied' as well since I applied similar logic
            cur.execute("""
                SELECT 
                    cl.tebra_claim_id, 
                    cl.paid_amount, 
                    cl.claim_status, 
                    cl.payer_status
                FROM tebra.fin_claim_line cl
                WHERE cl.paid_amount > 0 
                AND (cl.claim_status ILIKE '%Denied%' OR cl.payer_status ILIKE '%Denied%')
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                print("Found Paid claims with 'Denied' in status:")
            else:
                 print("No paid claims found with 'Denied' in status either.")

        else:
            print(f"Found {len(rows)} Paid claims with 'Rejected' in status:")
            
        for row in rows:
            print(f"Claim: {row[0]}")
            print(f"  Paid: ${row[1]}")
            print(f"  Claim Status: {row[2]}")
            print(f"  Payer Status: {row[3]}")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(inspect_paid_rejections())
