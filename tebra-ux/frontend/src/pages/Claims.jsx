import { useState, useEffect } from 'react'
import PaginationControls from '../components/PaginationControls'

function Claims() {
    const [claims, setClaims] = useState([])
    const [loading, setLoading] = useState(true)
    const [page, setPage] = useState(1)
    const [searchTerm, setSearchTerm] = useState('')
    const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' })
    const ITEMS_PER_PAGE = 20

    useEffect(() => {
        fetchClaims()
    }, [page, searchTerm, sortConfig])

    const fetchClaims = async () => {
        setLoading(true)
        try {
            const queryParams = new URLSearchParams({
                page: page,
                page_size: ITEMS_PER_PAGE,
                sort_by: sortConfig.key,
                order: sortConfig.direction
            })

            if (searchTerm) {
                queryParams.append('search', searchTerm)
            }

            const response = await fetch(`http://localhost:8000/api/claims/list?${queryParams}`)
            const data = await response.json()
            setClaims(data)
        } catch (error) {
            console.error('Error fetching claims:', error)
            setClaims([])
        } finally {
            setLoading(false)
        }
    }

    const handleSort = (key) => {
        setSortConfig(current => {
            if (current.key === key) {
                return { key, direction: current.direction === 'asc' ? 'desc' : 'asc' }
            }
            return { key, direction: 'desc' }
        })
        setPage(1)
    }

    const getSortIcon = (key) => {
        if (sortConfig.key !== key) return '↕'
        return sortConfig.direction === 'asc' ? '↑' : '↓'
    }

    // Debounce search input
    useEffect(() => {
        const timer = setTimeout(() => {
            if (page !== 1) setPage(1)
            else fetchClaims()
        }, 500)
        return () => clearTimeout(timer)
    }, [searchTerm])

    return (
        <div>
            <h1 style={{ marginBottom: '24px' }}>Claims</h1>

            <div className="card">
                <div className="card-header">
                    <div className="card-title">All Claims</div>
                    <div className="card-subtitle">Claim search and management</div>
                </div>

                <div style={{ padding: '20px 0' }}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <div className="search-box" style={{ flex: 1, maxWidth: '400px' }}>
                            <svg className="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            <input
                                type="text"
                                placeholder="Search by Claim ID, Patient, Practice, Status..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                    </div>
                </div>

                <div className="table-container" style={{ marginTop: '24px' }}>
                    <table>
                        <thead>
                            <tr>
                                <th>Claim ID</th>
                                <th onClick={() => handleSort('patient')} style={{ cursor: 'pointer' }}>Patient {getSortIcon('patient')}</th>
                                <th onClick={() => handleSort('practice')} style={{ cursor: 'pointer' }}>Practice {getSortIcon('practice')}</th>
                                <th onClick={() => handleSort('date')} style={{ cursor: 'pointer' }}>Date {getSortIcon('date')}</th>
                                <th onClick={() => handleSort('amount')} style={{ cursor: 'pointer' }}>Amount {getSortIcon('amount')}</th>
                                <th onClick={() => handleSort('status')} style={{ cursor: 'pointer' }}>Status {getSortIcon('status')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan="6" style={{ textAlign: 'center', padding: '40px' }}>
                                        <div className="spinner"></div>
                                    </td>
                                </tr>
                            ) : claims.length > 0 ? (
                                claims.map((claim, idx) => (
                                    <tr key={idx}>
                                        <td>{claim.claimId}</td>
                                        <td>{claim.patientName}</td>
                                        <td>{claim.practiceName}</td>
                                        <td>{claim.date !== 'None' ? claim.date : 'N/A'}</td>
                                        <td>${claim.billed.toFixed(2)}</td>
                                        <td>
                                            <span className={`status-badge ${claim.status === 'Paid' ? 'paid' :
                                                    claim.status === 'Denied' || claim.status === 'Rejected' ? 'denied' :
                                                        'pending'
                                                }`}>
                                                {claim.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="6" style={{ textAlign: 'center', color: 'var(--slate-500)', padding: '40px' }}>
                                        No claims found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>

                    <PaginationControls
                        currentPage={page}
                        totalItems={claims.length === ITEMS_PER_PAGE ? (page * ITEMS_PER_PAGE) + 1 : (page - 1) * ITEMS_PER_PAGE + claims.length}
                        itemsPerPage={ITEMS_PER_PAGE}
                        onPageChange={setPage}
                        hasNext={claims.length === ITEMS_PER_PAGE}
                    />
                </div>
            </div>
        </div>
    )
}

export default Claims
