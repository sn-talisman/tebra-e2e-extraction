import { useState, useEffect } from 'react'
import Topbar from '../components/Topbar'
import Sidebar from '../components/Sidebar'
import PatientDetailsModal from '../components/PatientDetailsModal'
import EncounterDetailsModal from '../components/EncounterDetailsModal'
import ClaimDetailsModal from '../components/ClaimDetailsModal'
import PaginationControls from '../components/PaginationControls'
import {
    LineChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart
} from 'recharts'

function Practices() {
    const [practices, setPractices] = useState([])
    const [selectedPractice, setSelectedPractice] = useState(null)
    const [activeTab, setActiveTab] = useState('patients')
    const [searchTerm, setSearchTerm] = useState('')
    const [loading, setLoading] = useState(true)
    const [dropdownOpen, setDropdownOpen] = useState(false)
    const [showPaidOnly, setShowPaidOnly] = useState(false)

    // Tab data states
    const [patients, setPatients] = useState([])
    const [encounters, setEncounters] = useState([])
    const [claims, setClaims] = useState([])

    // Patient details modal
    const [showPatientModal, setShowPatientModal] = useState(false)
    const [selectedPatientGuid, setSelectedPatientGuid] = useState(null)
    const [financialMetrics, setFinancialMetrics] = useState(null)
    const [loadingMetrics, setLoadingMetrics] = useState(false)

    // Encounter details modal
    const [showEncounterModal, setShowEncounterModal] = useState(false)
    const [selectedEncounterId, setSelectedEncounterId] = useState(null)

    // Claim details modal
    const [showClaimModal, setShowClaimModal] = useState(false)
    const [selectedClaimRefId, setSelectedClaimRefId] = useState(null)

    // Pagination State
    const [patientsPage, setPatientsPage] = useState(1)
    const [encountersPage, setEncountersPage] = useState(1)
    const [claimsPage, setClaimsPage] = useState(1)
    const ITEMS_PER_PAGE = 10

    useEffect(() => {
        fetchPractices()
    }, [])

    // Handle URL Params for Deep Linking
    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const practiceGuid = params.get('practice')
        const tab = params.get('tab')
        const patientGuid = params.get('patient')
        const claimRef = params.get('claimRef')

        if (practices.length > 0 && practiceGuid) {
            const practice = practices.find(p => p.locationGuid === practiceGuid || p.practiceGuid === practiceGuid)
            if (practice) {
                setSelectedPractice(practice)
                if (tab) setActiveTab(tab)

                // Open Modals if params exist
                if (patientGuid) {
                    handleViewPatientDetails(patientGuid)
                }
                if (claimRef) {
                    handleViewClaim(claimRef)
                }
            }
        }
    }, [practices, window.location.search]) // Re-run when practices load or URL changes

    useEffect(() => {
        if (selectedPractice) {
            fetchTabData()
        }
    }, [selectedPractice, activeTab, showPaidOnly])

    const fetchPractices = async () => {
        try {
            const response = await fetch('/api/practices/list')
            const data = await response.json()
            setPractices(data)
            setLoading(false)
        } catch (error) {
            console.error('Error fetching practices:', error)
            setLoading(false)
        }
    }

    const fetchTabData = async () => {
        if (!selectedPractice) return

        try {
            if (activeTab === 'patients') {
                const response = await fetch(`/api/practices/${selectedPractice.locationGuid}/patients`)
                const data = await response.json()
                setPatients(data)
            } else if (activeTab === 'encounters') {
                const response = await fetch(`/api/practices/${selectedPractice.locationGuid}/encounters`)
                const data = await response.json()
                setEncounters(data)
            } else if (activeTab === 'claims') {
                const url = `/api/practices/${selectedPractice.locationGuid}/claims${showPaidOnly ? '?paid_only=true' : ''}`
                const response = await fetch(url)
                const data = await response.json()
                setClaims(data)
            }
        } catch (error) {
            console.error('Error fetching tab data:', error)
        }
    }

    const filteredPractices = practices.filter(p =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.state.toLowerCase().includes(searchTerm.toLowerCase())
    )

    const handleSelectPractice = (practice) => {
        setSelectedPractice(practice)
        setDropdownOpen(false)
        setSearchTerm('')
    }

    const handleViewPatientDetails = (patientGuid) => {
        setSelectedPatientGuid(patientGuid)
        setShowPatientModal(true)
    }

    const closePatientModal = () => {
        setShowPatientModal(false)
        setSelectedPatientGuid(null)
    }

    const handleViewEncounter = (encounterId) => {
        setSelectedEncounterId(encounterId)
        setShowEncounterModal(true)
    }

    const handleViewClaim = (claimRefId) => {
        setSelectedClaimRefId(claimRefId)
        setShowClaimModal(true)
    }

    const fetchFinancialMetrics = async (practiceGuid) => {
        setLoadingMetrics(true)
        try {
            const response = await fetch(`http://localhost:8000/api/practices/${practiceGuid}/financial-metrics`)
            const data = await response.json()
            setFinancialMetrics(data)
        } catch (error) {
            console.error('Error fetching financial metrics:', error)
        } finally {
            setLoadingMetrics(false)
        }
    }

    const formatDate = (dateString) => {
        if (!dateString || dateString === 'N/A') return 'N/A'
        const date = new Date(dateString)
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const year = String(date.getFullYear()).slice(-2)
        return `${month}/${day}/${year}`
    }

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
                <div className="spinner"></div>
            </div>
        )
    }

    return (
        <div>
            <h1 style={{ marginBottom: '24px' }}>Practice Management</h1>

            {/* Searchable Practice Dropdown */}
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
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
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
                                                {practice.city}, {practice.state} • {practice.encounterCount} encounters
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

            {/* Tabs Section */}
            {selectedPractice && (
                <div className="card" style={{ marginTop: '24px' }}>
                    <div className="tabs">
                        <button
                            className={`tab ${activeTab === 'patients' ? 'active' : ''}`}
                            onClick={() => setActiveTab('patients')}
                        >
                            Patients
                        </button>
                        <button
                            className={`tab ${activeTab === 'encounters' ? 'active' : ''}`}
                            onClick={() => setActiveTab('encounters')}
                        >
                            Encounters
                        </button>
                        <button
                            className={`tab ${activeTab === 'claims' ? 'active' : ''}`}
                            onClick={() => setActiveTab('claims')}
                        >
                            Claims
                        </button>
                        <button
                            className={`tab ${activeTab === 'financial' ? 'active' : ''}`}
                            onClick={async () => {
                                setActiveTab('financial')
                                if (selectedPractice && !financialMetrics) {
                                    await fetchFinancialMetrics(selectedPractice.locationGuid)
                                }
                            }}
                        >
                            Financial Metrics
                        </button>
                    </div>

                    <div className="tab-content">
                        {activeTab === 'patients' && (
                            <div>
                                <h3>Patients at {selectedPractice.name}</h3>
                                <div className="table-container" style={{ marginTop: '16px' }}>
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Patient Name</th>
                                                <th>Patient ID</th>
                                                <th>Encounters</th>
                                                <th>Last Visit</th>
                                                <th style={{ width: '80px', textAlign: 'center' }}>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {patients.length > 0 ? (
                                                patients
                                                    .filter(p => !selectedPatientGuid || p.patientGuid === selectedPatientGuid)
                                                    .slice((patientsPage - 1) * ITEMS_PER_PAGE, patientsPage * ITEMS_PER_PAGE)
                                                    .map((patient, idx) => (
                                                        <tr key={idx} style={{ backgroundColor: selectedPatientGuid === patient.patientGuid ? '#f0fdf4' : 'inherit' }}>
                                                            <td>{patient.name}</td>
                                                            <td>{patient.patientId}</td>
                                                            <td>{patient.encounterCount}</td>
                                                            <td>{patient.lastVisit}</td>
                                                            <td style={{ textAlign: 'center' }}>
                                                                <button
                                                                    className="icon-button"
                                                                    onClick={() => handleViewPatientDetails(patient.patientGuid)}
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
                                                <tr>
                                                    <td colSpan="5" style={{ textAlign: 'center', padding: '40px' }}>
                                                        Loading patients...
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                    <PaginationControls
                                        currentPage={patientsPage}
                                        totalItems={selectedPatientGuid ? 1 : patients.length}
                                        itemsPerPage={ITEMS_PER_PAGE}
                                        onPageChange={setPatientsPage}
                                    />
                                </div>
                            </div>
                        )}

                        {activeTab === 'encounters' && (
                            <div>
                                <h3>Encounters at {selectedPractice.name}</h3>
                                <div className="table-container" style={{ marginTop: '16px' }}>
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Date</th>
                                                <th>Patient</th>
                                                <th>Provider</th>
                                                <th>Status</th>
                                                <th style={{ width: '80px', textAlign: 'center' }}>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {encounters.length > 0 ? (
                                                encounters.slice((encountersPage - 1) * ITEMS_PER_PAGE, encountersPage * ITEMS_PER_PAGE).map((enc, idx) => (
                                                    <tr key={idx}>
                                                        <td>{enc.date}</td>
                                                        <td>{enc.patientName}</td>
                                                        <td>{enc.providerName}</td>
                                                        <td>
                                                            <span className={`status-badge ${enc.status?.toLowerCase() || 'pending'}`}>
                                                                {enc.status || 'Pending'}
                                                            </span>
                                                        </td>
                                                        <td style={{ textAlign: 'center' }}>
                                                            <button
                                                                className="icon-button"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    handleViewEncounter(enc.encounterId);
                                                                }}
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
                                                <tr>
                                                    <td colSpan="6" style={{ textAlign: 'center', padding: '40px' }}>
                                                        Loading encounters...
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                    <PaginationControls
                                        currentPage={encountersPage}
                                        totalItems={encounters.length}
                                        itemsPerPage={ITEMS_PER_PAGE}
                                        onPageChange={setEncountersPage}
                                    />
                                </div>
                            </div>
                        )}

                        {activeTab === 'claims' && (
                            <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <h3>Claims for {selectedPractice.name}</h3>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: '#475569', cursor: 'pointer' }}>
                                        <input
                                            type="checkbox"
                                            checked={showPaidOnly}
                                            onChange={(e) => setShowPaidOnly(e.target.checked)}
                                            style={{ cursor: 'pointer' }}
                                        />
                                        Show only paid claims
                                    </label>
                                </div>
                                <div className="table-container" style={{ marginTop: '16px' }}>
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Claim ID</th>
                                                <th>Date</th>
                                                <th>Patient</th>
                                                <th>Billed</th>
                                                <th>Paid</th>
                                                <th>Status</th>
                                                <th style={{ width: '80px', textAlign: 'center' }}>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {claims.length > 0 ? (
                                                claims
                                                    .filter(c => !selectedClaimRefId || c.claimReferenceId === selectedClaimRefId)
                                                    .slice((claimsPage - 1) * ITEMS_PER_PAGE, claimsPage * ITEMS_PER_PAGE)
                                                    .map((claim, idx) => (
                                                        <tr key={idx} style={{ backgroundColor: selectedClaimRefId === claim.claimReferenceId ? '#fff7ed' : 'inherit' }}>
                                                            <td>{claim.claimId}</td>
                                                            <td>{claim.date}</td>
                                                            <td>{claim.patientName}</td>
                                                            <td>${claim.billed.toFixed(2)}</td>
                                                            <td>${claim.paid.toFixed(2)}</td>
                                                            <td>
                                                                <span className={`status-badge ${claim.status === 'Paid' ? 'paid' :
                                                                    claim.status === 'Denied' || claim.status === 'Rejected' ? 'denied' :
                                                                        'pending'
                                                                    }`}>
                                                                    {claim.status}
                                                                </span>
                                                            </td>
                                                            <td style={{ textAlign: 'center' }}>
                                                                {claim.claimReferenceId && (
                                                                    <button
                                                                        className="icon-button"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            handleViewClaim(claim.claimReferenceId);
                                                                        }}
                                                                        title="View Details"
                                                                    >
                                                                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="18" height="18">
                                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                                                        </svg>
                                                                    </button>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    ))
                                            ) : (
                                                <tr>
                                                    <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: 'var(--slate-500)' }}>
                                                        No claims found for this practice
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                    <PaginationControls
                                        currentPage={claimsPage}
                                        totalItems={selectedClaimRefId ? 1 : claims.length}
                                        itemsPerPage={ITEMS_PER_PAGE}
                                        onPageChange={setClaimsPage}
                                    />
                                </div>
                            </div>
                        )}


                        {/* Financial Metrics Tab */}
                        {activeTab === 'financial' && (
                            <div>
                                {loadingMetrics ? (
                                    <div style={{ padding: '40px', textAlign: 'center' }}>
                                        <div className="spinner"></div>
                                    </div>
                                ) : financialMetrics ? (
                                    <div>
                                        {/* Metrics Cards Grid */}
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '32px' }}>
                                            {/* Days in AR Card */}
                                            <div className="metric-card" style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid var(--slate-200)' }}>
                                                <div style={{ fontSize: '13px', color: 'var(--slate-600)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>Days in A/R</div>
                                                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
                                                    <span style={{ fontSize: '32px', fontWeight: '700', color: 'var(--slate-800)' }}>
                                                        {financialMetrics.metrics.daysInAR.value !== null ? financialMetrics.metrics.daysInAR.value : 'N/A'}
                                                    </span>
                                                    {financialMetrics.metrics.daysInAR.trend !== null && (
                                                        <span style={{ fontSize: '14px', color: financialMetrics.metrics.daysInAR.trend > 0 ? '#ef4444' : '#22c55e' }}>
                                                            {financialMetrics.metrics.daysInAR.trend > 0 ? '↑' : '↓'} {Math.abs(financialMetrics.metrics.daysInAR.trend)}
                                                        </span>
                                                    )}
                                                </div>
                                                <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginBottom: '16px' }}>Industry benchmark: 30-40 days</div>
                                                {financialMetrics.metrics.daysInAR.performance && (
                                                    <div className={`performance-badge ${financialMetrics.metrics.daysInAR.performance}`}>
                                                        {financialMetrics.metrics.daysInAR.performance}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Net Collection Rate Card */}
                                            <div className="metric-card" style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid var(--slate-200)' }}>
                                                <div style={{ fontSize: '13px', color: 'var(--slate-600)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>Net Collection Rate</div>
                                                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
                                                    <span style={{ fontSize: '32px', fontWeight: '700', color: 'var(--slate-800)' }}>
                                                        {financialMetrics.metrics.netCollectionRate.value !== null ? `${financialMetrics.metrics.netCollectionRate.value}%` : 'N/A'}
                                                    </span>
                                                    {financialMetrics.metrics.netCollectionRate.trend !== null && (
                                                        <span style={{ fontSize: '14px', color: financialMetrics.metrics.netCollectionRate.trend > 0 ? '#22c55e' : '#ef4444' }}>
                                                            {financialMetrics.metrics.netCollectionRate.trend > 0 ? '↑' : '↓'} {Math.abs(financialMetrics.metrics.netCollectionRate.trend)}%
                                                        </span>
                                                    )}
                                                </div>
                                                <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginBottom: '16px' }}>Industry benchmark: 96-97%</div>
                                                {financialMetrics.metrics.netCollectionRate.performance && (
                                                    <div className={`performance-badge ${financialMetrics.metrics.netCollectionRate.performance}`}>
                                                        {financialMetrics.metrics.netCollectionRate.performance}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Denial Rate Card */}
                                            <div className="metric-card" style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid var(--slate-200)' }}>
                                                <div style={{ fontSize: '13px', color: 'var(--slate-600)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>Denial Rate</div>
                                                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
                                                    <span style={{ fontSize: '32px', fontWeight: '700', color: 'var(--slate-800)' }}>
                                                        {financialMetrics.metrics.denialRate.value !== null ? `${financialMetrics.metrics.denialRate.value}%` : 'N/A'}
                                                    </span>
                                                    {financialMetrics.metrics.denialRate.trend !== null && (
                                                        <span style={{ fontSize: '14px', color: financialMetrics.metrics.denialRate.trend > 0 ? '#ef4444' : '#22c55e' }}>
                                                            {financialMetrics.metrics.denialRate.trend > 0 ? '↑' : '↓'} {Math.abs(financialMetrics.metrics.denialRate.trend)}%
                                                        </span>
                                                    )}
                                                </div>
                                                <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginBottom: '16px' }}>Industry target: &lt;5%</div>
                                                {financialMetrics.metrics.denialRate.performance && (
                                                    <div className={`performance-badge ${financialMetrics.metrics.denialRate.performance}`}>
                                                        {financialMetrics.metrics.denialRate.performance}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Patient Collection Rate Card */}
                                            <div className="metric-card" style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid var(--slate-200)' }}>
                                                <div style={{ fontSize: '13px', color: 'var(--slate-600)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>Patient Collection Rate</div>
                                                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
                                                    <span style={{ fontSize: '32px', fontWeight: '700', color: 'var(--slate-800)' }}>
                                                        {financialMetrics.metrics.patientCollectionRate.value !== null ? `${financialMetrics.metrics.patientCollectionRate.value}%` : 'N/A'}
                                                    </span>
                                                    {financialMetrics.metrics.patientCollectionRate.trend !== null && (
                                                        <span style={{ fontSize: '14px', color: financialMetrics.metrics.patientCollectionRate.trend > 0 ? '#22c55e' : '#ef4444' }}>
                                                            {financialMetrics.metrics.patientCollectionRate.trend > 0 ? '↑' : '↓'} {Math.abs(financialMetrics.metrics.patientCollectionRate.trend)}%
                                                        </span>
                                                    )}
                                                </div>
                                                <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginBottom: '16px' }}>Industry benchmark: 90%</div>
                                                {financialMetrics.metrics.patientCollectionRate.performance && (
                                                    <div className={`performance-badge ${financialMetrics.metrics.patientCollectionRate.performance}`}>
                                                        {financialMetrics.metrics.patientCollectionRate.performance}
                                                    </div>
                                                )}
                                            </div>

                                            {/* AR Over 120 Days Card */}
                                            <div className="metric-card" style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid var(--slate-200)' }}>
                                                <div style={{ fontSize: '13px', color: 'var(--slate-600)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>AR Over 120 Days</div>
                                                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
                                                    <span style={{ fontSize: '32px', fontWeight: '700', color: 'var(--slate-800)' }}>
                                                        {financialMetrics.metrics.arOver120Days.value !== null ? `${financialMetrics.metrics.arOver120Days.value}%` : 'N/A'}
                                                    </span>
                                                    {financialMetrics.metrics.arOver120Days.trend !== null && (
                                                        <span style={{ fontSize: '14px', color: financialMetrics.metrics.arOver120Days.trend > 0 ? '#ef4444' : '#22c55e' }}>
                                                            {financialMetrics.metrics.arOver120Days.trend > 0 ? '↑' : '↓'} {Math.abs(financialMetrics.metrics.arOver120Days.trend)}%
                                                        </span>
                                                    )}
                                                </div>
                                                <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginBottom: '16px' }}>Industry target: &lt;15%</div>
                                                {financialMetrics.metrics.arOver120Days.performance && (
                                                    <div className={`performance-badge ${financialMetrics.metrics.arOver120Days.performance}`}>
                                                        {financialMetrics.metrics.arOver120Days.performance}
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Comparison Section */}
                                        <div style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid var(--slate-200)', marginBottom: '24px' }}>
                                            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '20px', color: 'var(--slate-800)' }}>Performance vs. Talisman Network Average</h3>
                                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
                                                <div>
                                                    <div style={{ fontSize: '13px', color: 'var(--slate-600)', marginBottom: '8px' }}>Your Practice</div>
                                                    <div style={{ fontSize: '24px', fontWeight: '600', color: 'var(--accent)' }}>
                                                        {financialMetrics.metrics.daysInAR.value !== null ? `${financialMetrics.metrics.daysInAR.value} days` : 'N/A'}
                                                    </div>
                                                    <div style={{ fontSize: '12px', color: 'var(--slate-500)' }}>Days in A/R</div>
                                                </div>
                                                <div>
                                                    <div style={{ fontSize: '13px', color: 'var(--slate-600)', marginBottom: '8px' }}>Network Average</div>
                                                    <div style={{ fontSize: '24px', fontWeight: '600', color: 'var(--slate-600)' }}>
                                                        {financialMetrics.comparisons.allPractices.avgDaysInAR !== null ? `${financialMetrics.comparisons.allPractices.avgDaysInAR} days` : 'N/A'}
                                                    </div>
                                                    <div style={{ fontSize: '12px', color: 'var(--slate-500)' }}>Days in A/R</div>
                                                </div>
                                                <div>
                                                    <div style={{ fontSize: '13px', color: 'var(--slate-600)', marginBottom: '8px' }}>Your Percentile Rank</div>
                                                    <div style={{
                                                        fontSize: '24px', fontWeight: '600', color:
                                                            !financialMetrics.comparisons.percentileRank ? 'var(--slate-600)' :
                                                                financialMetrics.comparisons.percentileRank >= 75 ? '#22c55e' :
                                                                    financialMetrics.comparisons.percentileRank >= 50 ? '#f59e0b' : '#ef4444'
                                                    }}>
                                                        {financialMetrics.comparisons.percentileRank !== null ? `${financialMetrics.comparisons.percentileRank}th` : 'N/A'}
                                                    </div>
                                                    <div style={{ fontSize: '12px', color: 'var(--slate-500)' }}>Among Talisman practices</div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Trends Section */}
                                        <div style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid var(--slate-200)' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                                                <h3 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--slate-800)', margin: 0 }}>6-Month Financial Trend</h3>
                                                <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }}></div>
                                                        <span style={{ color: 'var(--slate-600)' }}>Days in A/R</span>
                                                    </div>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e' }}></div>
                                                        <span style={{ color: 'var(--slate-600)' }}>Net Collection Rate</span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div style={{ height: '300px', width: '100%' }}>
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <ComposedChart
                                                        data={financialMetrics.trends}
                                                        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                                                    >
                                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                                        <XAxis
                                                            dataKey="month"
                                                            axisLine={false}
                                                            tickLine={false}
                                                            tick={{ fill: '#64748b', fontSize: 12 }}
                                                            dy={10}
                                                        />
                                                        <YAxis
                                                            yAxisId="left"
                                                            axisLine={false}
                                                            tickLine={false}
                                                            tick={{ fill: '#64748b', fontSize: 12 }}
                                                            label={{ value: 'Days', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#94a3b8', fontSize: 11 } }}
                                                        />
                                                        <YAxis
                                                            yAxisId="right"
                                                            orientation="right"
                                                            axisLine={false}
                                                            tickLine={false}
                                                            tick={{ fill: '#64748b', fontSize: 12 }}
                                                            unit="%"
                                                            domain={[0, 100]}
                                                            label={{ value: 'Rate %', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#94a3b8', fontSize: 11 } }}
                                                        />
                                                        <Tooltip
                                                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                                            itemStyle={{ fontSize: '12px', padding: '2px 0' }}
                                                            labelStyle={{ fontSize: '12px', fontWeight: '600', color: '#334155', marginBottom: '8px' }}
                                                        />
                                                        <Bar
                                                            yAxisId="right"
                                                            dataKey="ncr"
                                                            name="Net Collection Rate"
                                                            fill="#dcfce7"
                                                            barSize={32}
                                                            radius={[4, 4, 0, 0]}
                                                        />
                                                        <Line
                                                            yAxisId="right"
                                                            type="monotone"
                                                            dataKey="ncr"
                                                            name="NCR Trend"
                                                            stroke="#22c55e"
                                                            strokeWidth={2}
                                                            dot={{ r: 3, fill: '#22c55e', strokeWidth: 0 }}
                                                            activeDot={{ r: 5 }}
                                                        />
                                                        <Line
                                                            yAxisId="left"
                                                            type="monotone"
                                                            dataKey="daysInAR"
                                                            name="Days in A/R"
                                                            stroke="#3b82f6"
                                                            strokeWidth={3}
                                                            dot={{ r: 4, fill: '#3b82f6', strokeWidth: 2, stroke: '#fff' }}
                                                            activeDot={{ r: 6 }}
                                                        />
                                                    </ComposedChart>
                                                </ResponsiveContainer>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--slate-500)' }}>
                                        No financial metrics data available
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {!selectedPractice && (
                <div className="card" style={{ marginTop: '24px', textAlign: 'center', padding: '60px' }}>
                    <svg style={{ width: '64px', height: '64px', margin: '0 auto 16px', color: 'var(--slate-300)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    <h3 style={{ color: 'var(--slate-600)', marginBottom: '8px' }}>No Practice Selected</h3>
                    <p style={{ color: 'var(--slate-500)' }}>Select a practice from the dropdown above to view details</p>
                </div>
            )}

            {/* Modals */}
            <PatientDetailsModal
                isOpen={showPatientModal}
                onClose={closePatientModal}
                patientGuid={selectedPatientGuid}
            />

            <EncounterDetailsModal
                isOpen={showEncounterModal}
                onClose={() => {
                    setShowEncounterModal(false)
                    setSelectedEncounterId(null)
                }}
                encounterId={selectedEncounterId}
            />

            <ClaimDetailsModal
                isOpen={showClaimModal}
                onClose={() => {
                    setShowClaimModal(false)
                    setSelectedClaimRefId(null)
                }}
                claimRefId={selectedClaimRefId}
            />
        </div>
    )
}

export default Practices
