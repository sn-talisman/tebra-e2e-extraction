import React, { useState, useEffect } from 'react';
import { analyticsService } from '../../services/analytics';
import InteractiveReport from './InteractiveReport';

// Helper for safe property access
const safeGet = (obj, path, fallback) => {
    if (!obj) return fallback;
    const keys = path.split('.');
    let result = obj;
    for (const key of keys) {
        if (result && typeof result === 'object' && key in result) {
            result = result[key];
        } else {
            return fallback;
        }
    }
    return result !== undefined ? result : fallback;
};

const PracticeDashboard = ({ practiceId }) => {
    const [reportOpen, setReportOpen] = useState(false);
    const [summary, setSummary] = useState(null);
    const [reportData, setReportData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (practiceId) {
            const safetyTimer = setTimeout(() => {
                setLoading(prev => {
                    if (prev) {
                        console.warn("Safety timeout triggered.");
                        return false;
                    }
                    return prev;
                });
            }, 60000);

            loadDashboardData().finally(() => clearTimeout(safetyTimer));
            return () => clearTimeout(safetyTimer);
        }
    }, [practiceId]);

    const loadDashboardData = async () => {
        setLoading(true);
        console.log("Loading Dashboard & Report for", practiceId);

        try {
            const [
                summaryResult,
                reportDataResult
            ] = await Promise.allSettled([
                analyticsService.getPracticePerformance(practiceId, 90),
                analyticsService.getPracticeReportData(practiceId, 90)
            ]);

            setSummary(summaryResult.status === 'fulfilled' ? summaryResult.value : { practice_name: 'Data Unavailable' });
            if (reportDataResult.status === 'fulfilled' && reportDataResult.value) {
                setReportData(reportDataResult.value);
            }

        } catch (error) {
            console.error("Critical Error loading dashboard:", error);
        } finally {
            setLoading(false);
        }
    };

    // Chevron icon component
    const Chevron = ({ open }) => (
        <svg
            style={{
                width: '20px', height: '20px',
                transition: 'transform 0.3s ease',
                transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
                flexShrink: 0,
            }}
            viewBox="0 0 20 20" fill="currentColor"
        >
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
    );

    if (loading) return (
        <div className="flex flex-col items-center justify-center py-24 text-slate-500">
            <div className="spinner mb-4"></div>
            <p>Generating Practice Insights...</p>
        </div>
    );

    return (
        <div className="space-y-4 animate-fadeIn pb-10">
            {/* Header */}
            <header className="border-b border-slate-200 pb-4">
                <h2 className="text-2xl font-bold text-slate-800">{reportData?.practice_name || summary?.practice_name || 'Practice Performance'}</h2>
                <p className="text-sm text-slate-500">Practice Performance Analytics & AI Analysis</p>
            </header>

            {/* ── Always-visible KPI Cards ─────────────────────── */}
            {reportData?.summary && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
                    {[
                        { icon: '📊', label: 'Total Claims', value: Number(reportData.summary.total_claims || 0).toLocaleString(), sub: `Past ${reportData.days_back} days` },
                        { icon: '💰', label: 'Total Billed', value: `$${Number(reportData.summary.total_billed || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}` },
                        { icon: '✅', label: 'Total Paid', value: `$${Number(reportData.summary.total_paid || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}` },
                        { icon: '⚠️', label: 'Denied Amount', value: `$${Number(reportData.summary.denied_amount || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, sub: 'Potential recovery' },
                    ].map((card, i) => (
                        <div key={i} style={{
                            background: '#fff', borderRadius: 12, padding: '20px 24px',
                            border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,.06)',
                            display: 'flex', flexDirection: 'column', gap: 4,
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                <span style={{ fontSize: 20 }}>{card.icon}</span>
                                <span style={{ fontSize: 12, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '.05em' }}>{card.label}</span>
                            </div>
                            <div style={{ fontSize: 28, fontWeight: 700, color: '#0f172a', lineHeight: 1.1 }}>{card.value}</div>
                            {card.sub && <div style={{ fontSize: 12, color: '#94a3b8' }}>{card.sub}</div>}
                        </div>
                    ))}
                </div>
            )}

            {/* ── Collapsible: Interactive Report ──────────────── */}
            <div className="card shadow-sm border border-slate-200 overflow-hidden">
                <button
                    onClick={() => setReportOpen(!reportOpen)}
                    style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        width: '100%', padding: '16px 24px',
                        backgroundColor: reportOpen ? '#f8fafc' : '#ffffff',
                        border: 'none',
                        borderBottom: reportOpen ? '1px solid #e2e8f0' : 'none',
                        cursor: 'pointer', transition: 'background-color 0.2s ease',
                    }}
                    onMouseEnter={e => e.currentTarget.style.backgroundColor = '#f1f5f9'}
                    onMouseLeave={e => e.currentTarget.style.backgroundColor = reportOpen ? '#f8fafc' : '#ffffff'}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span style={{ fontSize: '18px' }}>📊</span>
                        <div style={{ textAlign: 'left' }}>
                            <div style={{ fontWeight: 600, fontSize: '15px', color: '#1e293b' }}>Interactive Report</div>
                            <div style={{ fontSize: '12px', color: '#64748b' }}>KPIs, Charts & Sortable Tables</div>
                        </div>
                    </div>
                    <Chevron open={reportOpen} />
                </button>
                <div style={{
                    maxHeight: reportOpen ? '10000px' : '0px',
                    overflow: 'hidden',
                    transition: 'max-height 0.5s ease-in-out',
                }}>
                    <div style={{ padding: '20px 24px' }}>
                        {reportData ? (
                            <InteractiveReport data={reportData} />
                        ) : (
                            <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
                                No report data available
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PracticeDashboard;

