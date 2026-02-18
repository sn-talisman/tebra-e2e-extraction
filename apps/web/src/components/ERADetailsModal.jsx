import React, { useState, useEffect } from 'react'
import '../index.css'
import { getAdjustmentDesc } from '../utils/carc_codes'
import { API_BASE_URL } from '../config'

const ERADetailsModal = ({ eraId, onClose }) => {
    const [details, setDetails] = useState(null)
    const [loading, setLoading] = useState(true)
    const [filterType, setFilterType] = useState('all') // 'all', 'rejections', 'denials'

    useEffect(() => {
        if (eraId) fetchDetails()
    }, [eraId])

    const fetchDetails = async () => {
        setLoading(true)
        try {
            const res = await fetch(`${API_BASE_URL}/api/eras/${eraId}/details`)
            const data = await res.json()
            setDetails(data)
        } catch (err) {
            console.error("Failed to load ERA details", err)
        } finally {
            setLoading(false)
        }
    }

    if (!eraId) return null

    // Helper to format adjustments
    const renderAdjustments = (adjStr) => {
        if (!adjStr) return '-'
        // Expected format: "CO-45: $10.00, PR-3: $5.00"
        return adjStr.split(', ').map((adj, i) => {
            const [code, amt] = adj.split(':')
            const desc = getAdjustmentDesc(code.trim())
            return (
                <div key={i} style={{ marginBottom: '4px' }}>
                    <span style={{ fontWeight: '500', color: '#d9534f' }}>{code}</span>
                    {amt && <span>: {amt}</span>}
                    {desc && <div style={{ fontSize: '0.8em', color: '#666', fontStyle: 'italic' }}>{desc}</div>}
                </div>
            )
        })
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content large" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>ERA Report Details</h2>
                    <button className="close-button" onClick={onClose}>&times;</button>
                </div>

                <div className="modal-body">
                    {loading ? (
                        <div style={{ padding: '40px', textAlign: 'center' }}>Loading details...</div>
                    ) : details ? (
                        <>
                            {/* Header Section - Split Layout */}
                            <div className="patient-header-card" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                                <div className="section">
                                    <h4 style={{ margin: '0 0 12px 0', borderBottom: '2px solid #e2e8f0', paddingBottom: '8px', color: '#1e293b', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Payer Information</h4>
                                    <div className="info-group">
                                        <label>Payer Name</label>
                                        <div className="value">{details.payer}</div>
                                    </div>
                                    <div className="info-group">
                                        <label>Check Number</label>
                                        <div className="value">{details.checkNumber}</div>
                                    </div>
                                    <div className="info-group">
                                        <label>Check Date</label>
                                        <div className="value">{details.checkDate}</div>
                                    </div>
                                </div>
                                <div className="section">
                                    <h4 style={{ margin: '0 0 12px 0', borderBottom: '2px solid #e2e8f0', paddingBottom: '8px', color: '#1e293b', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Practice & Payment</h4>
                                    <div className="info-group">
                                        <label>Practice</label>
                                        <div className="value">{details.practice}</div>
                                    </div>
                                    <div className="info-group">
                                        <label>Received Date</label>
                                        <div className="value">{details.receivedDate}</div>
                                    </div>
                                    <div className="info-group">
                                        <label>Total Paid</label>
                                        <div className="value highlight">${details.totalPaid.toFixed(2)}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Claim Summary Counts */}
                            {details.summary && (
                                <div className="card" style={{ marginBottom: '24px', padding: '16px', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                                    <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', textTransform: 'uppercase', color: '#64748b' }}>Claim Summary</h4>
                                    <div style={{ display: 'flex', gap: '32px' }}>
                                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                                            <span style={{ fontSize: '12px', color: '#64748b' }}>Paid</span>
                                            <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#22c55e' }}>{details.summary.paid}</span>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                                            <span style={{ fontSize: '12px', color: '#64748b' }}>Rejected</span>
                                            <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#ef4444' }}>{details.summary.rejected}</span>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                                            <span style={{ fontSize: '12px', color: '#64748b' }}>Denied</span>
                                            <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#dc2626' }}>{details.summary.denied}</span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Claim Bundles */}
                            {(() => {
                                const filteredBundles = details.bundles.filter(b => {
                                    if (filterType === 'all') return true
                                    if (filterType === 'rejections') {
                                        return b.claims.some(c => c.status === 'Rejected' || c.previouslyRejected)
                                    }
                                    if (filterType === 'denials') {
                                        return b.claims.some(c => c.status === 'Denied')
                                    }
                                    return true
                                })

                                return (
                                    <>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                            <h3 style={{ margin: 0 }}>Claim Bundles ({filteredBundles.length})</h3>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <label style={{ fontSize: '14px', color: '#64748b' }}>Show:</label>
                                                <select
                                                    value={filterType}
                                                    onChange={(e) => setFilterType(e.target.value)}
                                                    style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                                                >
                                                    <option value="all">All Bundles</option>
                                                    <option value="rejections">With Rejections</option>
                                                    <option value="denials">With Denials</option>
                                                </select>
                                            </div>
                                        </div>

                                        {details.bundles.length === 0 && details.claimCount > 0 && (
                                            <div style={{ padding: '12px', marginBottom: '16px', background: '#fff3cd', color: '#856404', borderRadius: '4px', border: '1px solid #ffeeba' }}>
                                                <strong>Note:</strong> This report indicates {details.claimCount} claims processed, but no detailed payment bundles were found.
                                                This typically occurs for fully denied claims or informational-only reports with $0.00 payment.
                                            </div>
                                        )}

                                        <div className="bundles-list">
                                            {filteredBundles.map((bundle) => (
                                                <div key={bundle.referenceId} className="bundle-card" style={{ border: '1px solid #eee', borderRadius: '8px', marginBottom: '16px', padding: '12px' }}>
                                                    <div className="bundle-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', borderBottom: '1px solid #f0f0f0', paddingBottom: '8px' }}>
                                                        <span><strong>Ref ID:</strong> {bundle.referenceId}</span>
                                                        <span><strong>Patient:</strong> {bundle.claims[0]?.patient || 'Unknown'}</span>
                                                        <span><strong>Paid:</strong> ${bundle.bundlePaid.toFixed(2)}</span>
                                                    </div>

                                                    <table className="data-table small">
                                                        <thead>
                                                            <tr>
                                                                <th>Date</th>
                                                                <th>Provider</th>
                                                                <th>Proc Code</th>
                                                                <th style={{ width: '25%' }}>Diagnoses</th>
                                                                <th style={{ width: '25%' }}>Adjustments (CARC/RARC)</th>
                                                                <th>Status</th>
                                                                <th>Billed</th>
                                                                <th>Paid</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {bundle.claims.map((claim, idx) => (
                                                                <tr key={idx}>
                                                                    <td>{claim.date}</td>
                                                                    <td>{claim.provider}</td>
                                                                    <td>{claim.procCode}</td>
                                                                    <td style={{ fontSize: '0.85em', color: '#555' }}>
                                                                        {claim.diagnoses ? claim.diagnoses : '-'}
                                                                    </td>
                                                                    <td style={{ fontSize: '0.85em' }}>
                                                                        {claim.adjustmentDescriptions ? (
                                                                            <div style={{ whiteSpace: 'pre-wrap', color: '#d32f2f' }}>
                                                                                {claim.adjustmentDescriptions}
                                                                            </div>
                                                                        ) : (
                                                                            renderAdjustments(claim.adjustments)
                                                                        )}
                                                                    </td>
                                                                    <td>
                                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                                                            <span className={`status-badge ${claim.status === 'Paid' ? 'paid' : (claim.status === 'Denied' || claim.status === 'Rejected') ? 'denied' : 'neutral'}`}>
                                                                                {claim.status}
                                                                            </span>
                                                                            {claim.previouslyRejected && (
                                                                                <span style={{ fontSize: '10px', color: '#ef4444', fontWeight: '600' }}>
                                                                                    (Pre-Reject)
                                                                                </span>
                                                                            )}
                                                                        </div>
                                                                    </td>
                                                                    <td>${claim.billed.toFixed(2)}</td>
                                                                    <td>${claim.paid.toFixed(2)}</td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            ))}
                                            {filteredBundles.length === 0 && (
                                                <div style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>
                                                    No bundles match the selected filter.
                                                </div>
                                            )}
                                        </div>
                                    </>
                                )
                            })()}
                        </>
                    ) : (
                        <div>Error loading data.</div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default ERADetailsModal
