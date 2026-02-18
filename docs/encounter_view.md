# Encounter 360 View: 388650
**Generated from Postgres Database**

## 1. Context
- **Encounter GUID**: `71242908-70a8-4e5d-9f38-d0e798f9c1f1`
- **Date**: 2025-10-08
- **Status**: Approved
- **Type**: None
- **Reason**: None
- **Location**: KEYS2WELLNESS LLC
- **Address**: `{'city': 'LAUREL', 'state': 'MS', 'address': '216 S 13TH AVE # C'}`

## 2. Entities
### Patient
- **Name**: **KATHARINE PETTY**
- **Case ID**: `106818`
- **Tebra ID**: `113520`
- **Patient GUID**: `033e412f-5d02-4884-a4be-3445baf51878`

### Provider
- **Name**: FELICIA KEYS
- **NPI**: `1497187512`

### Payer (Insurance)
- **Company**: Medicare of Mississippi
- **Plan**: Medicare of Mississippi
- **Policy #**: `7V42XG3RX91`
- **Group #**: ``

## 3. Clinical Data
### Diagnoses
- **713793** - Major depressive disorder, recurrent severe without psychotic features (Precedence: 5)
- **713794** - Generalized anxiety disorder (Precedence: 6)
- **713795** - Personal history of other mental and behavioral disorders (Precedence: 7)
- **713796** - Problems of adjustment to life-cycle transitions (Precedence: 8)

## 4. Financials (Lines)
| Date | Proc | Description | Billed | Paid (Line) | Units | ERA Ref | Adjustments |
|---|---|---|---|---|---|---|---|
| 2025-10-08 | `HC:99215:25` | OFFICE OR OTHER OUTPATIENT VISIT FOR THE EVALUATION AND MANAGEMENT OF AN ESTABLISHED PATIENT, WHICH REQUIRES A MEDICALLY APPROPRIATE HISTORY AND/OR EXAMINATION AND HIGH LEVEL OF MEDICAL DECISION MAKING. WHEN USING TOTAL TIME ON THE DATE OF THE ENCOUNTER, 40 MINUTES MUST BE MET OR EXCEEDED. | $208.47 | $0.00 | 0 | `388650Z43267` | `{'OA-22': 208.47}`<br>_OA-22: Payment adjusted because this care may be covered by another payer per coordination of benefits._ |
| 2025-10-08 | `HC:99417` | Prolonged office or other outpatient evaluation and management service(s) beyond the maximum required time of the primary procedure which has been selected using total time on the date of the primary service; each addl 15 mins by the physician or QHCP, with or without direct patient contact | $50.00 | $0.00 | 0 | `388650Z43267` | `{'CO-96': 50.0}`<br>_CO-96: Non-covered charge(s). This change to be effective 4/1/2007: At least one Remark Code must be provided (may be comprised of either the Remittance Advice Remark Code or NCPDP Reject Reason Code.)_ |
| 2025-10-08 | `HC:96127` | Assessment of emotional or behavioral problems | $100.00 | $0.00 | 0 | `388650Z43267` | `{'OA-22': 100.0}`<br>_OA-22: Payment adjusted because this care may be covered by another payer per coordination of benefits._ |
| 2025-10-08 | `HC:99401` | Preventive medicine counseling, typically 15 minutes | $59.24 | $0.00 | 0 | `388650Z43267` | `{'PR-96': 59.24}`<br>_PR-96: Non-covered charge(s). This change to be effective 4/1/2007: At least one Remark Code must be provided (may be comprised of either the Remittance Advice Remark Code or NCPDP Reject Reason Code.)_ |
| 2025-10-08 | `HC:G2083` | Visit esketamine, > 56m | $1093.68 | $0.00 | 0 | `388650Z43267` | `{'OA-22': 1093.68}`<br>_OA-22: Payment adjusted because this care may be covered by another payer per coordination of benefits._ |

**Totals**: Billed: **$1511.39** | Line Paid: **$0.00**

## 5. ERA Payment Bundles (Parent Checks)
| Claim Ref ID | Payer Name | Total Check Paid | Patient Resp |
|---|---|---|---|
| `388650Z43267` | MS MEDICARE | $0.00 | $59.24 |