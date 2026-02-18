import { useState, useRef, useEffect } from 'react'

export default function PracticeSelector({
    practices,
    selectedPractice,
    onSelect,
    placeholder = "Choose a practice..."
}) {
    const [dropdownOpen, setDropdownOpen] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const searchInputRef = useRef(null)

    useEffect(() => {
        if (dropdownOpen && searchInputRef.current) {
            searchInputRef.current.focus()
        }
    }, [dropdownOpen])

    const filteredPractices = practices.filter(p => {
        const name = p.name || p.practice_name || ''
        const city = p.city || ''
        const state = p.state || ''
        const search = searchTerm.toLowerCase()
        return name.toLowerCase().includes(search) ||
            city.toLowerCase().includes(search) ||
            state.toLowerCase().includes(search)
    })

    const handleSelect = (practice) => {
        onSelect(practice)
        setDropdownOpen(false)
        setSearchTerm('')
    }

    return (
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
                                <div className="practice-selector-name">{selectedPractice.name || selectedPractice.practice_name}</div>
                                {(selectedPractice.city || selectedPractice.state) && (
                                    <div className="practice-selector-location">
                                        {selectedPractice.city}{selectedPractice.city && selectedPractice.state ? ', ' : ''}{selectedPractice.state}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <span className="practice-selector-placeholder">{placeholder}</span>
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
                                    ref={searchInputRef}
                                    type="text"
                                    placeholder="Search practices..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                            <div className="practice-dropdown-list">
                                <div
                                    className={`practice-dropdown-item ${!selectedPractice ? 'selected' : ''}`}
                                    onClick={() => handleSelect(null)}
                                >
                                    <div className="practice-dropdown-item-name">All Practices (Executive Summary)</div>
                                    <div className="practice-dropdown-item-meta">View aggregate performance across all practices</div>
                                </div>
                                {filteredPractices.map((practice) => (
                                    <div
                                        key={practice.locationGuid || practice.practice_id}
                                        className={`practice-dropdown-item ${selectedPractice?.locationGuid === practice.locationGuid || selectedPractice?.practice_id === practice.practice_id ? 'selected' : ''}`}
                                        onClick={() => handleSelect(practice)}
                                    >
                                        <div className="practice-dropdown-item-name">{practice.name || practice.practice_name}</div>
                                        {(practice.city || practice.state) && (
                                            <div className="practice-dropdown-item-meta">
                                                {practice.city}{practice.city && practice.state ? ', ' : ''}{practice.state}
                                            </div>
                                        )}
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
    )
}
