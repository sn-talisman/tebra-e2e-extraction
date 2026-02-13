import React, { useState, useEffect } from 'react';
import { analyticsService } from '../../services/analytics';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    ScatterChart, Scatter, ZAxis, ReferenceLine
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 border border-slate-200 shadow-lg rounded-lg text-sm">
                <p className="font-bold text-slate-800 mb-1">{payload[0].payload.name}</p>
                {payload.map((p, i) => (
                    <p key={i} style={{ color: p.color }}>
                        {p.name}: <span className="font-semibold">{p.value}</span>
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

const ExecutiveSummary = ({ practices }) => {
    const [summary, setSummary] = useState(null);
    const [payers, setPayers] = useState([]);
    const [cpts, setCpts] = useState([]);
    const [actionItems, setActionItems] = useState([]);
    const [expandedActionIndex, setExpandedActionIndex] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadGlobalInsights();
    }, []);

    const loadGlobalInsights = async () => {
        setLoading(true);
        try {
            const [summaryData, payersData, cptsData, actionsData] = await Promise.all([
                analyticsService.getGlobalPerformanceSummary(90),
                analyticsService.getGlobalPayerPerformance(90),
                analyticsService.getGlobalCptPerformance(90),
                analyticsService.getGlobalActionItems(90)
            ]);

            setSummary(summaryData);
            setPayers(payersData);
            setCpts(cptsData);
            setActionItems(actionsData.action_items || []);
        } catch (error) {
            console.error("Failed to load global insights:", error);
        } finally {
            setLoading(false);
        }
    };

    // Chart Data Preparation ---------------------------

    const safeNumber = (val) => {
        const num = Number(val);
        return isNaN(num) ? 0 : num;
    };

    // 1. Practice Performance (Bar Chart)
    const practiceData = Array.isArray(practices) ? practices
        .map(p => ({
            name: p.practice_name || 'Unknown',
            'Denial Rate': p.denial_rate ? parseFloat((p.denial_rate * 100).toFixed(1)) : 0,
            'Denied Amount': Math.round(p.denied_billed || 0)
        }))
        .sort((a, b) => b['Denial Rate'] - a['Denial Rate'])
        .slice(0, 15) : [];

    // 2. Payer Landscape (Scatter: Vol vs Rate, Size=Amount)
    const payerScatterData = Array.isArray(payers) ? payers.map(p => ({
        name: p.name || 'Unknown',
        x: safeNumber(p.total_claims),
        y: safeNumber(p.rate), // Already 0-100 from backend? Backend sends 'rate' as % (e.g. 15.5)
        z: safeNumber(p.denied_amount)
    })) : [];

    // 3. CPT Landscape (Scatter: Vol vs Rate, Size=Amount)
    const cptScatterData = Array.isArray(cpts) ? cpts.map(c => ({
        name: c.code || 'Unknown',
        x: safeNumber(c.volume),
        y: c.denial_rate ? parseFloat((c.denial_rate * 100).toFixed(1)) : 0,
        z: safeNumber(c.denied_amount)
    })) : [];

    if (loading) return (
        <div className="flex flex-col items-center justify-center py-24 text-slate-500">
            <div className="spinner mb-4"></div>
            <p>Aggregating Global Insights...</p>
        </div>
    );

    // Fallback if critical data is missing (though we render what we can)
    if (!summary && !loading) {
        return (
            <div className="p-8 text-center text-slate-500">
                <p>Unable to load Executive Summary data. Please try again later.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn pb-10">
            {/* Header */}
            <header className="border-b border-slate-200 pb-4">
                <h2 className="text-2xl font-bold text-slate-800">Executive Summary (All Practices)</h2>
                <p className="text-sm text-slate-500">Global Performance Analytics & Strategic Action Items</p>
            </header>

            {/* KPI Cards */}
            {summary && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
                    {[
                        { icon: '📊', label: 'Total Claims', value: Number(summary.total_claims).toLocaleString(), sub: 'Last 90 Days' },
                        { icon: '💰', label: 'Total Billed', value: `$${Number(summary.total_billed).toLocaleString(undefined, { maximumFractionDigits: 0 })}` },
                        { icon: '🚫', label: 'Denial Rate', value: `${(summary.denial_rate * 100).toFixed(1)}%`, color: summary.denial_rate > 0.1 ? '#dc2626' : '#16a34a' },
                        { icon: '⚠️', label: 'Denied Amount', value: `$${Number(summary.denied_amount).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, sub: 'Potential Recovery' },
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
                            <div style={{ fontSize: 28, fontWeight: 700, color: card.color || '#0f172a', lineHeight: 1.1 }}>{card.value}</div>
                            {card.sub && <div style={{ fontSize: 12, color: '#94a3b8' }}>{card.sub}</div>}
                        </div>
                    ))}
                </div>
            )}

            {/* 1. Practice Health (Bar Chart) */}
            <div className="card shadow-sm border border-slate-200 p-6 rounded-xl bg-white">
                <div className="mb-4">
                    <h3 className="text-lg font-bold text-slate-900">Practice Denial Rates</h3>
                    <p className="text-sm text-slate-500">Comparing denial % across practices (Top 15)</p>
                </div>
                <div style={{ width: '100%', height: 300 }}>
                    {practiceData.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={practiceData} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="name" angle={-45} textAnchor="end" height={60} tick={{ fontSize: 11 }} interval={0} />
                                <YAxis unit="%" tick={{ fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                    cursor={{ fill: '#f8fafc' }}
                                />
                                <Bar dataKey="Denial Rate" fill="#6366f1" radius={[4, 4, 0, 0]} name="Denial Rate %" />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-full text-slate-400">
                            No practice data available to display.
                        </div>
                    )}
                </div>
            </div>

            {/* 2. Payer & CPT Landscape (Scatter Plots) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* Payer Landscape */}
                <div className="card shadow-sm border border-slate-200 p-6 rounded-xl bg-white">
                    <div className="mb-4">
                        <h3 className="text-lg font-bold text-slate-900">Payer Landscape</h3>
                        <p className="text-sm text-slate-500">Volume vs. Denial Rate (Size = Denied $)</p>
                    </div>
                    <div style={{ width: '100%', height: 320 }}>
                        {payerScatterData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                    <XAxis type="number" dataKey="x" name="Claims Volume" unit="" fontSize={12} />
                                    <YAxis type="number" dataKey="y" name="Denial Rate" unit="%" fontSize={12} />
                                    <ZAxis type="number" dataKey="z" range={[50, 400]} name="Denied Amount" unit="$" />
                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
                                    <ReferenceLine y={20} label="High Denial Risk (20%)" stroke="#ef4444" strokeDasharray="3 3" />
                                    <Scatter name="Payers" data={payerScatterData} fill="#0ea5e9" fillOpacity={0.6} stroke="#0284c7" />
                                </ScatterChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-slate-400">
                                No payer data available.
                            </div>
                        )}
                    </div>
                </div>

                {/* CPT Landscape */}
                <div className="card shadow-sm border border-slate-200 p-6 rounded-xl bg-white">
                    <div className="mb-4">
                        <h3 className="text-lg font-bold text-slate-900">Procedure (CPT) Risks</h3>
                        <p className="text-sm text-slate-500">Volume vs. Denial Rate (Size = Denied $)</p>
                    </div>
                    <div style={{ width: '100%', height: 320 }}>
                        {cptScatterData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                    <XAxis type="number" dataKey="x" name="Volume" unit="" fontSize={12} />
                                    <YAxis type="number" dataKey="y" name="Denial Rate" unit="%" fontSize={12} />
                                    <ZAxis type="number" dataKey="z" range={[50, 400]} name="Denied Amount" unit="$" />
                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
                                    <ReferenceLine y={10} label="Avg Denial Rate" stroke="#f59e0b" strokeDasharray="3 3" />
                                    <Scatter name="CPTs" data={cptScatterData} fill="#8b5cf6" fillOpacity={0.6} stroke="#7c3aed" />
                                </ScatterChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-slate-400">
                                No CPT data available.
                            </div>
                        )}
                    </div>
                </div>
            </div>


            {/* Action Items - Executive Style */}
            {actionItems.length > 0 && (
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                            🚀 Strategic Action Plan
                        </h3>
                        <span className="text-xs font-semibold bg-blue-50 text-blue-600 px-3 py-1 rounded-full border border-blue-100">
                            AI GENERATED INSIGHTS
                        </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {actionItems.map((item, index) => (
                            <div key={index} className="group relative bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
                                <div className={`absolute top-0 left-0 w-1.5 h-full rounded-l-xl ${item.priority === 'HIGH' ? 'bg-rose-500' : 'bg-amber-500'
                                    }`}></div>

                                <div className="pl-3">
                                    <div className="flex justify-between items-start mb-3">
                                        <span className={`text-[10px] font-bold tracking-widest uppercase px-2 py-1 rounded-md ${item.priority === 'HIGH'
                                            ? 'bg-rose-50 text-rose-600 border border-rose-100'
                                            : 'bg-amber-50 text-amber-600 border border-amber-100'
                                            }`}>
                                            {item.priority} PRIORITY
                                        </span>
                                        {item.financial_impact > 0 && (
                                            <div className="text-right">
                                                <div className="text-xs text-slate-400 font-medium uppercase tracking-wide">Impact Opportunity</div>
                                                <div className="text-lg font-bold text-emerald-600">
                                                    ${item.financial_impact.toLocaleString()}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <h4 className="text-lg font-bold text-slate-800 mb-2 group-hover:text-blue-600 transition-colors">
                                        {item.title}
                                    </h4>

                                    <p className="text-sm text-slate-600 leading-relaxed mb-4">
                                        {item.recommendation}
                                    </p>

                                    {/* Expanded Details Section */}
                                    {expandedActionIndex === index && item.suggested_next_steps && (
                                        <div className="mt-5 bg-slate-50 p-5 rounded-lg border border-slate-200 animate-fadeIn">
                                            <h5 className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                                                <span className="text-blue-500 text-lg">⚡</span> Suggested Next Steps
                                            </h5>
                                            <ul className="space-y-3">
                                                {item.suggested_next_steps.map((step, stepIdx) => (
                                                    <li key={stepIdx} className="flex items-start gap-3 text-sm text-slate-700">
                                                        <div className="mt-1.5 min-w-[6px] h-[6px] rounded-full bg-blue-500 shrink-0"></div>
                                                        <span className="leading-relaxed">{step}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    <button
                                        onClick={() => setExpandedActionIndex(expandedActionIndex === index ? null : index)}
                                        className="text-xs font-semibold text-slate-500 flex items-center gap-1 group-hover:text-blue-600 transition-colors hover:cursor-pointer"
                                    >
                                        {expandedActionIndex === index ? 'HIDE DETAILS' : 'VIEW DETAILS'}
                                        <span className={`text-lg leading-none transition-transform duration-200 ${expandedActionIndex === index ? 'rotate-90' : ''}`}>›</span>
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ExecutiveSummary;
