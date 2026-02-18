"""Practice Insights Report - Self-contained (queries tebra_dw directly).

This module generates a markdown report for a practice by querying the
local tebra_dw database tables directly.  It does NOT depend on the
denial-models AI service (port 8001).

Tables used:
  tebra.fin_claim_line      – claim-level financial data
  tebra.fin_era_bundle      – ERA payer information
  tebra.cmn_practice        – practice name lookup
  tebra.clin_encounter      – encounter ↔ insurance policy link
  tebra.ref_insurance_policy – payer company name
"""

from fastapi import APIRouter
from typing import Dict, Any, List, Tuple
from datetime import date, timedelta
import json
import re
from app.db.connection import get_db_cursor

router = APIRouter()

# -----------------------------------------------------------------------
#  DATA ACCESS  – all queries hit tebra_dw via psycopg2
# -----------------------------------------------------------------------

def _get_practice_name(practice_guid: str) -> str:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT name FROM tebra.cmn_practice WHERE practice_guid = %s",
            (practice_guid,),
        )
        row = cur.fetchone()
        return row[0] if row else "Unknown Practice"


def _get_performance_summary(practice_guid: str, date_from: date, date_to: date) -> Dict[str, Any]:
    """Aggregate performance metrics for the practice."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*)                                    AS total_claims,
                COALESCE(SUM(billed_amount), 0)             AS total_billed,
                COALESCE(SUM(paid_amount), 0)               AS total_paid,
                COALESCE(SUM(billed_amount) - SUM(paid_amount), 0) AS denied_amount
            FROM tebra.fin_claim_line
            WHERE practice_guid = %s
              AND date_of_service BETWEEN %s AND %s
        """, (practice_guid, date_from, date_to))
        row = cur.fetchone()
        total_claims = row[0] or 0
        total_billed = float(row[1])
        total_paid   = float(row[2])
        denied_amount = float(row[3])

        # Denial rate  =  claims where paid==0 / total
        cur.execute("""
            SELECT COUNT(*) FROM tebra.fin_claim_line
            WHERE practice_guid = %s
              AND date_of_service BETWEEN %s AND %s
              AND paid_amount = 0
        """, (practice_guid, date_from, date_to))
        denied_count = cur.fetchone()[0] or 0

        denial_rate = denied_count / total_claims if total_claims else 0.0

        # Overall denial rate (all practices, same window)
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE paid_amount = 0)::float
                / NULLIF(COUNT(*), 0)
            FROM tebra.fin_claim_line
            WHERE date_of_service BETWEEN %s AND %s
        """, (date_from, date_to))
        overall_rate = cur.fetchone()[0] or 0.0

        return {
            "total_claims": total_claims,
            "total_billed": total_billed,
            "total_paid": total_paid,
            "denied_amount": denied_amount,
            "denial_rate": denial_rate,
            "denial_rate_vs_overall": denial_rate - overall_rate,
            "avg_denial_probability": 0.0,
            "avg_probability_vs_overall": 0.0,
            "high_risk_claims": 0,
            "high_risk_pct": 0.0,
        }


def _get_payer_performance(practice_guid: str, date_from: date, date_to: date) -> List[Dict]:
    """Per-payer breakdown using ERA bundle payer_name."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT
                COALESCE(eb.payer_name, ip.company_name, cl.clearinghouse_payer, 'Unknown') AS payer_name,
                COUNT(*)                              AS total_claims,
                COUNT(*) FILTER (WHERE cl.paid_amount = 0)::float
                    / NULLIF(COUNT(*), 0)              AS denial_rate,
                COALESCE(SUM(cl.billed_amount - cl.paid_amount), 0) AS denied_amount
            FROM tebra.fin_claim_line cl
            LEFT JOIN tebra.fin_era_bundle eb
                ON cl.claim_reference_id = eb.claim_reference_id
            LEFT JOIN tebra.clin_encounter ce
                ON cl.encounter_id = ce.encounter_id
            LEFT JOIN tebra.ref_insurance_policy ip
                ON ce.insurance_policy_key = ip.policy_key
            WHERE cl.practice_guid = %s
              AND cl.date_of_service BETWEEN %s AND %s
            GROUP BY 1
            ORDER BY denied_amount DESC
        """, (practice_guid, date_from, date_to))
        rows = cur.fetchall()
        return [
            {
                "payer_name": r[0] or "Unknown",
                "total_claims": r[1],
                "denial_rate": float(r[2] or 0),
                "denied_amount": float(r[3]),
                "avg_denial_probability": 0.0,
            }
            for r in rows
        ]


def _get_cpt_performance(practice_guid: str, date_from: date, date_to: date) -> List[Dict]:
    """Per-CPT code breakdown."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT
                proc_code                              AS cpt_code,
                COUNT(*)                               AS total_claims,
                COUNT(*) FILTER (WHERE paid_amount = 0)::float
                    / NULLIF(COUNT(*), 0)               AS denial_rate,
                COALESCE(SUM(billed_amount - paid_amount), 0) AS denied_amount
            FROM tebra.fin_claim_line
            WHERE practice_guid = %s
              AND date_of_service BETWEEN %s AND %s
              AND proc_code IS NOT NULL
            GROUP BY proc_code
            ORDER BY denied_amount DESC
        """, (practice_guid, date_from, date_to))
        rows = cur.fetchall()
        return [
            {
                "cpt_code": r[0],
                "total_claims": r[1],
                "denial_rate": float(r[2] or 0),
                "denied_amount": float(r[3]),
                "avg_denial_probability": 0.0,
            }
            for r in rows
        ]


def _get_high_risk_claims(practice_guid: str, date_from: date, date_to: date, limit: int = 20) -> List[Dict]:
    """Claims with the highest denied amounts (proxy for 'high risk')."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT
                cl.claim_reference_id,
                COALESCE(eb.payer_name, cl.clearinghouse_payer, 'Unknown') AS payer_name,
                cl.proc_code,
                cl.billed_amount,
                cl.paid_amount
            FROM tebra.fin_claim_line cl
            LEFT JOIN tebra.fin_era_bundle eb
                ON cl.claim_reference_id = eb.claim_reference_id
            WHERE cl.practice_guid = %s
              AND cl.date_of_service BETWEEN %s AND %s
              AND cl.paid_amount = 0
              AND cl.billed_amount > 0
            ORDER BY cl.billed_amount DESC
            LIMIT %s
        """, (practice_guid, date_from, date_to, limit))
        rows = cur.fetchall()
        return [
            {
                "claim_id": r[0] or "N/A",
                "payer_name": r[1] or "Unknown",
                "cpt_code": r[2] or "N/A",
                "denial_probability": 1.0,  # fully denied
                "billed_amount": float(r[3] or 0),
            }
            for r in rows
        ]


def _parse_carc_codes(adjustments_json: str) -> List[Tuple[str, float]]:
    """Parse adjustment JSON like '{"CO-45": 123.0, "PR-22": 56.0}'.
    
    Returns list of (carc_code, amount) tuples.
    """
    try:
        data = json.loads(adjustments_json)
        # Handle double-encoded JSON: '"{\"CO-18\": 54.0}"'
        if isinstance(data, str):
            data = json.loads(data)
        if not isinstance(data, dict):
            return []
        results = []
        for key, amount in data.items():
            # key format is "GROUP-CODE", e.g. "CO-45" → CARC 45
            parts = key.split("-", 1)
            if len(parts) == 2:
                carc_code = parts[1]
                results.append((carc_code, float(amount)))
        return results
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


# CARC descriptions for common codes
CARC_DESCRIPTIONS = {
    "1": "Deductible Amount",
    "2": "Coinsurance Amount",
    "3": "Co-payment Amount",
    "4": "The procedure code is inconsistent with the modifier used",
    "5": "The procedure code/bill type is inconsistent with the place of service",
    "15": "Authorization requirement not met",
    "16": "Claim/service lacks information which is needed for adjudication",
    "18": "Exact duplicate claim/service",
    "22": "This care may be covered by another payer per coordination of benefits",
    "23": "Coordination of Benefits",
    "27": "Expenses incurred after coverage terminated",
    "29": "Time limit for filing has expired",
    "39": "Services denied at the time authorization/pre-certification was requested",
    "45": "Charge exceeds fee schedule/maximum allowable or contracted/legislated fee arrangement",
    "50": "These are non-covered services because this is not deemed a medical necessity",
    "55": "Medical Necessity",
    "56": "Medical Necessity",
    "96": "Non-covered charge(s)",
    "97": "The benefit for this service is included in the payment/allowance for another service",
    "104": "Managed care withholding",
    "109": "Claim/service not covered by this payer/contractor",
    "119": "Benefit maximum for this time period or occurrence has been reached",
    "197": "Precertification/authorization/notification absent",
    "242": "Self-administered drug",
    "251": "Information not available from provider",
    "252": "Service not rendered",
    "253": "Claim/service denied. Refer to the 835 Healthcare Policy Identification Segment",
}


def _get_denial_reasons(practice_guid: str, date_from: date, date_to: date) -> Dict[str, Any]:
    """Extract CARC codes from adjustments_json."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT adjustments_json
            FROM tebra.fin_claim_line
            WHERE practice_guid = %s
              AND date_of_service BETWEEN %s AND %s
              AND adjustments_json IS NOT NULL
              AND adjustments_json != ''
              AND adjustments_json != '{}'
        """, (practice_guid, date_from, date_to))
        rows = cur.fetchall()

    # Aggregate CARC codes
    carc_agg: Dict[str, Dict] = {}
    for (adj_json,) in rows:
        for carc_code, amount in _parse_carc_codes(adj_json):
            if carc_code not in carc_agg:
                carc_agg[carc_code] = {
                    "carc_code": carc_code,
                    "description": CARC_DESCRIPTIONS.get(carc_code, f"CARC {carc_code}"),
                    "occurrence_count": 0,
                    "affected_claims": 0,
                    "total_adjustment_amount": 0.0,
                }
            carc_agg[carc_code]["occurrence_count"] += 1
            carc_agg[carc_code]["affected_claims"] += 1
            carc_agg[carc_code]["total_adjustment_amount"] += amount

    carc_list = sorted(carc_agg.values(), key=lambda x: x["total_adjustment_amount"], reverse=True)
    return {"carc_codes": carc_list, "rarc_codes": []}


def _get_cpt_carc_correlation(practice_guid: str, date_from: date, date_to: date) -> Dict[str, Any]:
    """Cross-tab CPT × CARC."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT proc_code, adjustments_json
            FROM tebra.fin_claim_line
            WHERE practice_guid = %s
              AND date_of_service BETWEEN %s AND %s
              AND adjustments_json IS NOT NULL
              AND adjustments_json != ''
              AND adjustments_json != '{}'
              AND proc_code IS NOT NULL
        """, (practice_guid, date_from, date_to))
        rows = cur.fetchall()

    combo_agg: Dict[str, Dict] = {}
    for proc_code, adj_json in rows:
        for carc_code, amount in _parse_carc_codes(adj_json):
            key = f"{proc_code}|{carc_code}"
            if key not in combo_agg:
                combo_agg[key] = {
                    "cpt_code": proc_code,
                    "carc_code": carc_code,
                    "carc_description": CARC_DESCRIPTIONS.get(carc_code, f"CARC {carc_code}"),
                    "occurrence_count": 0,
                    "affected_claims": 0,
                    "total_adjustment_amount": 0.0,
                }
            combo_agg[key]["occurrence_count"] += 1
            combo_agg[key]["affected_claims"] += 1
            combo_agg[key]["total_adjustment_amount"] += amount

    combos = sorted(combo_agg.values(), key=lambda x: x["total_adjustment_amount"], reverse=True)
    return {"cpt_carc": combos}


# -----------------------------------------------------------------------
#  MARKDOWN GENERATION  – identical structure to reference script
# -----------------------------------------------------------------------

def _build_markdown(
    practice_name: str,
    summary: Dict[str, Any],
    payers: List[Dict],
    cpts: List[Dict],
    high_risk: List[Dict],
    denial_reasons: Dict[str, Any],
    cpt_carc: Dict[str, Any],
) -> str:
    md: List[str] = []

    # Header
    md.append(f"## {practice_name}")
    md.append("")

    # ── Performance Summary ────────────────────────────────────────────
    md.append("### 📊 Performance Summary")
    md.append("")
    md.append("| Metric | Value | vs Overall |")
    md.append("|--------|-------|------------|")
    md.append(f"| Total Claims | {summary['total_claims']:,} | - |")
    dr = summary["denial_rate"]
    dr_vs = summary["denial_rate_vs_overall"]
    md.append(f"| Denial Rate | {dr:.1%} | {'🔴 +' if dr_vs > 0 else '🟢 '}{dr_vs:+.1%} |")
    md.append(f"| Total Billed | ${summary['total_billed']:,.2f} | - |")
    md.append(f"| Total Paid | ${summary['total_paid']:,.2f} | - |")
    md.append(f"| **Denied Amount** | **${summary['denied_amount']:,.2f}** | **Potential Recovery** |")
    md.append("")

    # ── Prioritized Action Items (top payer + top CPT denials) ─────────
    action_items = []
    for p in payers[:3]:
        if p["denial_rate"] > 0:
            action_items.append({
                "title": f"High Denial Rate with {p['payer_name'][:40]}",
                "financial_impact": p["denied_amount"],
                "recommendation": (
                    f"Review documentation requirements and coding practices for "
                    f"{p['payer_name'][:40]}. Consider payer-specific training for billing staff."
                ),
                "details": (
                    f"{p['denial_rate']:.1%} denial rate on {p['total_claims']} claims "
                    f"(${p['denied_amount']:,.2f} at risk)"
                ),
            })
    for c in cpts[:3]:
        if c["denial_rate"] > 0:
            action_items.append({
                "title": f"High Denial Rate for CPT {c['cpt_code']}",
                "financial_impact": c["denied_amount"],
                "recommendation": (
                    f"Review coding accuracy and documentation for CPT {c['cpt_code']}. "
                    f"Verify code selection and medical necessity."
                ),
                "details": (
                    f"{c['denial_rate']:.1%} denial rate "
                    f"({int(c['total_claims'] * c['denial_rate'])}/{c['total_claims']} claims, "
                    f"${c['denied_amount']:,.2f} at risk)"
                ),
            })
    # Sort action items by financial impact
    action_items.sort(key=lambda x: x["financial_impact"], reverse=True)

    if action_items:
        md.append("### 🎯 Prioritized Action Items")
        md.append("")
        for idx, item in enumerate(action_items[:10], 1):
            md.append(f"#### {idx}. {item['title']}")
            md.append("")
            md.append(f"**Financial Impact**: ${item['financial_impact']:,.2f} in denied claims")
            md.append("")
            md.append(f"**Recommendation**: {item['recommendation']}")
            if item.get("details"):
                md.append("")
                md.append(f"*{item['details']}*")
            md.append("")
    else:
        md.append("### 🎯 Prioritized Action Items")
        md.append("")
        md.append("*No specific action items identified. Practice performance is within normal parameters.*")
        md.append("")

    # ── Detailed Analysis ──────────────────────────────────────────────
    if payers:
        md.append("### 📋 Detailed Analysis")
        md.append("")
        md.append("#### Performance by Payer")
        md.append("")
        md.append("| Payer | Claims | Denial Rate | Denied Amount | Avg Risk |")
        md.append("|-------|--------|-------------|---------------|----------|")
        for p in payers[:10]:
            md.append(
                f"| {p['payer_name'][:40]} | {p['total_claims']} "
                f"| {p['denial_rate']:.1%} | ${p['denied_amount']:,.2f} "
                f"| {p['avg_denial_probability']:.2f} |"
            )
        md.append("")

    if cpts:
        md.append("#### Performance by CPT Code")
        md.append("")
        md.append("| CPT Code | Claims | Denial Rate | Denied Amount | Avg Risk |")
        md.append("|----------|--------|-------------|---------------|----------|")
        for c in cpts[:10]:
            md.append(
                f"| {c['cpt_code']} | {c['total_claims']} "
                f"| {c['denial_rate']:.1%} | ${c['denied_amount']:,.2f} "
                f"| {c['avg_denial_probability']:.2f} |"
            )
        md.append("")

    # High-risk claims
    if high_risk:
        md.append("#### High-Risk Claims Requiring Immediate Attention")
        md.append("")
        md.append("| Claim ID | Payer | CPT | Denial Prob | Billed Amount |")
        md.append("|----------|-------|-----|-------------|---------------|")
        for cl in high_risk[:20]:
            cid = (cl["claim_id"] or "N/A")[:8]
            pn = (cl["payer_name"] or "Unknown")[:25]
            cpt = (cl["cpt_code"] or "N/A")[:10]
            md.append(
                f"| {cid} | {pn} | {cpt} "
                f"| {cl['denial_probability']:.1%} | ${cl['billed_amount']:,.2f} |"
            )
        md.append("")
    else:
        md.append("#### High-Risk Claims Requiring Immediate Attention")
        md.append("")
        md.append("*No high-risk claims identified.*")
        md.append("")

    # CARC codes
    carc_codes = denial_reasons.get("carc_codes", [])
    if carc_codes:
        md.append("#### Denial Reasons (CARC/RARC Codes)")
        md.append("")
        md.append("##### Top CARC (Claim Adjustment Reason) Codes")
        md.append("")
        md.append("| CARC Code | Description | Occurrences | Affected Claims | Total Amount |")
        md.append("|-----------|-------------|-------------|-----------------|--------------|")
        for c in carc_codes[:15]:
            md.append(
                f"| {c['carc_code']} | {c['description'][:50]} "
                f"| {c['occurrence_count']} | {c['affected_claims']} "
                f"| ${c['total_adjustment_amount']:,.2f} |"
            )
        md.append("")

    # CPT-CARC correlation
    cpt_carc_list = cpt_carc.get("cpt_carc", [])
    if cpt_carc_list:
        md.append("#### CPT-CARC Correlation Analysis")
        md.append("")
        md.append("This analysis shows which procedure codes are most commonly associated with which denial reason codes.")
        md.append("")
        md.append("##### Top CPT-CARC Combinations")
        md.append("")
        md.append("| CPT Code | CARC Code | Description | Occurrences | Affected Claims | Total Amount |")
        md.append("|----------|-----------|-------------|-------------|-----------------|--------------|")
        for combo in cpt_carc_list[:15]:
            md.append(
                f"| {combo['cpt_code']} | {combo['carc_code']} "
                f"| {combo['carc_description'][:40]} "
                f"| {combo['occurrence_count']} | {combo['affected_claims']} "
                f"| ${combo['total_adjustment_amount']:,.2f} |"
            )
        md.append("")

    md.append("")
    md.append("---")
    md.append("")
    return "\n".join(md)


# -----------------------------------------------------------------------
#  ENDPOINT
# -----------------------------------------------------------------------

@router.get("/practice/{practice_guid}/insights/markdown")
def get_practice_insights_markdown(practice_guid: str, days_back: int = 90):
    """Generate a full markdown report for the practice.

    Queries the local tebra_dw database directly – no external service needed.
    """
    date_to = date.today()
    date_from = date_to - timedelta(days=days_back)

    practice_name = _get_practice_name(practice_guid)
    summary       = _get_performance_summary(practice_guid, date_from, date_to)
    payers        = _get_payer_performance(practice_guid, date_from, date_to)
    cpts          = _get_cpt_performance(practice_guid, date_from, date_to)
    high_risk     = _get_high_risk_claims(practice_guid, date_from, date_to)
    denial_reasons = _get_denial_reasons(practice_guid, date_from, date_to)
    cpt_carc      = _get_cpt_carc_correlation(practice_guid, date_from, date_to)

    markdown_body = _build_markdown(
        practice_name, summary, payers, cpts, high_risk, denial_reasons, cpt_carc
    )

    header = [
        "# Practice Performance Insights & Actionable Recommendations",
        "",
        f"*Generated from local database for 1 practice over the past {days_back} days "
        f"({summary['total_claims']:,} total claims)*",
        "",
        "---",
        "",
    ]

    return {"markdown": "\n".join(header) + markdown_body}


@router.get("/practice/{practice_guid}/insights/data")
def get_practice_insights_data(practice_guid: str, days_back: int = 90):
    """Return structured JSON data for interactive report rendering."""
    date_to = date.today()
    date_from = date_to - timedelta(days=days_back)

    practice_name  = _get_practice_name(practice_guid)
    summary        = _get_performance_summary(practice_guid, date_from, date_to)
    payers         = _get_payer_performance(practice_guid, date_from, date_to)
    cpts           = _get_cpt_performance(practice_guid, date_from, date_to)
    high_risk      = _get_high_risk_claims(practice_guid, date_from, date_to)
    denial_reasons = _get_denial_reasons(practice_guid, date_from, date_to)
    cpt_carc       = _get_cpt_carc_correlation(practice_guid, date_from, date_to)

    return {
        "practice_name": practice_name,
        "days_back": days_back,
        "summary": summary,
        "payers": payers[:15],
        "cpts": cpts[:15],
        "high_risk": high_risk,
        "denial_reasons": denial_reasons,
        "cpt_carc": cpt_carc,
    }

