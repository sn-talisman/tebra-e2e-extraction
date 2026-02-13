import React, { useState, useEffect } from 'react';
import { analyticsService } from '../services/analytics';
import ExecutiveSummary from '../components/analytics/ExecutiveSummary';
import PracticeDashboard from '../components/analytics/PracticeDashboard';
import PracticeSelector from '../components/PracticeSelector';

const Analytics = () => {
    const [practices, setPractices] = useState([]);
    const [selectedPractice, setSelectedPractice] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadPractices();
    }, []);

    const loadPractices = async () => {
        try {
            const data = await analyticsService.getPractices(90); // 90 days default
            setPractices(data);
        } catch (error) {
            console.error("Failed to load practices:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="mb-6 flex justify-between items-end">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Analytics Dashboard</h1>
                    <p className="text-slate-500">Insights for the last 90 days (Quarterly View)</p>
                </div>

                <div className="w-72">
                    <PracticeSelector
                        practices={practices}
                        selectedPractice={practices.find(p => p.practice_id === selectedPractice) || null}
                        onSelect={(p) => setSelectedPractice(p ? p.practice_id : null)}
                        placeholder="All Practices (Executive Summary)"
                    />
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center items-center h-64">
                    <div className="spinner"></div>
                </div>
            ) : (
                <>
                    {!selectedPractice ? (
                        <ExecutiveSummary practices={practices} />
                    ) : (
                        <PracticeDashboard practiceId={selectedPractice} />
                    )}
                </>
            )}
        </div>
    );
};

export default Analytics;
