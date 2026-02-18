import React, { useState, useMemo } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer, PieChart, Pie, Cell, Treemap,
} from 'recharts';

/* ── colour palette ────────────────────────────────────────────── */
const ACCENT = '#2563eb';
const SUCCESS = '#059669';
const DANGER = '#dc2626';
const WARNING = '#d97706';
const COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2', '#be185d', '#4f46e5'];

/* ── formatting helpers ────────────────────── */
const fmt$ = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const fmtPct = (v) => `${(Number(v || 0) * 100).toFixed(1)}%`;
const fmtNum = (v) => Number(v || 0).toLocaleString();

/* ────────────────────────────────────────────────────────────────
   KPI CARD
   ────────────────────────────────────────────────────────────── */
const KpiCard = ({ label, value, subtitle, icon, trend, trendLabel, color = '#2563eb' }) => (
    <div style={{
        background: '#fff', borderRadius: 12, padding: '20px 24px',
        border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,.06)',
        display: 'flex', flexDirection: 'column', gap: 4, minWidth: 0,
    }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 20 }}>{icon}</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '.05em' }}>{label}</span>
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, color: '#0f172a', lineHeight: 1.1 }}>{value}</div>
        {trend !== undefined && (
            <div style={{ fontSize: 13, fontWeight: 600, color: trend < 0 ? SUCCESS : DANGER, display: 'flex', alignItems: 'center', gap: 4 }}>
                {trend < 0 ? '▼' : '▲'} {Math.abs(trend * 100).toFixed(1)}% {trendLabel || 'vs overall'}
            </div>
        )}
        {subtitle && <div style={{ fontSize: 12, color: '#94a3b8' }}>{subtitle}</div>}
    </div>
);

/* ────────────────────────────────────────────────────────────────
   SORTABLE TABLE
   ────────────────────────────────────────────────────────────── */
const SortableTable = ({ columns, data, maxRows = 15, emptyMessage = 'No data available' }) => {
    const [sortKey, setSortKey] = useState(null);
    const [sortAsc, setSortAsc] = useState(true);

    const sorted = useMemo(() => {
        if (!sortKey) return data;
        return [...data].sort((a, b) => {
            const va = a[sortKey], vb = b[sortKey];
            if (typeof va === 'number' && typeof vb === 'number') return sortAsc ? va - vb : vb - va;
            return sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
        });
    }, [data, sortKey, sortAsc]);

    const handleSort = (key) => {
        if (sortKey === key) { setSortAsc(!sortAsc); } else { setSortKey(key); setSortAsc(false); }
    };

    if (!data || data.length === 0) return <div style={{ padding: 24, color: '#94a3b8', textAlign: 'center' }}>{emptyMessage}</div>;

    return (
        <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                    <tr>
                        {columns.map(col => (
                            <th
                                key={col.key}
                                onClick={() => handleSort(col.key)}
                                style={{
                                    padding: '10px 14px', textAlign: col.align || 'left',
                                    fontSize: 11, fontWeight: 700, color: '#64748b',
                                    textTransform: 'uppercase', letterSpacing: '.05em',
                                    borderBottom: '2px solid #e2e8f0', cursor: 'pointer',
                                    background: sortKey === col.key ? '#f1f5f9' : 'transparent',
                                    userSelect: 'none', whiteSpace: 'nowrap',
                                    transition: 'background .15s',
                                }}
                            >
                                {col.label} {sortKey === col.key ? (sortAsc ? '↑' : '↓') : ''}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {sorted.slice(0, maxRows).map((row, i) => (
                        <tr
                            key={i}
                            style={{ transition: 'background .15s' }}
                            onMouseEnter={e => e.currentTarget.style.background = '#f8fafc'}
                            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                        >
                            {columns.map(col => (
                                <td key={col.key} style={{
                                    padding: '10px 14px', borderBottom: '1px solid #f1f5f9',
                                    textAlign: col.align || 'left', whiteSpace: 'nowrap',
                                    color: '#334155', fontVariantNumeric: 'tabular-nums',
                                }}>
                                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

/* ────────────────────────────────────────────────────────────────
   SECTION WRAPPER — collapsible card
   ────────────────────────────────────────────────────────────── */
const Section = ({ title, icon, children, defaultOpen = true }) => {
    const [open, setOpen] = useState(defaultOpen);
    return (
        <div style={{
            background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,.06)', overflow: 'hidden',
        }}>
            <button
                onClick={() => setOpen(!open)}
                style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    width: '100%', padding: '14px 20px', background: 'none', border: 'none',
                    cursor: 'pointer', borderBottom: open ? '1px solid #e2e8f0' : 'none',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 18 }}>{icon}</span>
                    <span style={{ fontSize: 15, fontWeight: 600, color: '#1e293b' }}>{title}</span>
                </div>
                <svg style={{ width: 18, height: 18, transition: 'transform .25s', transform: open ? 'rotate(180deg)' : 'rotate(0)' }}
                    viewBox="0 0 20 20" fill="#64748b">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
            </button>
            <div style={{ maxHeight: open ? 2000 : 0, overflow: 'hidden', transition: 'max-height .35s ease-in-out' }}>
                <div style={{ padding: '16px 20px' }}>{children}</div>
            </div>
        </div>
    );
};

/* ── Denial-rate bar with colour ──────────────────────────────── */
const DenialBar = ({ rate }) => {
    const pct = (rate * 100);
    const color = pct > 25 ? DANGER : pct > 15 ? WARNING : SUCCESS;
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 60, height: 6, borderRadius: 3, background: '#e2e8f0', overflow: 'hidden' }}>
                <div style={{ width: `${Math.min(pct, 100)}%`, height: '100%', borderRadius: 3, background: color, transition: 'width .4s' }} />
            </div>
            <span style={{ fontSize: 12, fontWeight: 600, color }}>{pct.toFixed(1)}%</span>
        </div>
    );
};

/* ── Custom Recharts tooltip ──────────────── */
const ChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '10px 14px', boxShadow: '0 4px 12px rgba(0,0,0,.1)', fontSize: 13 }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
            {payload.map((p, i) => (
                <div key={i} style={{ color: p.color, display: 'flex', gap: 8 }}>
                    <span>{p.name}:</span>
                    <strong>{typeof p.value === 'number' ? (p.name.includes('Rate') ? fmtPct(p.value) : fmt$(p.value)) : p.value}</strong>
                </div>
            ))}
        </div>
    );
};

/* ════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ════════════════════════════════════════════════════════════ */
const InteractiveReport = ({ data }) => {
    if (!data) return null;

    const { practice_name, summary, payers = [], cpts = [], high_risk = [], denial_reasons = {}, cpt_carc = {} } = data;
    const carc_codes = denial_reasons?.carc_codes || [];
    const cpt_carc_list = cpt_carc?.cpt_carc || [];

    /* ── chart data prep ──────────────── */
    const payerChartData = payers.slice(0, 8).map(p => ({
        name: p.payer_name?.length > 18 ? p.payer_name.substring(0, 18) + '…' : p.payer_name,
        'Denied Amount': p.denied_amount,
        'Claims': p.total_claims,
        denial_rate: p.denial_rate,
    }));

    const cptChartData = cpts.slice(0, 8).map(c => ({
        name: c.cpt_code,
        'Denied Amount': c.denied_amount,
        'Claims': c.total_claims,
        denial_rate: c.denial_rate,
    }));

    const carcPieData = carc_codes.slice(0, 8).map(c => ({
        name: `CARC ${c.carc_code}`,
        value: c.total_adjustment_amount,
        desc: c.description,
        count: c.occurrence_count,
    }));

    /* ── denial rate trend indicator ──── */
    const rateVsOverall = summary.denial_rate_vs_overall;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* ─── KPI STRIP ──────────────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
                <KpiCard icon="📊" label="Total Claims" value={fmtNum(summary.total_claims)} subtitle={`Past ${data.days_back} days`} />
                <KpiCard icon="💰" label="Total Billed" value={fmt$(summary.total_billed)} />
                <KpiCard icon="✅" label="Total Paid" value={fmt$(summary.total_paid)} color={SUCCESS} />
                <KpiCard icon="⚠️" label="Denied Amount" value={fmt$(summary.denied_amount)} color={DANGER}
                    subtitle="Potential recovery" />
                <KpiCard icon="📉" label="Denial Rate" value={fmtPct(summary.denial_rate)}
                    trend={rateVsOverall} trendLabel="vs overall" />
            </div>

            {/* ─── PAYER PERFORMANCE ─────────────────────────── */}
            <Section title="Performance by Payer" icon="🏥" defaultOpen={true}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                    {/* Bar chart */}
                    <div style={{ height: 320 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 8 }}>Denied Amount by Payer</div>
                        <ResponsiveContainer width="100%" height="90%">
                            <BarChart data={payerChartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                                <XAxis type="number" tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} />
                                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} axisLine={false} />
                                <Tooltip content={<ChartTooltip />} />
                                <Bar dataKey="Denied Amount" fill={ACCENT} radius={[0, 4, 4, 0]} barSize={18} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    {/* Denial-rate mini bars */}
                    <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 8 }}>Denial Rate by Payer</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {payers.slice(0, 8).map((p, i) => (
                                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: 12, color: '#475569', maxWidth: '55%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {p.payer_name}
                                    </span>
                                    <DenialBar rate={p.denial_rate} />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
                {/* Full table */}
                <SortableTable
                    columns={[
                        { key: 'payer_name', label: 'Payer' },
                        { key: 'total_claims', label: 'Claims', align: 'right', render: v => fmtNum(v) },
                        { key: 'denial_rate', label: 'Denial Rate', align: 'right', render: (v) => <DenialBar rate={v} /> },
                        { key: 'denied_amount', label: 'Denied Amount', align: 'right', render: v => fmt$(v) },
                    ]}
                    data={payers}
                />
            </Section>

            {/* ─── CPT PERFORMANCE ───────────────────────────── */}
            <Section title="Performance by CPT Code" icon="🔬" defaultOpen={true}>
                <div style={{ height: 300, marginBottom: 16 }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={cptChartData} margin={{ bottom: 40 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis dataKey="name" tick={{ fontSize: 10, angle: -30, textAnchor: 'end' }} axisLine={false} />
                            <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} />
                            <Tooltip content={<ChartTooltip />} />
                            <Legend />
                            <Bar dataKey="Denied Amount" fill="#7c3aed" radius={[4, 4, 0, 0]} barSize={28} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
                <SortableTable
                    columns={[
                        { key: 'cpt_code', label: 'CPT Code' },
                        { key: 'total_claims', label: 'Claims', align: 'right', render: v => fmtNum(v) },
                        { key: 'denial_rate', label: 'Denial Rate', align: 'right', render: (v) => <DenialBar rate={v} /> },
                        { key: 'denied_amount', label: 'Denied Amount', align: 'right', render: v => fmt$(v) },
                    ]}
                    data={cpts}
                />
            </Section>

            {/* ─── DENIAL REASONS (CARC) ────────────────────── */}
            {carc_codes.length > 0 && (
                <Section title="Denial Reasons (CARC Codes)" icon="🔍" defaultOpen={true}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                        <div style={{ height: 280 }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 8 }}>Adjustment Amount Distribution</div>
                            <ResponsiveContainer width="100%" height="90%">
                                <PieChart>
                                    <Pie data={carcPieData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                                        outerRadius={90} innerRadius={50} paddingAngle={2}>
                                        {carcPieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                                    </Pie>
                                    <Tooltip formatter={(v) => fmt$(v)} />
                                    <Legend wrapperStyle={{ fontSize: 11 }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        {/* Top CARC summary cards */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 4 }}>Top Denial Reasons</div>
                            {carc_codes.slice(0, 5).map((c, i) => (
                                <div key={i} style={{
                                    padding: '10px 14px', borderRadius: 8, border: '1px solid #e2e8f0',
                                    background: '#fafbfc', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                }}>
                                    <div>
                                        <div style={{ fontSize: 13, fontWeight: 600, color: COLORS[i % COLORS.length] }}>CARC {c.carc_code}</div>
                                        <div style={{ fontSize: 11, color: '#64748b', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {c.description}
                                        </div>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                        <div style={{ fontSize: 14, fontWeight: 700, color: '#0f172a' }}>{fmt$(c.total_adjustment_amount)}</div>
                                        <div style={{ fontSize: 11, color: '#94a3b8' }}>{c.occurrence_count} occurrences</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <SortableTable
                        columns={[
                            { key: 'carc_code', label: 'CARC Code' },
                            { key: 'description', label: 'Description', render: v => <span title={v}>{v?.length > 50 ? v.substring(0, 50) + '…' : v}</span> },
                            { key: 'occurrence_count', label: 'Occurrences', align: 'right', render: v => fmtNum(v) },
                            { key: 'affected_claims', label: 'Claims', align: 'right', render: v => fmtNum(v) },
                            { key: 'total_adjustment_amount', label: 'Total Amount', align: 'right', render: v => fmt$(v) },
                        ]}
                        data={carc_codes}
                    />
                </Section>
            )}

            {/* ─── CPT-CARC CORRELATION ─────────────────────── */}
            {cpt_carc_list.length > 0 && (
                <Section title="CPT–CARC Correlation" icon="🔗" defaultOpen={false}>
                    <p style={{ fontSize: 13, color: '#64748b', marginBottom: 12 }}>
                        Shows which procedure codes are most commonly denied with specific CARC reasons.
                    </p>
                    <SortableTable
                        columns={[
                            { key: 'cpt_code', label: 'CPT Code' },
                            { key: 'carc_code', label: 'CARC Code' },
                            { key: 'carc_description', label: 'Reason', render: v => <span title={v}>{v?.length > 40 ? v.substring(0, 40) + '…' : v}</span> },
                            { key: 'occurrence_count', label: 'Occurrences', align: 'right', render: v => fmtNum(v) },
                            { key: 'affected_claims', label: 'Claims', align: 'right', render: v => fmtNum(v) },
                            { key: 'total_adjustment_amount', label: 'Amount', align: 'right', render: v => fmt$(v) },
                        ]}
                        data={cpt_carc_list}
                    />
                </Section>
            )}

            {/* ─── HIGH-RISK CLAIMS ─────────────────────────── */}
            {high_risk.length > 0 && (
                <Section title="High-Risk Claims" icon="🚨" defaultOpen={false}>
                    <SortableTable
                        columns={[
                            { key: 'claim_id', label: 'Claim ID', render: v => <code style={{ fontSize: 12, background: '#f1f5f9', padding: '2px 6px', borderRadius: 4 }}>{v?.substring(0, 12)}</code> },
                            { key: 'payer_name', label: 'Payer' },
                            { key: 'cpt_code', label: 'CPT Code' },
                            { key: 'denial_probability', label: 'Denial Prob.', align: 'right', render: v => <span style={{ color: DANGER, fontWeight: 600 }}>{fmtPct(v)}</span> },
                            { key: 'billed_amount', label: 'Billed Amount', align: 'right', render: v => <span style={{ fontWeight: 600 }}>{fmt$(v)}</span> },
                        ]}
                        data={high_risk}
                        maxRows={20}
                    />
                </Section>
            )}
        </div>
    );
};

export default InteractiveReport;
