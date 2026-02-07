import React, { useEffect, useState } from 'react';

const PatientDetailsModal = ({ isOpen, onClose, patientGuid }) => {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isOpen && patientGuid) {
            fetchPatientDetails();
        } else {
            setDetails(null);
        }
    }, [isOpen, patientGuid]);

    const fetchPatientDetails = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/patients/${patientGuid}/details`);
            if (!response.ok) {
                throw new Error('Failed to fetch patient details');
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

    const formatDate = (dateString) => {
        if (!dateString || dateString === 'N/A') return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { year: '2-digit', month: '2-digit', day: '2-digit' });
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex',
            justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }} onClick={onClose}>
            <div className="modal-content" style={{
                backgroundColor: 'white', borderRadius: '8px', width: '800px',
                maxWidth: '95vw', maxHeight: '90vh', overflowY: 'auto',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
            }} onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div style={{
                    padding: '20px 24px', borderBottom: '1px solid #e2e8f0',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    position: 'sticky', top: 0, backgroundColor: 'white', zIndex: 10
                }}>
                    <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                        Patient Details
                    </h2>
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
                        {/* Patient Information */}
                        <div style={{ marginBottom: '24px' }}>
                            <h3 style={sectionTitleStyle}>Patient Information</h3>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                <InfoItem label="Full Name" value={details.patient.fullName} />
                                <InfoItem label="Patient ID" value={details.patient.patientId} />
                                <InfoItem label="Date of Birth" value={formatDate(details.patient.dob)} />
                                <InfoItem label="Gender" value={details.patient.gender === 'M' ? 'Male' : details.patient.gender === 'F' ? 'Female' : details.patient.gender} />
                                <InfoItem label="Case ID" value={details.patient.caseId} />
                                <div style={{ gridColumn: 'span 2' }}>
                                    <InfoItem label="Address" value={
                                        details.patient.addressLine1 ?
                                            `${details.patient.addressLine1}, ${details.patient.city}, ${details.patient.state} ${details.patient.zip}` :
                                            'N/A'
                                    } />
                                </div>
                            </div>
                        </div>

                        {/* Insurance Information */}
                        {details.insurance && (
                            <div style={{ marginBottom: '24px' }}>
                                <h3 style={sectionTitleStyle}>Insurance Information</h3>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                    <InfoItem label="Provider" value={details.insurance.companyName} />
                                    <InfoItem label="Plan" value={details.insurance.planName} />
                                    <InfoItem label="Policy #" value={details.insurance.policyNumber} />
                                    <InfoItem label="Group #" value={details.insurance.groupNumber} />
                                </div>
                            </div>
                        )}

                        {/* Encounter History */}
                        <div>
                            <h3 style={sectionTitleStyle}>Encounter History</h3>
                            <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead style={{ backgroundColor: '#f8fafc' }}>
                                        <tr>
                                            <th style={thStyle}>Date</th>
                                            <th style={thStyle}>Location</th>
                                            <th style={thStyle}>Diagnoses</th>
                                            <th style={thStyle}>Billed</th>
                                            <th style={thStyle}>Paid</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {details.encounters && details.encounters.length > 0 ? (
                                            details.encounters.map((enc, idx) => (
                                                <tr key={idx} style={{ borderTop: '1px solid #e2e8f0' }}>
                                                    <td style={tdStyle}>{formatDate(enc.date)}</td>
                                                    <td style={tdStyle}>{enc.location}</td>
                                                    <td style={tdStyle}>
                                                        {enc.diagnoses && enc.diagnoses.length > 0 ? (
                                                            enc.diagnoses.map((d, i) => (
                                                                <div key={i} style={{ fontSize: '12px', marginBottom: '4px' }}>
                                                                    <span style={{ fontWeight: '500', color: '#0369a1' }}>{d.code}</span>
                                                                    <span style={{ color: '#64748b', marginLeft: '6px' }}>{d.description}</span>
                                                                </div>
                                                            ))
                                                        ) : <span style={{ color: '#94a3b8' }}>None</span>}
                                                    </td>
                                                    <td style={tdStyle}>${enc.totalBilled.toFixed(2)}</td>
                                                    <td style={tdStyle}>${enc.totalPaid.toFixed(2)}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="5" style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>
                                                    No encounter history
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                    </div>
                ) : null}
            </div>
        </div>
    );
};

const sectionTitleStyle = {
    fontSize: '16px', fontWeight: '600', color: '#1e293b',
    marginBottom: '16px', paddingBottom: '8px', borderBottom: '2px solid #f1f5f9'
};

const InfoItem = ({ label, value }) => (
    <div style={{ marginBottom: '8px' }}>
        <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</div>
        <div style={{ fontSize: '14px', color: '#334155', fontWeight: '500' }}>{value || 'N/A'}</div>
    </div>
);

const thStyle = {
    textAlign: 'left', padding: '12px 16px', fontSize: '12px',
    fontWeight: '600', color: '#64748b', textTransform: 'uppercase'
};

const tdStyle = {
    padding: '12px 16px', fontSize: '14px', color: '#334155', verticalAlign: 'top'
};

export default PatientDetailsModal;
