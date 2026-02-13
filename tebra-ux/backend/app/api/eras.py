from fastapi import APIRouter, HTTPException, Query
from app.db.connection import get_db_cursor
from typing import List, Optional

router = APIRouter()

@router.get("/list")
async def get_era_reports(
    practice_guid: Optional[str] = None,
    page: int = 1, 
    page_size: int = 20,
    search: Optional[str] = None,
    sort_by: str = 'date',
    order: str = 'desc',
    hide_informational: bool = False,
    show_rejections: bool = False,
    show_denials: bool = False
):
    """
    Get list of ERA Reports (Checks).
    Aggregates metrics from fin_era_report including Practice Name and Denied counts.
    Supports pagination.
    """
    with get_db_cursor() as cur:
        # Base Query
        # Join fin_era_report -> cmn_practice via practice_guid (Direct Link)
        # Join fin_era_report -> fin_era_bundle -> fin_claim_line (For counts)
        
        offset = (page - 1) * page_size
        
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
                COALESCE(p.name, 'Unknown Practice') as practice_name,
                
                -- Source Metrics (Use Line Count if Source is 0 or less than calculated)
                GREATEST(
                    r.claim_count_source,
                    (SELECT COUNT(cl.tebra_claim_id) 
                     FROM tebra.fin_era_bundle b 
                     JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                     WHERE b.era_report_id = r.era_report_id)
                ) as claim_count,
                
                -- Calculated Status Counts (Only count if Paid Amount is 0)
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND (
                        (cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%')
                        OR (cl.billed_amount > 0)
                    )
                    THEN 1 
                    ELSE NULL 
                END) as denied_count,
                
                COUNT(CASE 
                    WHEN cl.paid_amount = 0 AND (cl.payer_status ILIKE '%%Rejected%%' OR cl.claim_status ILIKE '%%Rejected%%') 
                    THEN 1 
                    ELSE NULL 
                END) as rejected_count,

                -- Denial Reasons (Aggregate Distinct Codes)
                STRING_AGG(DISTINCT cl.adjustments_json, ', ') FILTER (WHERE cl.paid_amount = 0) as denial_reasons,

                'Processed' as status_display,

                -- ERA Type Logic
                CASE 
                    WHEN r.total_paid > 0 THEN 'Payment'
                    WHEN COUNT(CASE 
                        WHEN cl.paid_amount = 0 AND (
                            (cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%')
                            OR (cl.billed_amount > 0)
                        )
                        THEN 1 
                        ELSE NULL 
                    END) > 0 THEN 'Denial'
                    ELSE 'Informational'
                END as era_type
                
            FROM tebra.fin_era_report r
            LEFT JOIN tebra.cmn_practice p ON r.practice_guid = p.practice_guid
            LEFT JOIN tebra.fin_era_bundle b ON r.era_report_id = b.era_report_id
            LEFT JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
        """
        
        params = []
        where_clauses = []
        
        if practice_guid and practice_guid != 'All':
            where_clauses.append("r.practice_guid = %s")
            params.append(practice_guid)
            
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        # Search Logic
        if search:
            search_pattern = f"%{search}%"
            search_condition = """
                AND (
                    r.payer_name ILIKE %s OR 
                    r.era_report_id::text ILIKE %s OR 
                    r.check_number ILIKE %s OR
                    r.file_name ILIKE %s
                )
            """
            # Append to WHERE or start new WHERE
            if "WHERE" in sql:
                sql += search_condition
            else:
                sql += " WHERE " + search_condition.lstrip(" AND ")
            
            
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        
        sql += """
            GROUP BY r.era_report_id, r.received_date, r.payer_name, r.check_number, r.total_paid, r.payment_method, p.name
        """

        # HAVING Filters (Aggregated Counts / Calculated Types)
        having_clauses = []

        if hide_informational:
            # Hide Informational = Keep Payment OR Denial
            # Payment: total_paid > 0
            # Denial: denied_count > 0 OR rejected_count > 0 OR (billed > 0 AND paid = 0)
            # Re-using the logic from select list is hard, so we assume Informational is (Paid=0 AND No Denials)
            having_clauses.append("""
                (r.total_paid > 0 OR 
                 COUNT(CASE 
                    WHEN (cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%')
                      OR (cl.billed_amount > 0 AND cl.paid_amount = 0)
                    THEN 1 
                    ELSE NULL 
                 END) > 0 OR
                 COUNT(CASE 
                    WHEN cl.payer_status ILIKE '%%Rejected%%' OR cl.claim_status ILIKE '%%Rejected%%' THEN 1 
                    ELSE NULL 
                 END) > 0)
            """)

        # Rejection/Denial Filters (Additive: Show if Rejection OR Denial matches)
        status_or_clauses = []
        if show_rejections:
             status_or_clauses.append("COUNT(CASE WHEN cl.payer_status ILIKE '%%Rejected%%' OR cl.claim_status ILIKE '%%Rejected%%' THEN 1 ELSE NULL END) > 0")
        if show_denials:
             status_or_clauses.append("""
                 COUNT(CASE 
                    WHEN (cl.payer_status ILIKE '%%Denied%%' OR cl.claim_status ILIKE '%%Denied%%')
                      OR (cl.billed_amount > 0 AND cl.paid_amount = 0)
                    THEN 1 
                    ELSE NULL 
                 END) > 0
             """)
        
        if status_or_clauses:
            having_clauses.append(f"({' OR '.join(status_or_clauses)})")

        if having_clauses:
            sql += " HAVING " + " AND ".join(having_clauses)
        


        # Sorting Logic
        order_clause = "DESC" if order == 'desc' else "ASC"
        sort_map = {
            'id': 'r.era_report_id',
            'date': 'r.received_date',
            'payer': 'r.payer_name',
            'total_paid': 'total_paid', # Calculated column
            'claim_count': 'claim_count'
        }
        sort_col = sort_map.get(sort_by, 'r.received_date')
        
        sql += f" ORDER BY {sort_col} {order_clause}"
        
        # Pagination
        sql += """
            LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])
        
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "receivedDate": str(row[1]) if row[1] else "N/A",
                "payer": row[2] or "Unknown",
                "checkNumber": row[3] or "N/A",
                "totalPaid": float(row[4] or 0),
                "totalBilled": float(row[5] or 0),
                "practice": row[6],
                "claimCount": row[7],
                "deniedCount": row[8],
                "rejectedCount": row[9], 
                "denialReasons": row[10],
                "status": row[11],
                "type": row[12]
            })
            
        return result

@router.get("/{report_id}/details")
async def get_era_details(report_id: str):
    """
    Get full details for an ERA Report:
    - Header info
    - List of Claim Bundles with nested Claim Lines
    """
    with get_db_cursor() as cur:
        # 1. Header
        # 1. Header
        cur.execute("""
            SELECT 
                r.era_report_id, r.file_name, r.received_date, r.payer_name, r.check_number, r.check_date, 
                -- Calculated Total Paid for Consistency
                COALESCE(
                    (SELECT SUM(cl.paid_amount) 
                     FROM tebra.fin_era_bundle b 
                     JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
                     WHERE b.era_report_id = r.era_report_id), 
                    r.total_paid, 
                    0
                ) as total_paid,
                r.payment_method,
                COALESCE(p.name, 'Unknown Practice') as practice_name,
                r.claim_count_source
            FROM tebra.fin_era_report r
            LEFT JOIN tebra.cmn_practice p ON r.practice_guid = p.practice_guid
            WHERE r.era_report_id = %s
        """, (report_id,))
        header = cur.fetchone()
        
        if not header:
            raise HTTPException(status_code=404, detail="ERA Report not found")
            
        data = {
            "id": header[0],
            "fileName": header[1],
            "receivedDate": str(header[2]),
            "payer": header[3],
            "checkNumber": header[4],
            "checkDate": str(header[5]),
            "totalPaid": float(header[6] or 0),
            "method": header[7],
            "practice": header[8],
            "claimCount": int(header[9] or 0),
            "bundles": []
        }
        
        # 2. Bundles & Lines
        # Fetching flat and nesting in python
        # Added Practice Name and Provider Name
        cur.execute("""
            SELECT 
                b.claim_reference_id, b.total_paid, b.total_patient_resp,
                cl.tebra_claim_id, cl.proc_code, cl.billed_amount, cl.paid_amount, 
                cl.claim_status, cl.payer_status, cl.date_of_service,
                cl.adjustments_json, cl.adjustment_descriptions,
                p.full_name as patient_name,
                
                -- Aggregate Diagnoses
                (
                    SELECT STRING_AGG(diag.diag_code || ': ' || COALESCE(diag.description, ''), ', ')
                    FROM tebra.clin_encounter_diagnosis diag
                    WHERE diag.encounter_id = cl.encounter_id
                ) as diagnoses,
                
                -- Provider Name (from Encounter)
                prov.name as provider_name
                
            FROM tebra.fin_era_bundle b
            LEFT JOIN tebra.fin_claim_line cl ON b.claim_reference_id = cl.claim_reference_id
            LEFT JOIN tebra.clin_encounter e ON cl.encounter_id = e.encounter_id
            LEFT JOIN tebra.cmn_patient p ON e.patient_guid = p.patient_guid
            LEFT JOIN tebra.cmn_provider prov ON e.provider_guid = prov.provider_guid
            WHERE b.era_report_id = %s
            ORDER BY b.claim_reference_id
        """, (report_id,))
        
        rows = cur.fetchall()
        
        # Group by Bundle
        bundles_map = {}
        for row in rows:
            bid = row[0]
            if bid not in bundles_map:
                bundles_map[bid] = {
                    "referenceId": bid,
                    "bundlePaid": float(row[1] or 0),
                    "patientResp": float(row[2] or 0),
                    "claims": []
                }
            
            # Add Claims if present
            if row[3]: # tebra_claim_id exists
                # Parse Adjustments
                adj_json = row[10]
                adj_desc = row[11]
                adj_str = ""
                
                if adj_json:
                    import json
                    try:
                        # adj_json might be string or dict depending on driver/db
                        adjs = adj_json if isinstance(adj_json, dict) else json.loads(adj_json)
                        if isinstance(adjs, dict):
                             # Format as "Code: $Amount, ..."
                             adj_str = ", ".join([f"{k}: ${v}" for k, v in adjs.items()])
                    except:
                        adj_str = str(adj_json)
                
                
                # Status Logic: Prioritize Rejected/Denied ONLY if not paid
                c_status = row[7]
                p_status = row[8]
                paid_amount = float(row[6] or 0)
                billed_amount = float(row[5] or 0)
                
                final_status = c_status or p_status or "Processed"
                previously_rejected = False
                
                if paid_amount > 0:
                    final_status = "Paid" 
                    # Check for specific keywords in either field to override generic status
                    if (c_status and "Rejected" in c_status) or (p_status and "Rejected" in p_status):
                         previously_rejected = True
                else:
                    # Unpaid Claims ($0)
                    if (c_status and "Rejected" in c_status) or (p_status and "Rejected" in p_status):
                        final_status = "Rejected"
                    else:
                        # Default all other $0 claims (Pending, Processed, Denied, etc.) to Denied
                        final_status = "Denied"

                # Add line
                bundles_map[bid]["claims"].append({
                    "claimId": row[3],
                    "procCode": row[4],
                    "billed": billed_amount,
                    "paid": paid_amount,
                    "status": final_status,
                    "previouslyRejected": previously_rejected,
                    "date": str(row[9]),
                    "adjustments": adj_str,
                    "adjustmentDescriptions": adj_desc,
                    "patient": row[12] or "Unknown",
                    "diagnoses": row[13] or "",
                    "provider": row[14] or "Unknown Provider"
                })
            
        # Calculate Summary Counts
        paid_cnt = 0
        rejected_cnt = 0
        denied_cnt = 0
        
        all_bundles = list(bundles_map.values())
        for b in all_bundles:
            for c in b["claims"]:
                if c["paid"] > 0:
                    paid_cnt += 1
                elif c["status"] == "Rejected": 
                    rejected_cnt += 1
                elif c["status"] == "Denied":
                    denied_cnt += 1
        
        data["bundles"] = all_bundles
        data["summary"] = {
            "paid": paid_cnt,
            "rejected": rejected_cnt,
            "denied": denied_cnt
        }
        return data

