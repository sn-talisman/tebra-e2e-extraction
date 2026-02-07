import { useState, useEffect } from 'react'

function Financial() {
    const [summary, setSummary] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/financial/summary')
            .then(res => res.json())
            .then(data => {
                setSummary(data)
                setLoading(false)
            })
            .catch(err => {
                console.error('Failed to load financial summary:', err)
                setLoading(false)
            })
    }, [])

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
                <div className="spinner"></div>
            </div>
        )
    }

    const collectionRate = summary?.totalBilled > 0
        ? (summary.totalPaid / summary.totalBilled * 100).toFixed(2)
        : 0

    return (
        <div>
            <h1 style={{ marginBottom: '24px' }}>Financial Metrics</h1>

            <div className="grid grid-4">
                <div className="card stat-card">
                    <div className="stat-label">Total Billed</div>
                    <div className="stat-value" style={{ fontSize: '24px' }}>
                        ${(summary?.totalBilled || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                </div>

                <div className="card stat-card">
                    <div className="stat-label">Total Paid</div>
                    <div className="stat-value" style={{ fontSize: '24px' }}>
                        ${(summary?.totalPaid || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                </div>

                <div className="card stat-card">
                    <div className="stat-label">Outstanding</div>
                    <div className="stat-value" style={{ fontSize: '24px' }}>
                        ${(summary?.outstanding || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                </div>

                <div className="card stat-card">
                    <div className="stat-label">Collection Rate</div>
                    <div className="stat-value" style={{ fontSize: '24px' }}>
                        {collectionRate}%
                    </div>
                </div>
            </div>

            <div className="card" style={{ marginTop: '24px' }}>
                <div className="card-header">
                    <div className="card-title">Financial Summary</div>
                    <div className="card-subtitle">{summary?.lineCount?.toLocaleString() || 0} claim lines</div>
                </div>
                <p style={{ color: 'var(--slate-600)' }}>
                    Detailed financial analytics and reporting will be available here.
                </p>
            </div>
        </div>
    )
}

export default Financial
