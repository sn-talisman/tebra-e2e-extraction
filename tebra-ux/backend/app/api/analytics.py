from fastapi import APIRouter, HTTPException, Query
from app.db.connection import get_db_cursor
from typing import List, Optional

router = APIRouter()
import requests
import json

AI_SERVICE_URL = "http://localhost:8001"

import logging
logging.basicConfig(filename='backend_debug.log', level=logging.INFO, format='%(asctime)s %(message)s')

def log_ai_request(endpoint, practice_guid, ai_guid, status):
    logging.info(f"Endpoint: {endpoint} | Practice: {practice_guid} | AI GUID: {ai_guid} | Status: {status}")

def _resolve_ai_practice_guid(db_guid: str, cursor) -> Optional[str]:
    """
    The AI Service (port 8001) uses the same UUIDs as the local database.
    We simply verify the practice exists locally before forwarding.
    """
    try:
        # Verify practice exists locally
        cursor.execute("SELECT 1 FROM tebra.cmn_practice WHERE practice_guid = %s", (db_guid,))
        if cursor.fetchone():
            return db_guid
        return None
    except Exception as e:
        print(f"Error checking practice GUID: {e}")
        return None

@router.get("/practices")
def get_practice_analytics(days_back: int = 90):
    """
    Get analytics metrics per practice.
    """
    with get_db_cursor() as cur:
        # Aggregate metrics from clean claims
        sql = """
            SELECT 
                p.practice_guid,
                COALESCE(p.name, 'Unknown Practice') as practice_name,
                COUNT(cl.tebra_claim_id) as total_claims,
                
                -- Denied Billed Amount
                SUM(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN cl.billed_amount 
                    ELSE 0 
                END) as denied_billed,
                
                -- Denied Count
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN 1 
                    ELSE NULL 
                END) as denied_count
                
            FROM tebra.fin_claim_line cl
            -- Optimizing join: Use claim line's practice_guid directly
            JOIN tebra.cmn_practice p ON cl.practice_guid = p.practice_guid
            -- Still need report for date filtering
            JOIN tebra.fin_era_bundle b ON cl.claim_reference_id = b.claim_reference_id
            JOIN tebra.fin_era_report r ON b.era_report_id = r.era_report_id
            WHERE r.received_date >= CURRENT_DATE - (CAST(%s AS INTEGER) * INTERVAL '1 day')
            GROUP BY p.practice_guid, p.name
        """
        
        cur.execute(sql, (days_back,))
        rows = cur.fetchall()
        
        result = []
        for row in rows:
            total = row[2]
            denied_amt = float(row[3] or 0)
            denied_cnt = row[4]
            denial_rate = (denied_cnt / total) if total > 0 else 0
            
            result.append({
                "practice_id": str(row[0]),
                "practice_name": row[1],
                "total_claims": total,
                "denied_billed": denied_amt,
                "denial_rate": denial_rate
            })
            
        return result

@router.get("/payers")
def get_payer_analytics(days_back: int = 90):
    """
    Get analytics metrics per payer.
    """
    with get_db_cursor() as cur:
        sql = """
            SELECT 
                r.payer_name,
                COUNT(cl.tebra_claim_id) as total_claims,
                
                -- Denied Billed
                SUM(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN cl.billed_amount 
                    ELSE 0 
                END) as denied_billed,
                
                -- Denied Count
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN 1 
                    ELSE NULL 
                END) as denied_count
                
            FROM tebra.fin_claim_line cl
            JOIN tebra.fin_era_bundle b ON cl.claim_reference_id = b.claim_reference_id
            JOIN tebra.fin_era_report r ON b.era_report_id = r.era_report_id
            WHERE r.received_date >= CURRENT_DATE - (CAST(%s AS INTEGER) * INTERVAL '1 day')
            GROUP BY r.payer_name
            ORDER BY denied_count DESC
            LIMIT 20
        """
        
        cur.execute(sql, (days_back,))
        rows = cur.fetchall()
        
        result = []
        for row in rows:
            payer = row[0]
            total = row[1]
            denied_amt = float(row[2] or 0)
            denied_cnt = row[3]
            denial_rate = (denied_cnt / total) if total > 0 else 0
            
            result.append({
                "payer_name": payer,
                "total_claims": total,
                "denied_billed": denied_amt,
                "denial_rate": denial_rate
            })
            
        return result

@router.get("/global/performance-summary")
def get_global_performance_summary(days_back: int = 90):
    with get_db_cursor() as cur:
        sql = """
            SELECT 
                COUNT(cl.tebra_claim_id) as total_claims,
                
                -- Denied Billed Amount
                SUM(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN cl.billed_amount 
                    ELSE 0 
                END) as denied_billed,
                
                -- Denied Count
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN 1 
                    ELSE NULL 
                END) as denied_count,
                 
                -- High Risk (e.g. > $1000 and denied)
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 1000
                    THEN 1 
                    ELSE NULL 
                END) as high_risk_count,

                -- Total Billed
                SUM(cl.billed_amount) as total_billed,

                -- Total Paid
                SUM(cl.paid_amount) as total_paid
                
            FROM tebra.fin_claim_line cl
            WHERE EXISTS (
                  SELECT 1 
                  FROM tebra.fin_era_bundle b
                  JOIN tebra.fin_era_report r ON b.era_report_id = r.era_report_id
                  WHERE b.claim_reference_id = cl.claim_reference_id
                  AND r.received_date >= CURRENT_DATE - (CAST(%s AS INTEGER) * INTERVAL '1 day')
              )
        """
        
        cur.execute(sql, (days_back,))
        row = cur.fetchone()
        
        total = row[0] or 0
        denied_amt = float(row[1] or 0)
        denied_cnt = row[2] or 0
        high_risk = row[3] or 0
        total_billed = float(row[4] or 0)
        total_paid = float(row[5] or 0)
        
        denial_rate = (denied_cnt / total) if total > 0 else 0
        
        return {
            "practice_name": "All Practices (Executive Summary)",
            "total_claims": total,
            "total_billed": total_billed,
            "total_paid": total_paid,
            "denial_rate": denial_rate,
            "denial_rate_vs_overall": 0.0, # N/A for global
            "denied_amount": denied_amt,
            "recovery_potential": denied_amt * 0.8,
            "high_risk_claims": high_risk,
            "high_risk_pct": (high_risk / total) if total > 0 else 0
        }

@router.get("/global/payer-performance")
def get_global_payer_performance(days_back: int = 90):
    with get_db_cursor() as cur:
        sql = """
            SELECT 
                r.payer_name,
                COUNT(cl.tebra_claim_id) as total_claims,
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN 1 
                    ELSE NULL 
                END) as denied_count,
                SUM(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN cl.billed_amount 
                    ELSE 0 
                END) as denied_billed
            FROM tebra.fin_claim_line cl
            JOIN tebra.fin_era_bundle b ON cl.claim_reference_id = b.claim_reference_id
            JOIN tebra.fin_era_report r ON b.era_report_id = r.era_report_id
            WHERE r.received_date >= CURRENT_DATE - (CAST(%s AS INTEGER) * INTERVAL '1 day')
            GROUP BY r.payer_name
            ORDER BY denied_billed DESC
            LIMIT 10
        """
        cur.execute(sql, (days_back,))
        rows = cur.fetchall()
        
        return [
            {
                "name": row[0],
                "total_claims": row[1],
                "denied_count": row[2],
                "denied_amount": float(row[3] or 0),
                "rate": round((row[2]/row[1]*100), 1) if row[1] > 0 else 0
            }
            for row in rows
        ]

@router.get("/global/cpt-performance")
def get_global_cpt_performance(days_back: int = 90):
    with get_db_cursor() as cur:
        sql = """
            SELECT 
                cl.proc_code,
                cl.description,
                COUNT(cl.tebra_claim_id) as total_claims,
                SUM(cl.billed_amount) as total_billed,
                
                -- Denied Count
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN 1 
                    ELSE NULL 
                END) as denied_count,

                -- Denied Amount
                 SUM(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN cl.billed_amount 
                    ELSE 0 
                END) as denied_billed

            FROM tebra.fin_claim_line cl
            JOIN tebra.fin_era_bundle b ON cl.claim_reference_id = b.claim_reference_id
            JOIN tebra.fin_era_report r ON b.era_report_id = r.era_report_id
            WHERE r.received_date >= CURRENT_DATE - (CAST(%s AS INTEGER) * INTERVAL '1 day')
            GROUP BY cl.proc_code, cl.description
            ORDER BY denied_billed DESC
            LIMIT 10
        """
        cur.execute(sql, (days_back,))
        rows = cur.fetchall()
        
        return [
            {
                "code": row[0],
                "description": row[1],
                "volume": row[2],
                "value": float(row[3] or 0),
                "denied_amount": float(row[5] or 0),
                "denial_rate": (row[4] / row[2]) if row[2] > 0 else 0
            }
            for row in rows
        ]

@router.get("/global/action-items")
def get_global_action_items(days_back: int = 90):
    # For global, we can generate action items based on the top denied payers/CPTs
    payers = get_global_payer_performance(days_back)
    cpts = get_global_cpt_performance(days_back)
    
    actions = []
    
    # Top Payer Action
    if payers:
        top_payer = payers[0]
        if top_payer['denied_amount'] > 0:
            actions.append({
                "priority": "HIGH",
                "title": f"Address High Denials with {top_payer['name']}",
                "financial_impact": top_payer['denied_amount'],
                "recommendation": f"Global issue: {top_payer['name']} has denied ${top_payer['denied_amount']:,.0f} across all practices. Review payer contracts and billing policies.",
                "suggested_next_steps": [
                    f"Audit top 20 denied claims for {top_payer['name']}.",
                    "Verify if recent policy changes affect this payer.",
                    "Check for common denial reason codes (e.g., CO-16, CO-18).",
                    "Contact provider representative if improved documentation is needed."
                ]
            })
            
    # Top CPT Action
    if cpts:
        top_cpt = cpts[0]
        if top_cpt['denied_amount'] > 0:
             actions.append({
                "priority": "MEDIUM",
                "title": f"Review Coding for CPT {top_cpt['code']}",
                "financial_impact": top_cpt['denied_amount'],
                "recommendation": f"Procedure code {top_cpt['code']} ({top_cpt['description'][:30]}...) has a high denial rate. Audit coding compliance globally.",
                "suggested_next_steps": [
                    f"Review clinical documentation for CPT {top_cpt['code']}.",
                    "Ensure modifiers (e.g., -25, -59) are applied correctly.",
                    "Check National Correct Coding Initiative (NCCI) edits.",
                    "Educate coding staff on specific requirements for this procedure."
                ]
            })
            
    return {"action_items": actions}


@router.get("/practice/{practice_guid}/performance-summary")
def get_practice_summary(practice_guid: str, days_back: int = 90):
    with get_db_cursor() as cur:
        # Try to get data from AI Service first
        try:
            ai_guid = _resolve_ai_practice_guid(practice_guid, cur)
            if ai_guid:
                resp = requests.get(f"{AI_SERVICE_URL}/api/v1/analytics/practice/{ai_guid}/performance-summary?days_back={days_back}")
                log_ai_request("summary", practice_guid, ai_guid, resp.status_code)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(f"AI Service Fallback Error: {e}")
            # Continue to SQL fallback

        # Get Practice Name
        cur.execute("SELECT name FROM tebra.cmn_practice WHERE practice_guid = %s", (practice_guid,))
        p_row = cur.fetchone()
        p_name = p_row[0] if p_row else "Unknown Practice"
        
        # Get Metrics
        sql = """
            SELECT 
                COUNT(cl.tebra_claim_id) as total_claims,
                
                -- Denied Billed Amount
                SUM(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN cl.billed_amount 
                    ELSE 0 
                END) as denied_billed,
                
                -- Denied Count
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN 1 
                    ELSE NULL 
                END) as denied_count,
                 
                -- High Risk (e.g. > $1000 and denied)
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 1000
                    THEN 1 
                    ELSE NULL 
                END) as high_risk_count
                
            FROM tebra.fin_claim_line cl
            -- Direct link to practice for filtering
            WHERE cl.practice_guid = %s
              -- Ensure date filtering uses report received date by joining safely if needed
              -- Or checking claim date if close enough? No, requirements say Report date usually.
              -- Let's stick to ERA Report Date for consistency with other metrics
              AND EXISTS (
                  SELECT 1 
                  FROM tebra.fin_era_bundle b
                  JOIN tebra.fin_era_report r ON b.era_report_id = r.era_report_id
                  WHERE b.claim_reference_id = cl.claim_reference_id
                  AND r.received_date >= CURRENT_DATE - (CAST(%s AS INTEGER) * INTERVAL '1 day')
              )
        """
        
        cur.execute(sql, (practice_guid, days_back))
        row = cur.fetchone()
        
        total = row[0] or 0
        denied_amt = float(row[1] or 0)
        denied_cnt = row[2] or 0
        high_risk = row[3] or 0
        
        denial_rate = (denied_cnt / total) if total > 0 else 0
        
        return {
            "practice_name": p_name,
            "denial_rate": denial_rate,
            "denial_rate_vs_overall": 0.15, # Mock benchmark
            "denied_amount": denied_amt,
            "recovery_potential": denied_amt * 0.8, # Mock 80% recovery
            "high_risk_claims": high_risk,
            "high_risk_pct": (high_risk / total) if total > 0 else 0
        }

@router.get("/practice/{practice_guid}/action-items")
def get_action_items(practice_guid: str):
    # Mock Action Items based on simple logic
    return [
        {
            "priority": "HIGH",
            "title": "Review High Value Denials",
            "financial_impact": 15000,
            "recommendation": "Focus on 5 claims over $1000 denied for Medical Necessity."
        },
        {
            "priority": "MEDIUM",
            "title": "Credentialing Update",
            "financial_impact": 5000,
            "recommendation": "Update NPI for Dr. Smith with UHC."
        }
    ]

@router.get("/practice/{practice_guid}/payer-performance")
def get_practice_payer_performance(practice_guid: str, days_back: int = 90):
    with get_db_cursor() as cur:
        sql = """
            SELECT 
                r.payer_name,
                COUNT(cl.tebra_claim_id) as total_claims,
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                    THEN 1 
                    ELSE NULL 
                END) as denied_count
            FROM tebra.fin_claim_line cl
            JOIN tebra.fin_era_bundle b ON cl.claim_reference_id = b.claim_reference_id
            JOIN tebra.fin_era_report r ON b.era_report_id = r.era_report_id
            WHERE cl.practice_guid = %s
              AND r.received_date >= CURRENT_DATE - (CAST(%s AS INTEGER) * INTERVAL '1 day')
            GROUP BY r.payer_name
            ORDER BY denied_count DESC
            LIMIT 10
        """
        cur.execute(sql, (practice_guid, days_back))
        rows = cur.fetchall()
        
        return [
            {
                "name": row[0],
                "rate": round((row[2]/row[1]*100), 1) if row[1] > 0 else 0
            }
            for row in rows
        ]

@router.get("/practice/{practice_guid}/cpt-performance")
def get_practice_cpt_performance(practice_guid: str, days_back: int = 90):
    try:
        with get_db_cursor() as cur:
            sql = """
                SELECT 
                    cl.proc_code,
                    cl.description,
                    COUNT(cl.tebra_claim_id) as total_claims,
                    SUM(cl.billed_amount) as total_billed,
                    
                    -- Denied Count
                    COUNT(CASE 
                        WHEN cl.paid_amount = 0 AND cl.billed_amount > 0
                        THEN 1 
                        ELSE NULL 
                    END) as denied_count
                    
                FROM tebra.fin_claim_line cl
                JOIN tebra.fin_era_bundle b ON cl.claim_reference_id = b.claim_reference_id
                JOIN tebra.fin_era_report r ON b.era_report_id = r.era_report_id
                WHERE cl.practice_guid = %s
                  AND r.received_date >= CURRENT_DATE - (CAST(%s AS INTEGER) * INTERVAL '1 day')
                GROUP BY cl.proc_code, cl.description
                ORDER BY total_claims DESC
                LIMIT 10
            """
            cur.execute(sql, (practice_guid, days_back))
            rows = cur.fetchall()
            
            return [
                {
                    "code": row[0],
                    "description": row[1],
                    "volume": row[2],
                    "value": float(row[3] or 0),
                    "denial_rate": (row[4] / row[2]) if row[2] > 0 else 0
                }
                for row in rows
            ]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting CPT performance: {str(e)}")

@router.get("/practice/{practice_guid}/ai/summary")
def get_ai_performance_summary(practice_guid: str, days_back: int = 90):
    with get_db_cursor() as cur:
        ai_guid = _resolve_ai_practice_guid(practice_guid, cur)
        if not ai_guid:
            raise HTTPException(status_code=404, detail="AI data not found for this practice")
        
    try:
        resp = requests.get(f"{AI_SERVICE_URL}/api/v1/analytics/practice/{ai_guid}/performance-summary?days_back={days_back}")
        log_ai_request("summary", practice_guid, ai_guid, resp.status_code)
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail="AI Service Error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/practice/{practice_guid}/ai/actions")
def get_ai_action_items(practice_guid: str, days_back: int = 90):
    with get_db_cursor() as cur:
        ai_guid = _resolve_ai_practice_guid(practice_guid, cur)
        if not ai_guid:
            return {"action_items": []}
            
    try:
        resp = requests.get(f"{AI_SERVICE_URL}/api/v1/analytics/practice/{ai_guid}/action-items?days_back={days_back}")
        if resp.status_code == 200:
            return resp.json()
        return {"action_items": []}
    except Exception as e:
        print(f"AI Actions Error: {e}")
        return {"action_items": []}

@router.get("/practice/{practice_guid}/ai/denial-reasons")
def get_ai_denial_reasons(practice_guid: str, days_back: int = 90):
    with get_db_cursor() as cur:
        ai_guid = _resolve_ai_practice_guid(practice_guid, cur)
        if not ai_guid:
             return {"carc_codes": []}

    try:
        resp = requests.get(f"{AI_SERVICE_URL}/api/v1/analytics/practice/{ai_guid}/denial-reasons?days_back={days_back}")
        if resp.status_code == 200:
            return resp.json()
        return {"carc_codes": []}
    except Exception as e:
        return {"carc_codes": []}

@router.get("/practice/{practice_guid}/ai/high-risk")
def get_ai_high_risk(practice_guid: str, limit: int = 20):
    with get_db_cursor() as cur:
        ai_guid = _resolve_ai_practice_guid(practice_guid, cur)
        if not ai_guid:
            return {"high_risk_claims": []}

    try:
        resp = requests.get(f"{AI_SERVICE_URL}/api/v1/analytics/practice/{ai_guid}/high-risk-claims?days_back=90&limit={limit}")
        if resp.status_code == 200:
            return resp.json()
        return {"high_risk_claims": []}
    except Exception as e:
        return {"high_risk_claims": []}
