import { useState } from 'react'
import { useLocation } from 'react-router-dom'

function Topbar({ title }) {
    const [dropdownOpen, setDropdownOpen] = useState(false)
    const [searchFilter, setSearchFilter] = useState('all')
    const [searchQuery, setSearchQuery] = useState('')
    const location = useLocation()

    // Hide search on Electronic Remittance page
    const showSearch = location.pathname !== '/eras'

    const toggleDropdown = () => {
        setDropdownOpen(!dropdownOpen)
    }

    const handleLogout = () => {
        console.log('Logout clicked')
        // Add logout logic here
    }

    const handleSearch = (e) => {
        e.preventDefault()
        console.log('Search:', { filter: searchFilter, query: searchQuery })
        // Add search logic here
    }

    return (
        <div className="topbar">
            {/* Search Bar */}
            <div className="topbar-search" style={{ visibility: showSearch ? 'visible' : 'hidden' }}>
                <form onSubmit={handleSearch} className="search-form">
                    <div className="search-filter-wrapper">
                        <select
                            className="search-filter"
                            value={searchFilter}
                            onChange={(e) => setSearchFilter(e.target.value)}
                        >
                            <option value="all">All Claims</option>
                            <option value="practice">By Practice</option>
                            <option value="patient">By Patient</option>
                            <option value="claim_number">By Claim #</option>
                            <option value="status">By Status</option>
                        </select>
                    </div>
                    <div className="search-input-wrapper">
                        <svg className="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <input
                            type="text"
                            className="search-input"
                            placeholder={`Search ${searchFilter === 'all' ? 'claims' : searchFilter.replace('_', ' ')}...`}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </form>
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
