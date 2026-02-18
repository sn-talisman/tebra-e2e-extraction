import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config';

const EncounterDetailsModal = ({ isOpen, onClose, encounterId }) => {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isOpen && encounterId) {
            fetchEncounterDetails();
        } else {
            setDetails(null);
        }
    }, [isOpen, encounterId]);

    const fetchEncounterDetails = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/api/encounters/${encounterId}/details`);
            if (!response.ok) {
                throw new Error('Failed to fetch encounter details');
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
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
        }} onClick={onClose}>
            <div className="modal-content" style={{
                backgroundColor: 'white',
                borderRadius: '8px',
                width: '900px',
                maxWidth: '95vw',
                maxHeight: '90vh',
                overflowY: 'auto',
                padding: '0',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
            }} onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div style={{
                    padding: '20px 24px',
                    borderBottom: '1px solid #e2e8f0',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    position: 'sticky',
                    top: 0,
                    backgroundColor: 'white',
                    zIndex: 10
                }}>
                    <div>
                        <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                            Encounter 360 View: {encounterId}
                        </h2>
                        {details && (
                            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                                GUID: {details.context.encounterGuid}
                            </div>
                        )}
                    </div>
                    <button onClick={onClose} style={{
                        background: 'none',
                        border: 'none',
                        fontSize: '24px',
                        cursor: 'pointer',
                        color: '#64748b'
                    }}>&times;</button>
                </div>

                {loading ? (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading details...</div>
                ) : error ? (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#ef4444' }}>Error: {error}</div>
                ) : details ? (
                    <div style={{ padding: '24px' }}>
                        {/* 1. Context & Status */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
                            <InfoCard label="Date" value={details.context.date} />
                            <InfoCard label="Status" value={details.context.status}
                                badgeColor={details.context.status === 'Approved' ? '#22c55e' : '#f59e0b'} />
                            <InfoCard label="Type" value={details.context.type || 'N/A'} />
                            <InfoCard label="Location" value={details.context.location} />
                        </div>

                        {/* 2. Entities Grid */}
                        <h3 style={sectionTitleStyle}>Entities involved</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', marginBottom: '24px' }}>
                            {/* Patient */}
                            <EntityCard title="Patient" icon="👤">
                                <div style={{ fontWeight: '600', color: '#334155' }}>{details.entities.patient.name}</div>
                                <div style={smallTextStyle}>ID: {details.entities.patient.id}</div>
                                <div style={smallTextStyle}>DOB: {details.entities.patient.dob}</div>
                                <div style={{ ...smallTextStyle, marginTop: '4px' }}>
                                    {details.entities.patient.address}
                                </div>
                            </EntityCard>

                            {/* Provider */}
                            <EntityCard title="Provider" icon="👨‍⚕️">
                                <div style={{ fontWeight: '600', color: '#334155' }}>{details.entities.provider.name}</div>
                                <div style={smallTextStyle}>NPI: {details.entities.provider.npi}</div>
                            </EntityCard>

                            {/* Payer */}
                            <EntityCard title="Payer" icon="🏦">
                                <div style={{ fontWeight: '600', color: '#334155' }}>{details.entities.payer.name}</div>
                                <div style={smallTextStyle}>Primary Insurance</div>
                            </EntityCard>
                        </div>

                        {/* 3. Clinical Data */}
                        <h3 style={sectionTitleStyle}>Clinical Data (Diagnoses)</h3>
                        <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', marginBottom: '24px' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead style={{ backgroundColor: '#f8fafc' }}>
                                    <tr>
                                        <th style={thStyle}>Code</th>
                                        <th style={thStyle}>Description</th>
                                        <th style={thStyle}>Precedence</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {details.clinical.diagnoses.map((diag, idx) => (
                                        <tr key={idx} style={{ borderTop: '1px solid #e2e8f0' }}>
                                            <td style={tdStyle}>
                                                <span style={{
                                                    backgroundColor: '#e0f2fe', color: '#0369a1',
                                                    padding: '2px 8px', borderRadius: '4px', fontSize: '13px', fontWeight: '500'
                                                }}>
                                                    {diag.code}
                                                </span>
                                            </td>
                                            <td style={tdStyle}>{diag.description}</td>
                                            <td style={tdStyle}>{diag.precedence}</td>
                                        </tr>
                                    ))}
                                    {details.clinical.diagnoses.length === 0 && (
                                        <tr><td colSpan="3" style={{ ...tdStyle, textAlign: 'center', color: '#94a3b8' }}>No diagnoses found</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* 4. Financials */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                            <h3 style={{ ...sectionTitleStyle, marginBottom: 0 }}>Financials</h3>
                            <div style={{ fontSize: '14px', fontWeight: '600' }}>
                                <span style={{ color: '#64748b' }}>Total Billed: </span>
                                <span style={{ color: '#0f172a' }}>${details.financials.totals.billed.toFixed(2)}</span>
                                <span style={{ margin: '0 8px', color: '#cbd5e1' }}>|</span>
                                <span style={{ color: '#64748b' }}>Total Paid: </span>
                                <span style={{ color: '#22c55e' }}>${details.financials.totals.paid.toFixed(2)}</span>
                            </div>
                        </div>

                        <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', marginBottom: '24px' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead style={{ backgroundColor: '#f8fafc' }}>
                                    <tr>
                                        <th style={thStyle}>Date</th>
                                        <th style={thStyle}>Proc Code</th>
                                        <th style={thStyle}>Description</th>
                                        <th style={thStyle}>Billed</th>
                                        <th style={thStyle}>Paid</th>

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
                                            <td style={{ ...tdStyle, maxWidth: '300px' }}>{line.description}</td>
                                            <td style={tdStyle}>${line.billed.toFixed(2)}</td>
                                            <td style={tdStyle}>${line.paid.toFixed(2)}</td>

                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* 5. ERA Info */}
                        {details.financials.eraBundles.length > 0 && (
                            <div style={{ backgroundColor: '#f8fafc', padding: '16px', borderRadius: '8px' }}>
                                <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#475569' }}>Payment Source (ERA)</h4>
                                {details.financials.eraBundles.map((era, idx) => (
                                    <div key={idx} style={{ display: 'flex', gap: '16px', fontSize: '13px' }}>
                                        <span><strong>Ref:</strong> {era.claimRefId}</span>
                                        <span><strong>Payer:</strong> {era.payer}</span>
                                        <span><strong>Check:</strong> ${era.paid.toFixed(2)}</span>
                                        <span><strong>Pat Resp:</strong> ${era.patientResp.toFixed(2)}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                    </div>
                ) : null}
            </div>
        </div>
    );
};

// Helper Components & Styles
const InfoCard = ({ label, value, badgeColor }) => (
    <div style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px' }}>
        <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</div>
        <div style={{
            fontSize: '14px', fontWeight: '500', color: badgeColor || '#0f172a',
            marginTop: '4px'
        }}>
            {value}
        </div>
    </div>
);

const EntityCard = ({ title, icon, children }) => (
    <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
            <span style={{ fontSize: '18px' }}>{icon}</span>
            <span style={{ fontSize: '14px', fontWeight: '600', color: '#475569' }}>{title}</span>
        </div>
        <div>{children}</div>
    </div>
);

const sectionTitleStyle = {
    fontSize: '16px',
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: '16px',
    paddingBottom: '8px',
    borderBottom: '2px solid #f1f5f9'
};

const smallTextStyle = {
    fontSize: '13px',
    color: '#64748b',
    lineHeight: '1.4'
};

const thStyle = {
    textAlign: 'left',
    padding: '12px 16px',
    fontSize: '12px',
    fontWeight: '600',
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
};

const tdStyle = {
    padding: '12px 16px',
    fontSize: '14px',
    color: '#334155',
    verticalAlign: 'top'
};

export default EncounterDetailsModal;
