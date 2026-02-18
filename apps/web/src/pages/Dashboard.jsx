import React, { useState, useEffect } from 'react';
import { dashboardService } from '../services/dashboard';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend, ComposedChart, Line
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 border border-slate-200 shadow-lg rounded-lg text-sm">
                <p className="font-bold text-slate-800 mb-1">{payload[0].payload.name}</p>
                {payload.map((p, i) => (
                    <p key={i} style={{ color: p.color }}>
                        {p.name}: <span className="font-semibold">
                            {p.name.includes('Rate') || p.name.includes('%') ? `${p.value}%` :
                                p.name.includes('$') || p.name.includes('Paid') || p.name.includes('Billed') ? `$${Number(p.value).toLocaleString()}` :
                                    p.value}
                        </span>
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

function Dashboard() {
    const [metrics, setMetrics] = useState(null);
    const [statusDist, setStatusDist] = useState([]);
    const [practiceQual, setPracticeQual] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [metricsData, statusData, comparisonData] = await Promise.all([
                dashboardService.getMetrics(),
                dashboardService.getStatusDistribution(90),
                dashboardService.getPracticePerformance(90)
            ]);

            setMetrics(metricsData);
            setStatusDist(statusData);
            setPracticeQual(comparisonData);
        } catch (error) {
            console.error("Failed to load dashboard data:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-24 text-slate-500">
                <div className="spinner mb-4"></div>
                <p>Loading Dashboard Insights...</p>
            </div>
        );
    }

    return (
        <div className="animate-fadeIn pb-10">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-slate-900 mb-2">Executive Dashboard</h1>
                <p className="text-slate-500">Organizational overview and key performance indicators</p>
            </header>

            {/* KPI Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 32 }}>
                {[
                    { icon: '👥', label: 'Encounters', value: metrics?.totalEncounters?.toLocaleString() || 0, sub: 'All-time volume' },
                    { icon: '📊', label: 'Total Claims', value: metrics?.totalClaims?.toLocaleString() || 0, sub: 'Processed claims' },
                    { icon: '💰', label: 'Total Billed', value: `$${(metrics?.totalBilled || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, sub: 'Gross charges' },
                    { icon: '💵', label: 'Realized Revenue', value: `$${(metrics?.totalPaid || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, sub: 'Total payments', color: '#10b981' },
                    { icon: '✅', label: 'Collection Rate', value: `${metrics?.collectionRate || 0}%`, sub: 'Overall efficiency', color: metrics?.collectionRate > 80 ? '#10b981' : '#0f172a' },
                    { icon: '🏛️', label: 'Active Network', value: `${metrics?.practicesCount || 0} Practices`, sub: 'Connected locations' },
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

            {/* Main Visual Row: Status Distribution & Top Practice Performance */}
            <div className="grid grid-cols-1 xl:grid-cols-5 gap-6 mb-8">

                {/* 1. Status Distribution (Pie) */}
                <div className="xl:col-span-2 card shadow-sm border border-slate-200 p-6 rounded-xl bg-white">
                    <div className="mb-4">
                        <h3 className="text-lg font-bold text-slate-900">Claim Status Distribution</h3>
                        <p className="text-sm text-slate-500">Breakdown by current adjudication state</p>
                    </div>
                    <div style={{ width: '100%', height: 320 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={statusDist}
                                    cx="50%"
                                    cy="45%"
                                    innerRadius={70}
                                    outerRadius={100}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {statusDist.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                />
                                <Legend verticalAlign="bottom" height={36} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* 2. Top Practices Performance (Mixed Chart) */}
                <div className="xl:col-span-3 card shadow-sm border border-slate-200 p-6 rounded-xl bg-white">
                    <div className="mb-4">
                        <h3 className="text-lg font-bold text-slate-900">Top 10 Practices Performance</h3>
                        <p className="text-sm text-slate-500">Claims Volume (Bar) vs. Realized Revenue (Line)</p>
                    </div>
                    <div style={{ width: '100%', height: 320 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={practiceQual}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                                <YAxis yAxisId="left" orientation="left" tick={{ fontSize: 11 }} name="Volume" />
                                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} name="Revenue" tickFormatter={(v) => `$${Math.round(v / 1000)}k`} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Bar yAxisId="left" dataKey="claims" name="Claims Volume" fill="#818cf8" radius={[4, 4, 0, 0]} />
                                <Line yAxisId="right" type="monotone" dataKey="paid" name="Paid Amount ($)" stroke="#10b981" strokeWidth={3} dot={{ r: 4, fill: '#10b981' }} />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Financial Metrics Across Practices (Comparison Table) */}
            <div className="card shadow-sm border border-slate-200 p-6 rounded-xl bg-white">
                <div className="mb-6">
                    <h3 className="text-lg font-bold text-slate-900">Practice Financial Comparison</h3>
                    <p className="text-sm text-slate-500">Cross-comparison of key efficiency RCM metrics</p>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-100">
                                <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Practice Name</th>
                                <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Collection Rate</th>
                                <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Denial Rate</th>
                                <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Days in A/R</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                            {practiceQual.map((p, idx) => (
                                <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="py-4 px-4 font-medium text-slate-700">{p.name}</td>
                                    <td className="py-4 px-4 font-bold text-slate-900 text-right">{p.collection_rate}%</td>
                                    <td className="py-4 px-4 text-right">
                                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${p.denial_rate > 25 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'
                                            }`}>
                                            {p.denial_rate}%
                                        </span>
                                    </td>
                                    <td className="py-4 px-4 text-slate-600 text-right">{p.days_in_ar} Days</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    );
}

export default Dashboard;
