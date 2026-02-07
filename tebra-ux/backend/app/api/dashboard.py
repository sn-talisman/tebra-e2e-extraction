from fastapi import APIRouter
from app.db.connection import get_db_cursor

router = APIRouter()

@router.get("/metrics")
async def get_dashboard_metrics():
    """Get high-level dashboard metrics from tebra database"""
    with get_db_cursor() as cur:
        # Total Encounters
        cur.execute("SELECT COUNT(*) FROM tebra.clin_encounter")
        total_encounters = cur.fetchone()[0]
        
        # Total Claims (distinct claim IDs)
        cur.execute("SELECT COUNT(DISTINCT tebra_claim_id) FROM tebra.fin_claim_line")
        total_claims = cur.fetchone()[0]
        
        # Total Billed Amount
        cur.execute("SELECT COALESCE(SUM(billed_amount), 0) FROM tebra.fin_claim_line")
        total_billed = float(cur.fetchone()[0] or 0)
        
        # Total Paid Amount
        cur.execute("SELECT COALESCE(SUM(paid_amount), 0) FROM tebra.fin_claim_line")
        total_paid = float(cur.fetchone()[0] or 0)
        
        # Collection Rate
        collection_rate = (total_paid / total_billed * 100) if total_billed > 0 else 0
        
        # Practice Count (distinct locations)
        cur.execute("SELECT COUNT(*) FROM tebra.cmn_location")
        practice_count = cur.fetchone()[0]
        
        return {
            "totalEncounters": total_encounters,
            "totalClaims": total_claims,
            "totalBilled": round(total_billed, 2),
            "totalPaid": round(total_paid, 2),
            "collectionRate": round(collection_rate, 2),
            "practicesCount": practice_count
        }

@router.get("/recent-activity")
async def get_recent_activity():
    """Get recent encounter activity (last 30 days)"""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                DATE(start_date) as date,
                COUNT(*) as encounters
            FROM tebra.clin_encounter
            WHERE start_date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(start_date)
            ORDER BY date DESC
            LIMIT 30
        """)
        
        rows = cur.fetchall()
        return [
            {"date": str(row[0]), "count": row[1]}
            for row in rows
        ]
