import { useState, useEffect, useRef } from 'react'
import { API_BASE_URL } from '../config'
import { useLocation, useNavigate } from 'react-router-dom'

function Topbar({ title }) {
    const [dropdownOpen, setDropdownOpen] = useState(false)
    const [searchFilter, setSearchFilter] = useState('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState([])
    const [showResults, setShowResults] = useState(false)
    const [loading, setLoading] = useState(false)
    const searchRef = useRef(null)

    const location = useLocation()
    const navigate = useNavigate()

    // Hide search on Electronic Remittance page - Wait, requirement says "Searching for Status should open up Electronic Remittance"
    // So we should probably allow search everywhere, but maybe the prompt meant specific context?
    // "Please do not make any changes to other pages which is working functionality"
    // The previous code hid search on /eras. I should probably keep it hidden if that was the design, 
    // BUT the requirement says "Searching for Status - should open up the Electronic Remittance".
    // If I hide the search bar on /eras, I can't search for status while on /eras? 
    // Actually, usually global search is available everywhere. 
    // The existing code: `const showSearch = location.pathname !== '/eras'`
    // I will respect the existing "hide on eras" logic for now unless it blocks the flow, 
    // but the user requirement implies using global search *to go to* ERAs.
    // If I'm on Dashboard, I search status -> go to ERAs.
    // UseRef to click outside to close results
    useEffect(() => {
        function handleClickOutside(event) {
            if (searchRef.current && !searchRef.current.contains(event.target)) {
                setShowResults(false)
            }
        }
        document.addEventListener("mousedown", handleClickOutside)
        return () => {
            document.removeEventListener("mousedown", handleClickOutside)
        }
    }, [searchRef])

    const showSearch = location.pathname !== '/eras'

    const toggleDropdown = () => {
        setDropdownOpen(!dropdownOpen)
    }

    const handleLogout = () => {
        console.log('Logout clicked')
    }

    const handleSearch = async (e) => {
        e.preventDefault()
        if (!searchQuery.trim()) return

        setLoading(true)
        setShowResults(true)
        try {
            // Map frontend filter values to backend expected values
            // Frontend: all, practice, patient, claim_number, status
            // Backend types: practice, patient, claim, status
            let typeParam = ''
            if (searchFilter === 'practice') typeParam = '&type=practice'
            if (searchFilter === 'patient') typeParam = '&type=patient'
            if (searchFilter === 'claim_number') typeParam = '&type=claim'
            if (searchFilter === 'status') typeParam = '&type=status'

            const res = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(searchQuery)}${typeParam}`)
            const data = await res.json()
            setSearchResults(data)
        } catch (error) {
            console.error('Search error:', error)
            setSearchResults([])
        } finally {
            setLoading(false)
        }
    }

    const handleResultClick = (result) => {
        setShowResults(false)
        setSearchQuery('')

        if (result.type === 'practice') {
            navigate(`/practices?practice=${result.id}`)
        } else if (result.type === 'patient') {
            navigate(`/practices?practice=${result.metadata.practice_guid}&tab=patients&patient=${result.id}`)
        } else if (result.type === 'claim') {
            // For claims, we use claim_ref_id for the modal
            navigate(`/practices?practice=${result.metadata.practice_guid}&tab=claims&claimRef=${result.metadata.claim_ref_id}`)
        } else if (result.type === 'status') {
            navigate(`/eras?status=${result.id}`)
        }
    }

    return (
        <div className="topbar">
            {/* Search Bar */}
            <div className="topbar-search" style={{ visibility: showSearch ? 'visible' : 'hidden', position: 'relative' }} ref={searchRef}>
                <form onSubmit={handleSearch} className="search-form">
                    <div className="search-filter-wrapper">
                        <select
                            className="search-filter"
                            value={searchFilter}
                            onChange={(e) => setSearchFilter(e.target.value)}
                        >
                            <option value="all">All</option>
                            <option value="practice">Practice</option>
                            <option value="patient">Patient</option>
                            <option value="claim_number">Claim #</option>
                            <option value="status">Status</option>
                        </select>
                    </div>
                    <div className="search-input-wrapper">
                        <svg className="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <input
                            type="text"
                            className="search-input"
                            placeholder={`Search ${searchFilter === 'all' ? 'everything' : searchFilter.replace('_', ' ')}...`}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </form>

                {/* Search Results Dropdown */}
                {showResults && (
                    <div className="search-results-dropdown" style={{
                        position: 'absolute',
                        top: '100%',
                        left: 0,
                        right: 0,
                        backgroundColor: 'white',
                        borderRadius: '8px',
                        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                        marginTop: '8px',
                        zIndex: 50,
                        maxHeight: '400px',
                        overflowY: 'auto',
                        border: '1px solid #e2e8f0'
                    }}>
                        {loading ? (
                            <div style={{ padding: '16px', textAlign: 'center', color: '#64748b' }}>Searching...</div>
                        ) : searchResults.length > 0 ? (
                            searchResults.map((result) => (
                                <div
                                    key={`${result.type}-${result.id}`}
                                    onClick={() => handleResultClick(result)}
                                    style={{
                                        padding: '12px 16px',
                                        cursor: 'pointer',
                                        borderBottom: '1px solid #f1f5f9',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '12px'
                                    }}
                                    className="search-result-item"
                                    onMouseEnter={(e) => e.target.closest('.search-result-item').style.backgroundColor = '#f8fafc'}
                                    onMouseLeave={(e) => e.target.closest('.search-result-item').style.backgroundColor = 'white'}
                                >
                                    <div style={{
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        width: '32px', height: '32px', borderRadius: '50%',
                                        backgroundColor: result.type === 'practice' ? '#e0f2fe' :
                                            result.type === 'patient' ? '#dcfce7' :
                                                result.type === 'claim' ? '#ffedd5' : '#f3e8ff',
                                        color: result.type === 'practice' ? '#0369a1' :
                                            result.type === 'patient' ? '#15803d' :
                                                result.type === 'claim' ? '#c2410c' : '#7e22ce',
                                        fontSize: '14px'
                                    }}>
                                        {result.type === 'practice' && '🏥'}
                                        {result.type === 'patient' && '👤'}
                                        {result.type === 'claim' && '📄'}
                                        {result.type === 'status' && '🏷️'}
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: '500', color: '#1e293b' }}>{result.label}</div>
                                        {result.subtext && (
                                            <div style={{ fontSize: '12px', color: '#64748b' }}>{result.subtext}</div>
                                        )}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div style={{ padding: '16px', textAlign: 'center', color: '#64748b' }}>No results found</div>
                        )}
                    </div>
                )}
            </div>

            <div className="topbar-actions">
                <div className="topbar-user" onClick={toggleDropdown}>
                    <div className="topbar-user-info">
                        <div className="topbar-user-name">Admin User</div>
                        <div className="topbar-user-role">Administrator</div>
                    </div>
                    <div className="topbar-avatar">AD</div>
                    <svg className="topbar-dropdown-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>

                {dropdownOpen && (
                    <>
                        <div className="dropdown-overlay" onClick={toggleDropdown}></div>
                        <div className="topbar-dropdown">
                            <div className="topbar-dropdown-header">
                                <div className="topbar-avatar-large">AD</div>
                                <div>
                                    <div className="topbar-dropdown-name">Admin User</div>
                                    <div className="topbar-dropdown-email">admin@talismansolutions.com</div>
                                </div>
                            </div>
                            <div className="topbar-dropdown-divider"></div>
                            <a href="#" className="topbar-dropdown-item">
                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                                <span>My Profile</span>
                            </a>
                            <a href="#" className="topbar-dropdown-item">
                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                </svg>
                                <span>Settings</span>
                            </a>
                            <a href="#" className="topbar-dropdown-item">
                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>Help & Support</span>
                            </a>
                            <div className="topbar-dropdown-divider"></div>
                            <a href="#" className="topbar-dropdown-item" onClick={handleLogout}>
                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                </svg>
                                <span>Logout</span>
                            </a>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}

export default Topbar
