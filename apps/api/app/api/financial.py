from fastapi import APIRouter
from app.db.connection import get_db_cursor

router = APIRouter()

@router.get("/summary")
async def get_financial_summary():
    """Get financial summary metrics"""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                COALESCE(SUM(billed_amount), 0) as total_billed,
                COALESCE(SUM(paid_amount), 0) as total_paid
            FROM tebra.fin_claim_line
        """)
        
        row = cur.fetchone()
        total_billed = float(row[0] or 0)
        total_paid = float(row[1] or 0)
        outstanding = total_billed - total_paid
        collection_rate = (total_paid / total_billed * 100) if total_billed > 0 else 0
        
        return {
            "totalBilled": round(total_billed, 2),
            "totalPaid": round(total_paid, 2),
            "outstanding": round(outstanding, 2),
            "collectionRate": round(collection_rate, 2)
        }
