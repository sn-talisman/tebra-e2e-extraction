import { useState, useEffect } from 'react'

function Claims() {
    const [claims, setClaims] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // TODO: Replace with actual API call
        // For now, using placeholder data
        setTimeout(() => {
            setClaims([])
            setLoading(false)
        }, 500)
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
            <h1 style={{ marginBottom: '24px' }}>Claims</h1>

            <div className="card">
                <div className="card-header">
                    <div className="card-title">All Claims</div>
                    <div className="card-subtitle">Claim search and management</div>
                </div>

                <div style={{ padding: '20px 0' }}>
                    <p style={{ color: 'var(--slate-600)', marginBottom: '16px' }}>
                        Use the search bar above to find claims by:
                    </p>
                    <ul style={{ color: 'var(--slate-600)', paddingLeft: '24px' }}>
                        <li>Practice name</li>
                        <li>Patient name</li>
                        <li>Claim number</li>
                        <li>Claim status</li>
                    </ul>
                </div>

                <div className="table-container" style={{ marginTop: '24px' }}>
                    <table>
                        <thead>
                            <tr>
                                <th>Claim #</th>
                                <th>Patient</th>
                                <th>Practice</th>
                                <th>Date</th>
                                <th>Amount</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td colSpan="6" style={{ textAlign: 'center', color: 'var(--slate-500)', padding: '40px' }}>
                                    No claims to display. Use the search above to find claims.
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

export default Claims
