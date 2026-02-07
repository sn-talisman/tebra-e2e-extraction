import React, { useEffect, useState } from 'react';

const ClaimDetailsModal = ({ isOpen, onClose, claimRefId }) => {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isOpen && claimRefId) {
            fetchClaimDetails();
        } else {
            setDetails(null);
        }
    }, [isOpen, claimRefId]);

    const fetchClaimDetails = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/claims/${claimRefId}/details`);
            if (!response.ok) {
                throw new Error('Failed to fetch claim details');
            }
            const data = await response.json();
            setDetails(data);
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex',
            justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }} onClick={onClose}>
            <div className="modal-content" style={{
                backgroundColor: 'white', borderRadius: '8px', width: '900px',
                maxWidth: '95vw', maxHeight: '90vh', overflowY: 'auto',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
            }} onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div style={{
                    padding: '20px 24px', borderBottom: '1px solid #e2e8f0',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    position: 'sticky', top: 0, backgroundColor: 'white', zIndex: 10
                }}>
                    <div>
                        <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                            Claim Details
                        </h2>
                        <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                            Ref ID: {claimRefId}
                        </div>
                    </div>

                    <button onClick={onClose} style={{
                        background: 'none', border: 'none', fontSize: '24px',
                        cursor: 'pointer', color: '#64748b'
                    }}>&times;</button>
                </div>

                {loading ? (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading details...</div>
                ) : error ? (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#ef4444' }}>Error: {error}</div>
                ) : details ? (
                    <div style={{ padding: '24px' }}>

                        {/* Header Context */}
                        <div style={{
                            display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px',
                            marginBottom: '24px', padding: '16px', backgroundColor: '#f8fafc', borderRadius: '8px'
                        }}>
                            <InfoItem label="Date of Service" value={details.header.date} />
                            <InfoItem label="Status" value={details.header.status}
                                badgeColor={
                                    details.header.status === 'Paid' ? '#22c55e' :
                                        details.header.status === 'Denied' || details.header.status === 'Rejected' ? '#ef4444' :
                                            '#f59e0b'
                                }
                            />
                            <InfoItem label="Patient" value={details.header.patient.name} />
                            <InfoItem label="Provider" value={details.header.provider} />
                        </div>

                        {/* Financial Summary */}
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '24px', marginBottom: '24px', padding: '16px', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
                            <SummaryItem label="Total Billed" value={details.financials.totals.billed} />
                            <SummaryItem label="Total Paid" value={details.financials.totals.paid} color="#22c55e" />
                            <SummaryItem label="Balance" value={details.financials.totals.balance} color="#64748b" />
                        </div>

                        {/* Line Items */}
                        <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', marginBottom: '24px' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead style={{ backgroundColor: '#f8fafc' }}>
                                    <tr>
                                        <th style={thStyle}>Date</th>
                                        <th style={thStyle}>Proc Code</th>
                                        <th style={thStyle}>Description</th>
                                        <th style={thStyle}>Billed</th>
                                        <th style={thStyle}>Paid</th>
                                        <th style={thStyle}>Adj</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {details.financials.lines.map((line, idx) => (
                                        <tr key={idx} style={{ borderTop: '1px solid #e2e8f0' }}>
                                            <td style={tdStyle}>{line.date}</td>
                                            <td style={tdStyle}>
                                                <code style={{ backgroundColor: '#f1f5f9', padding: '2px 4px', borderRadius: '4px' }}>
                                                    {line.procCode}
                                                </code>
                                            </td>
                                            <td style={{ ...tdStyle, maxWidth: '250px' }}>{line.description}</td>
                                            <td style={tdStyle}>${line.billed.toFixed(2)}</td>
                                            <td style={tdStyle}>${line.paid.toFixed(2)}</td>
                                            <td style={{ ...tdStyle, color: '#64748b', minWidth: '180px' }}>
                                                {line.adjustmentDescriptions ? (
                                                    <span title={line.adjustmentDescriptions}>{line.adjustmentDescriptions}</span>
                                                ) : line.adjustments ? (
                                                    Object.entries(line.adjustments).map(([code, amount], i) => (
                                                        <div key={i}>{code}: ${amount}</div>
                                                    ))
                                                ) : '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* ERA Info */}
                        {details.financials.eras.length > 0 && (
                            <div>
                                <h3 style={sectionTitleStyle}>ERA Payments</h3>
                                <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                        <thead style={{ backgroundColor: '#f8fafc' }}>
                                            <tr>
                                                <th style={thStyle}>Payer</th>
                                                <th style={thStyle}>Check #</th>
                                                <th style={thStyle}>Date</th>
                                                <th style={thStyle}>Paid</th>
                                                <th style={thStyle}>Pat Resp</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {details.financials.eras.map((era, idx) => (
                                                <tr key={idx} style={{ borderTop: '1px solid #e2e8f0' }}>
                                                    <td style={tdStyle}>{era.payer}</td>
                                                    <td style={tdStyle}>{era.checkNumber || '-'}</td>
                                                    <td style={tdStyle}>{era.checkDate || '-'}</td>
                                                    <td style={tdStyle}>${era.paid.toFixed(2)}</td>
                                                    <td style={tdStyle}>${era.patientResp.toFixed(2)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                    </div>
                ) : null}
            </div>
        </div>
    );
};

// Styles & Helpers
const sectionTitleStyle = {
    fontSize: '16px', fontWeight: '600', color: '#1e293b',
    marginBottom: '12px'
};

const InfoItem = ({ label, value, badgeColor }) => (
    <div>
        <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</div>
        <div style={{ fontSize: '14px', fontWeight: '500', color: badgeColor || '#0f172a', marginTop: '4px' }}>
            {value || 'N/A'}
        </div>
    </div>
);

const SummaryItem = ({ label, value, color }) => (
    <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>{label}</div>
        <div style={{ fontSize: '18px', fontWeight: '600', color: color || '#0f172a' }}>
            ${(value || 0).toFixed(2)}
        </div>
    </div>
);

const thStyle = {
    textAlign: 'left', padding: '12px 16px', fontSize: '12px',
    fontWeight: '600', color: '#64748b', textTransform: 'uppercase'
};

const tdStyle = {
    padding: '12px 16px', fontSize: '14px', color: '#334155', verticalAlign: 'top'
};

export default ClaimDetailsModal;
