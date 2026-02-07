export const CARC_CODES = {
    '1': 'Deductible Amount',
    '2': 'Coinsurance Amount',
    '3': 'Co-payment Amount',
    '45': 'Charge exceeds fee schedule/maximum allowable or contracted/legislated fee arrangement',
    '96': 'Non-covered charge(s)',
    '97': 'The benefit for this service is included in the payment/allowance for another service/procedure that has already been adjudicated',
    '16': 'Claim/service lacks information or has submission/billing error(s)',
    '18': 'Duplicate claim/service',
    '29': 'The time limit for filing has expired',
    '22': 'This care may be covered by another payer per coordination of benefits',
    '109': 'Claim not covered by this payer/contractor. You must send the claim to the correct payer/contractor',
    '27': 'Expenses incurred after coverage terminated'
};

export const RARC_CODES = {
    'N1': 'Alert: You may appeal this decision in writing within the duration specified globally',
    'M15': 'Separately billed services/tests have been bundled',
    'M25': 'This service is not covered when performed by this provider',
    'N365': 'This procedure code is not payable',
    'MA130': 'Your claim contains incomplete and/or invalid information, and no appeal rights are afforded because the claim is unprocessable'
};

export function getAdjustmentDesc(code) {
    // Input format example: "CO-45" or "PR-3"
    if (!code) return '';
    const parts = code.split('-');
    const numCode = parts.length > 1 ? parts[1] : parts[0];

    // Check CARC
    if (CARC_CODES[numCode]) return CARC_CODES[numCode];

    // Check RARC (often independent)
    if (RARC_CODES[numCode]) return RARC_CODES[numCode];

    return 'Unknown Code';
}
