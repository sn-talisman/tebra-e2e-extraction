from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any

router = APIRouter()

DB_CONFIG = {
    "host": "localhost",
    "database": "tebra_dw",
    "user": "tebra_user",
    "password": "tebra_password"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@router.get("/practices/{practice_guid}/financial-metrics")
def get_financial_metrics(practice_guid: str):
    """
    Calculate and return financial metrics for a practice with benchmarking
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Resolve practice_guid to location_guids via Name Match (consistent with practices.py)
        # 1. Get Practice Name
        cur.execute("SELECT name FROM tebra.cmn_practice WHERE practice_guid::text = %s", (practice_guid,))
        practice_row = cur.fetchone()
        
        if not practice_row:
            raise HTTPException(status_code=404, detail="Practice not found")
            
        practice_name = practice_row['name']
        
        # 2. Get Associated Location GUIDs
        cur.execute("SELECT location_guid FROM tebra.cmn_location WHERE name = %s", (practice_name,))
        loc_rows = cur.fetchall()
        loc_guids = [str(row['location_guid']) for row in loc_rows]
        
        if not loc_guids:
            # Fallback: if no locations found by name, try using the practice_guid itself 
            # (though unlikely based on our findings, good for safety)
            loc_guids = [practice_guid]

        # Calculate metrics using the list of location GUIDs
        metrics = calculate_practice_metrics(cur, loc_guids)
        
        # Get comparison data (all practices) - Placeholder
        all_practices_metrics = calculate_all_practices_averages(cur)
        
        # Calculate percentile rank - Placeholder
        percentile_rank = calculate_percentile_rank(cur, loc_guids, metrics)
        
        # Get historical trends (last 6 months)
        trends = calculate_historical_trends(cur, loc_guids)
        
        return {
            "practice": {
                "guid": practice_guid,
                "name": practice_name
            },
            "metrics": metrics,
            "comparisons": {
                "allPractices": all_practices_metrics,
                "percentileRank": percentile_rank
            },
            "trends": trends,
            "industryBenchmarks": {
                "daysInAR": {"excellent": 32, "good": 40, "warning": 50, "critical": 60},
                "netCollectionRate": {"excellent": 97, "good": 96, "warning": 94, "critical": 90},
                "patientCollectionRate": {"excellent": 92, "good": 90, "warning": 85, "critical": 80},
                "denialRate": {"excellent": 3, "good": 5, "warning": 8, "critical": 10},
                "arOver120Days": {"excellent": 10, "good": 15, "warning": 20, "critical": 25}
            }
        }
    
    finally:
        cur.close()
        conn.close()

def calculate_practice_metrics(cur, loc_guids: List[str]) -> Dict[str, Any]:
    """Calculate all financial metrics for a practice"""
    
    # Date range: last 90 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # 1. Days in AR
    days_in_ar = calculate_days_in_ar(cur, loc_guids, start_date, end_date)
    
    # 2. Net Collection Rate
    net_collection_rate = calculate_net_collection_rate(cur, loc_guids, start_date, end_date)
    
    # 3. Patient Collection Rate
    patient_collection_rate = calculate_patient_collection_rate(cur, loc_guids, start_date, end_date)
    
    # 4. Denial Rate
    denial_rate = calculate_denial_rate(cur, loc_guids, start_date, end_date)
    
    # 5. AR Over 120 Days
    ar_over_120 = calculate_ar_over_120(cur, loc_guids)
    
    # Get previous period for trend calculation
    prev_start_date = start_date - timedelta(days=90)
    prev_days_in_ar = calculate_days_in_ar(cur, loc_guids, prev_start_date, start_date)
    prev_ncr = calculate_net_collection_rate(cur, loc_guids, prev_start_date, start_date)
    prev_denial = calculate_denial_rate(cur, loc_guids, prev_start_date, start_date)
    
    return {
        "daysInAR": {
            "value": round(days_in_ar, 1),
            "trend": round(days_in_ar - prev_days_in_ar, 1),
            "performance": get_performance_level(days_in_ar, 32, 40, 50, inverse=True)
        },
        "netCollectionRate": {
            "value": round(net_collection_rate, 1),
            "trend": round(net_collection_rate - prev_ncr, 1),
            "performance": get_performance_level(net_collection_rate, 97, 96, 94)
        },
        "patientCollectionRate": {
            "value": patient_collection_rate if patient_collection_rate is not None else None,
            "trend": None,  # No history yet
            "performance": get_performance_level(patient_collection_rate, 92, 90, 85) if patient_collection_rate is not None else None
        },
        "denialRate": {
            "value": round(denial_rate, 1),
            "trend": round(denial_rate - prev_denial, 1),
            "performance": get_performance_level(denial_rate, 3, 5, 8, inverse=True)
        },
        "arOver120Days": {
            "value": round(ar_over_120, 1),
            "trend": None,  # No history yet
            "performance": get_performance_level(ar_over_120, 10, 15, 20, inverse=True)
        }
    }

def calculate_days_in_ar(cur, loc_guids: List[str], start_date: datetime, end_date: datetime) -> float:
    """Calculate Days in Accounts Receivable"""
    
    # Total AR (unpaid or partially paid claims)
    cur.execute("""
        SELECT 
            SUM(fcl.billed_amount - COALESCE(fcl.paid_amount, 0)) as total_ar,
            COUNT(DISTINCT fcl.tebra_claim_id) as claim_count
        FROM tebra.fin_claim_line fcl
        JOIN tebra.clin_encounter enc ON fcl.encounter_id = enc.encounter_id
        WHERE enc.location_guid = ANY(%s::uuid[])
        AND fcl.date_of_service BETWEEN %s AND %s
        AND (fcl.paid_amount IS NULL OR fcl.paid_amount < fcl.billed_amount)
    """, (loc_guids, start_date, end_date))
    
    ar_data = cur.fetchone()
    total_ar = float(ar_data['total_ar'] or 0)
    
    # Average daily charges
    cur.execute("""
        SELECT 
            SUM(fcl.billed_amount) as total_charges,
            COUNT(DISTINCT DATE(fcl.date_of_service)) as days_count
        FROM tebra.fin_claim_line fcl
        JOIN tebra.clin_encounter enc ON fcl.encounter_id = enc.encounter_id
        WHERE enc.location_guid = ANY(%s::uuid[])
        AND fcl.date_of_service BETWEEN %s AND %s
    """, (loc_guids, start_date, end_date))
    
    charges_data = cur.fetchone()
    total_charges = float(charges_data['total_charges'] or 0)
    days_count = int(charges_data['days_count'] or 1)
    
    if days_count == 0 or total_charges == 0:
        return 0
    
    avg_daily_charges = total_charges / days_count
    
    if avg_daily_charges == 0:
        return 0
    
    return total_ar / avg_daily_charges

def calculate_net_collection_rate(cur, loc_guids: List[str], start_date: datetime, end_date: datetime) -> float:
    """Calculate Net Collection Rate (NCR)"""
    
    cur.execute("""
        SELECT 
            SUM(fcl.paid_amount) as total_payments,
            SUM(fcl.billed_amount) as total_charges
        FROM tebra.fin_claim_line fcl
        JOIN tebra.clin_encounter enc ON fcl.encounter_id = enc.encounter_id
        WHERE enc.location_guid = ANY(%s::uuid[])
        AND fcl.date_of_service BETWEEN %s AND %s
    """, (loc_guids, start_date, end_date))
    
    data = cur.fetchone()
    total_payments = float(data['total_payments'] or 0)
    total_charges = float(data['total_charges'] or 0)
    
    if total_charges == 0:
        return 0
    
    # NCR = (Payments / Charges) * 100
    return (total_payments / total_charges) * 100

def calculate_patient_collection_rate(cur, loc_guids: List[str], start_date: datetime, end_date: datetime) -> float:
    """Calculate Patient Responsibility Collection Rate"""
    
    cur.execute("""
        SELECT 
            SUM(era.total_patient_resp) as total_patient_resp,
            COUNT(*) as claim_count
        FROM tebra.fin_era_bundle era
        JOIN tebra.fin_claim_line fcl ON era.claim_reference_id = fcl.claim_reference_id
        JOIN tebra.clin_encounter enc ON fcl.encounter_id = enc.encounter_id
        WHERE enc.location_guid = ANY(%s::uuid[])
        AND fcl.date_of_service BETWEEN %s AND %s
        AND era.total_patient_resp > 0
    """, (loc_guids, start_date, end_date))
    
    data = cur.fetchone()
    total_patient_resp = float(data['total_patient_resp'] or 0)
    
    if total_patient_resp == 0:
        return None  # No data to calculate rate
    
    # Simplified: assume 90% collection rate as baseline
    # In real scenario, would track actual patient payments
    return None

def calculate_denial_rate(cur, loc_guids: List[str], start_date: datetime, end_date: datetime) -> float:
    """Calculate Denial Rate"""
    
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN fcl.paid_amount = 0 AND fcl.adjustments_json IS NOT NULL THEN 1 END) as denied_claims,
            COUNT(*) as total_claims
        FROM tebra.fin_claim_line fcl
        JOIN tebra.clin_encounter enc ON fcl.encounter_id = enc.encounter_id
        WHERE enc.location_guid = ANY(%s::uuid[])
        AND fcl.date_of_service BETWEEN %s AND %s
    """, (loc_guids, start_date, end_date))
    
    data = cur.fetchone()
    denied_claims = int(data['denied_claims'] or 0)
    total_claims = int(data['total_claims'] or 1)
    
    if total_claims == 0:
        return 0
    
    return (denied_claims / total_claims) * 100

def calculate_ar_over_120(cur, loc_guids: List[str]) -> float:
    """Calculate percentage of AR over 120 days old"""
    
    cutoff_date = datetime.now() - timedelta(days=120)
    
    cur.execute("""
        SELECT 
            SUM(CASE WHEN fcl.date_of_service < %s THEN fcl.billed_amount - COALESCE(fcl.paid_amount, 0) ELSE 0 END) as old_ar,
            SUM(fcl.billed_amount - COALESCE(fcl.paid_amount, 0)) as total_ar
        FROM tebra.fin_claim_line fcl
        JOIN tebra.clin_encounter enc ON fcl.encounter_id = enc.encounter_id
        WHERE enc.location_guid = ANY(%s::uuid[])
        AND (fcl.paid_amount IS NULL OR fcl.paid_amount < fcl.billed_amount)
    """, (cutoff_date, loc_guids))
    
    data = cur.fetchone()
    old_ar = float(data['old_ar'] or 0)
    total_ar = float(data['total_ar'] or 1)
    
    if total_ar == 0:
        return 0
    
    return (old_ar / total_ar) * 100

def calculate_all_practices_averages(cur) -> Dict[str, float]:
    """Calculate average metrics across all practices (Network Average)"""
    
    # 1. Get all practice GUIDs
    cur.execute("SELECT practice_guid FROM tebra.cmn_practice")
    all_practice_guids = [str(row['practice_guid']) for row in cur.fetchall()]
    
    if not all_practice_guids:
        return {
            "avgDaysInAR": 0,
            "avgNCR": 0,
            "avgDenialRate": 0,
            "avgPatientCollectionRate": 0,
            "avgAROver120": 0
        }

    # 2. Get all location GUIDs associated with these practices (to match how individual metrics are calculated)
    cur.execute("SELECT DISTINCT location_guid FROM tebra.cmn_location")
    all_loc_guids = [str(row['location_guid']) for row in cur.fetchall()]
    
    if not all_loc_guids:
        return {
            "avgDaysInAR": 0,
            "avgNCR": 0,
            "avgDenialRate": 0,
            "avgPatientCollectionRate": 0,
            "avgAROver120": 0
        }

    # Date range: last 90 days (consistent with practice metrics)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # Calculate global metrics
    avg_days_in_ar = calculate_days_in_ar(cur, all_loc_guids, start_date, end_date)
    avg_ncr = calculate_net_collection_rate(cur, all_loc_guids, start_date, end_date)
    avg_denial = calculate_denial_rate(cur, all_loc_guids, start_date, end_date)
    avg_ar_over_120 = calculate_ar_over_120(cur, all_loc_guids)
    
    return {
        "avgDaysInAR": round(avg_days_in_ar, 1),
        "avgNCR": round(avg_ncr, 1),
        "avgDenialRate": round(avg_denial, 1),
        "avgPatientCollectionRate": None, # Future implementation
        "avgAROver120": round(avg_ar_over_120, 1)
    }

def calculate_percentile_rank(cur, loc_guids: List[str], current_metrics: Dict) -> int:
    """Calculate percentile rank for Days in A/R among all practices"""
    
    # Date range: last 90 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # 1. Get all practices and their names
    cur.execute("SELECT practice_guid, name FROM tebra.cmn_practice")
    practices = cur.fetchall()
    
    practice_metrics = []
    current_value = current_metrics["daysInAR"]["value"]
    
    for p in practices:
        p_guid = str(p['practice_guid'])
        p_name = p['name']
        
        # Get location guids for this practice (by name match, as per our pattern)
        cur.execute("SELECT location_guid FROM tebra.cmn_location WHERE name = %s", (p_name,))
        p_loc_rows = cur.fetchall()
        p_loc_guids = [str(row['location_guid']) for row in p_loc_rows]
        
        if not p_loc_guids:
            p_loc_guids = [p_guid]
            
        val = calculate_days_in_ar(cur, p_loc_guids, start_date, end_date)
        if val > 0:
            practice_metrics.append(val)
            
    if not practice_metrics:
        return 50 # Neutral default
        
    # Days in AR: Lower is better, so we rank descending (better performance = lower value)
    # We want to know what % of practices have a WORSE (higher) Days in AR than us.
    practice_metrics.sort() # [low, ..., high]
    
    # Count how many practices have a HIGHER Days in AR than us (meaning they are worse)
    worse_than_us = [v for v in practice_metrics if v > current_value]
    
    rank = (len(worse_than_us) / len(practice_metrics)) * 100
    return int(rank)

def calculate_historical_trends(cur, loc_guids: List[str]) -> List[Dict]:
    """Calculate monthly trends for the last 6 months"""
    
    # Get all network location GUIDs for benchmarking
    cur.execute("SELECT DISTINCT location_guid FROM tebra.cmn_location")
    all_loc_guids = [str(row['location_guid']) for row in cur.fetchall()]
    
    trends = []
    for i in range(5, -1, -1):
        month_start = datetime.now() - timedelta(days=30 * (i + 1))
        month_end = datetime.now() - timedelta(days=30 * i)
        
        days_in_ar = calculate_days_in_ar(cur, loc_guids, month_start, month_end)
        ncr = calculate_net_collection_rate(cur, loc_guids, month_start, month_end)
        denial_rate = calculate_denial_rate(cur, loc_guids, month_start, month_end)
        
        # Benchmarks
        network_ncr = calculate_net_collection_rate(cur, all_loc_guids, month_start, month_end)
        
        trends.append({
            "month": month_end.strftime("%Y-%m"),
            "daysInAR": round(days_in_ar, 1),
            "ncr": round(ncr, 1),
            "denialRate": round(denial_rate, 1),
            "networkAvgNCR": round(network_ncr, 1),
            "industryAvgNCR": 96.0
        })
    
    return trends

def get_performance_level(value: float, excellent: float, good: float, warning: float, inverse: bool = False) -> str:
    """Determine performance level based on thresholds"""
    
    if inverse:
        # Lower is better (e.g., Days in AR, Denial Rate)
        if value <= excellent:
            return "excellent"
        elif value <= good:
            return "good"
        elif value <= warning:
            return "warning"
        else:
            return "critical"
    else:
        # Higher is better (e.g., Collection Rates)
        if value >= excellent:
            return "excellent"
        elif value >= good:
            return "good"
        elif value >= warning:
            return "warning"
        else:
            return "critical"
