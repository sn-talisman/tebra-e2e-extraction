import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import Dashboard from './pages/Dashboard'
import Practices from './pages/Practices'
import ElectronicRemittance from './pages/ElectronicRemittance'
import Financial from './pages/Financial'

function App() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
    const [currentPage, setCurrentPage] = useState('Dashboard')

    return (
        <BrowserRouter>
            <div className="app">
                <Sidebar
                    collapsed={sidebarCollapsed}
                    onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
                    onNavigate={setCurrentPage}
                />
                <div className="main-container">
                    <Topbar title={currentPage} />
                    <div className="content">
                        <Routes>
                            <Route path="/" element={<Navigate to="/dashboard" replace />} />
                            <Route path="/dashboard" element={<Dashboard />} />
                            <Route path="/practices" element={<Practices />} />
                            <Route path="/eras" element={<ElectronicRemittance />} />
                            <Route path="/financial" element={<Financial />} />
                        </Routes>
                    </div>
                </div>
            </div>
        </BrowserRouter>
    )
}

export default App
