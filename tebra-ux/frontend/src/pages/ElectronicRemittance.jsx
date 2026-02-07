import React, { useState, useEffect } from 'react'
import ERADetailsModal from '../components/ERADetailsModal'

const ElectronicRemittance = () => {
    // State
    const [practices, setPractices] = useState([])
    const [selectedPractice, setSelectedPractice] = useState('All')
    const [eras, setEras] = useState([])
    const [loading, setLoading] = useState(false)
    const [selectedEraId, setSelectedEraId] = useState(null)
    const [page, setPage] = useState(1)
    const [hasMore, setHasMore] = useState(true)
    // Filter State
    const [hideInformational, setHideInformational] = useState(false)
    const [showRejections, setShowRejections] = useState(false)
    const [showDenials, setShowDenials] = useState(false)

    // Practice Selector State
    const [dropdownOpen, setDropdownOpen] = useState(false)
    const [practiceSearchTerm, setPracticeSearchTerm] = useState('')
    const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' })

    // Initial Load: Practices & ERAs
    useEffect(() => {
        fetchPractices()
    }, [])

    // Re-fetch when filters/page change
    useEffect(() => {
        fetchEras()
    }, [selectedPractice, page, sortConfig, hideInformational, showRejections, showDenials])

    const fetchPractices = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/practices/list')
            const data = await res.json()
            setPractices(data)
            // Default to first practice if list not empty, or keep 'All' logic if preferred
            // Matching Practices.jsx behavior usually means selecting one or showing placeholder
            // But here we might want "All Practices" as an option potentially?
            // User requested "identical behavior" to Practices page. 
            // Practices page: Starts with "Choose a practice..." (null selected).
            // Let's stick to that for identical behavior.
            setSelectedPractice(null)
        } catch (err) {
            console.error('Failed to load practices', err)
        }
    }

    const fetchEras = async () => {
        setLoading(true)
        try {
            let url = `http://localhost:8000/api/eras/list?page=${page}&page_size=20&sort_by=${sortConfig.key}&order=${sortConfig.direction}&`

            if (selectedPractice) {
                // The backend expects GUID for 'All' check or specific GUID
                url += `practice_guid=${selectedPractice.locationGuid}&`
            }

            // Filters
            if (hideInformational) url += `hide_informational=true&`
            if (showRejections) url += `show_rejections=true&`
            if (showDenials) url += `show_denials=true&`

            // Search removed as per requirements

            console.log('Fetching ERAs from:', url)
            const res = await fetch(url)
            const data = await res.json()
            console.log('ERAs fetched:', data)
            setEras(data)
            setHasMore(data.length === 20)
        } catch (err) {
            console.error('Failed to load ERAs', err)
        } finally {
            setLoading(false)
        }
    }

    const handlePageChange = (newPage) => {
        if (newPage > 0) setPage(newPage)
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

    const handleSelectPractice = (practice) => {
        console.log('Selected Practice:', practice)
        setSelectedPractice(practice)
        setDropdownOpen(false)
        setPracticeSearchTerm('')
        setPage(1)
    }

    const filteredPractices = practices.filter(p =>
        p.name.toLowerCase().includes(practiceSearchTerm.toLowerCase()) ||
        p.city.toLowerCase().includes(practiceSearchTerm.toLowerCase()) ||
        p.state.toLowerCase().includes(practiceSearchTerm.toLowerCase())
    )

    return (
        <div className="page-container">
            <div className="page-header">
                <div>
                    <h1>Electronic Remittance</h1>
                    <p className="subtitle">View and manage ERA reports across practices</p>
                </div>
            </div>

            {/* Practice Selector Card (Matches Practices.jsx) */}
            <div className="practice-selector-card card">
                <label className="practice-selector-label">Select Practice</label>
                <div className="practice-dropdown-wrapper">
                    <div
                        className="practice-selector-input"
                        onClick={() => setDropdownOpen(!dropdownOpen)}
                    >
                        <div className="practice-selector-display">
                            {selectedPractice ? (
                                <div>
                                    <div className="practice-selector-name">{selectedPractice.name}</div>
                                    <div className="practice-selector-location">
                                        {selectedPractice.city}, {selectedPractice.state}
                                    </div>
                                </div>
                            ) : (
                                <span className="practice-selector-placeholder">Choose a practice...</span>
                            )}
                        </div>
                        <svg className="practice-selector-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>

                    {dropdownOpen && (
                        <>
                            <div className="dropdown-overlay" onClick={() => setDropdownOpen(false)}></div>
                            <div className="practice-dropdown-menu">
                                <div className="practice-dropdown-search">
                                    <svg className="search-icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                    <input
                                        type="text"
                                        placeholder="Search practices..."
                                        value={practiceSearchTerm}
                                        onChange={(e) => setPracticeSearchTerm(e.target.value)}
                                        autoFocus
                                    />
                                </div>
                                <div className="practice-dropdown-list">
                                    {filteredPractices.map((practice) => (
                                        <div
                                            key={practice.locationGuid}
                                            className={`practice-dropdown-item ${selectedPractice?.locationGuid === practice.locationGuid ? 'selected' : ''}`}
                                            onClick={() => handleSelectPractice(practice)}
                                        >
                                            <div className="practice-dropdown-item-name">{practice.name}</div>
                                            <div className="practice-dropdown-item-meta">
                                                {practice.city}, {practice.state} • {practice.eraCount} ERAs
                                            </div>
                                        </div>
                                    ))}
                                    {filteredPractices.length === 0 && (
                                        <div className="practice-dropdown-empty">No practices found</div>
                                    )}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Filters and Table - Always Show */}
            <>
                {/* Filters */}
                <div className="card" style={{ marginBottom: '16px', padding: '16px', display: 'flex', gap: '24px', alignItems: 'center' }}>
                    <div style={{ fontWeight: 600, color: '#334155' }}>Filter by:</div>

                    <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={hideInformational}
                            onChange={(e) => { setHideInformational(e.target.checked); setPage(1); }}
                        />
                        <span>Hide Informational ERAs</span>
                    </label>

                    <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={showRejections}
                            onChange={(e) => { setShowRejections(e.target.checked); setPage(1); }}
                        />
                        <span>Show ERAs with Rejections</span>
                    </label>

                    <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={showDenials}
                            onChange={(e) => { setShowDenials(e.target.checked); setPage(1); }}
                        />
                        <span>Show ERAs with Denials</span>
                    </label>
                </div>

                {/* Table */}
                <div className="card">
                    <div className="table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th onClick={() => handleSort('id')} style={{ cursor: 'pointer' }}>Report ID {getSortIcon('id')}</th>
                                    <th onClick={() => handleSort('date')} style={{ cursor: 'pointer' }}>Received Date {getSortIcon('date')}</th>
                                    {!selectedPractice && <th>Practice</th>}
                                    <th onClick={() => handleSort('payer')} style={{ cursor: 'pointer' }}>Payer {getSortIcon('payer')}</th>
                                    <th>Type</th>
                                    <th onClick={() => handleSort('total_billed')} style={{ cursor: 'pointer' }}>Total Billed {getSortIcon('total_billed')}</th>
                                    <th onClick={() => handleSort('total_paid')} style={{ cursor: 'pointer' }}>Total Paid {getSortIcon('total_paid')}</th>
                                    <th># Claims</th>
                                    <th>Rejected</th>
                                    <th>Denied</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="11" style={{ textAlign: 'center', padding: '20px' }}>Loading...</td></tr>
                                ) : eras.length > 0 ? (
                                    eras.map((era) => (
                                        <tr key={era.id}>
                                            <td>{era.id}</td>
                                            <td>{new Date(era.receivedDate).toLocaleDateString('en-US', { year: '2-digit', month: '2-digit', day: '2-digit' })}</td>
                                            {!selectedPractice && <td>{era.practice}</td>}
                                            <td>{era.payer}</td>
                                            <td>
                                                <span className={`status-badge ${era.type === 'Payment' ? 'paid' : era.type === 'Denial' ? 'denied' : 'neutral'}`}>
                                                    {era.type}
                                                </span>
                                            </td>
                                            <td>${(era.totalBilled || 0).toFixed(2)}</td>
                                            <td>${era.totalPaid.toFixed(2)}</td>
                                            <td>{era.claimCount}</td>
                                            <td>
                                                <span className={`status-badge ${era.rejectedCount > 0 ? 'rejected' : 'neutral'}`}>
                                                    {era.rejectedCount}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`status-badge ${era.deniedCount > 0 ? 'denied' : 'neutral'}`}>
                                                    {era.deniedCount}
                                                </span>
                                            </td>
                                            <td>
                                                <button
                                                    className="icon-button"
                                                    onClick={() => setSelectedEraId(era.id)}
                                                    title="View Details"
                                                >
                                                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="18" height="18">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                                    </svg>
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr><td colSpan="11" style={{ textAlign: 'center', padding: '40px', color: 'var(--slate-500)' }}>No ERAs found.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination Controls */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '16px', gap: '8px', borderTop: '1px solid #eee' }}>
                        <button
                            disabled={page === 1 || loading}
                            onClick={() => handlePageChange(page - 1)}
                            className="secondary-button"
                        >
                            Previous
                        </button>
                        <span style={{ alignSelf: 'center' }}>Page {page}</span>
                        <button
                            disabled={!hasMore || loading}
                            onClick={() => handlePageChange(page + 1)}
                            className="secondary-button"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </>

            {/* Modal */}
            {
                selectedEraId && (
                    <ERADetailsModal
                        eraId={selectedEraId}
                        onClose={() => setSelectedEraId(null)}
                    />
                )
            }
        </div >
    )
}

export default ElectronicRemittance
