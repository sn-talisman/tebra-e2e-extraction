import { useState, useEffect } from 'react'

function Dashboard() {
    const [metrics, setMetrics] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/dashboard/metrics')
            .then(res => res.json())
            .then(data => {
                setMetrics(data)
                setLoading(false)
            })
            .catch(err => {
                console.error('Failed to load metrics:', err)
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

    return (
        <div>
            <h1 style={{ marginBottom: '24px' }}>Dashboard</h1>

            <div className="grid grid-4">
                <div className="card stat-card">
                    <div className="stat-label">Total Encounters</div>
                    <div className="stat-value">{metrics?.totalEncounters?.toLocaleString() || 0}</div>
                </div>

                <div className="card stat-card">
                    <div className="stat-label">Total Claims</div>
                    <div className="stat-value">{metrics?.totalClaims?.toLocaleString() || 0}</div>
                </div>

                <div className="card stat-card">
                    <div className="stat-label">Total Billed</div>
                    <div className="stat-value">${(metrics?.totalBilled || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                </div>

                <div className="card stat-card">
                    <div className="stat-label">Collection Rate</div>
                    <div className="stat-value">{metrics?.collectionRate || 0}%</div>
                </div>
            </div>

            <div className="grid grid-2" style={{ marginTop: '24px' }}>
                <div className="card">
                    <div className="card-header">
                        <div className="card-title">Financial Overview</div>
                        <div className="card-subtitle">Last 30 days</div>
                    </div>
                    <div className="stat-label">Total Paid</div>
                    <div className="stat-value" style={{ fontSize: '28px' }}>
                        ${(metrics?.totalPaid || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <div className="card-title">Active Practices</div>
                        <div className="card-subtitle">Locations with encounters</div>
                    </div>
                    <div className="stat-value" style={{ fontSize: '28px' }}>
                        {metrics?.practicesCount || 0}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
