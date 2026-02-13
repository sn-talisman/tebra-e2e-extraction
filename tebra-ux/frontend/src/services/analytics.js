import { ANALYTICS_BASE_URL, API_BASE_URL } from '../config';

// Helper to fetch with timeout
const fetchWithTimeout = async (resource, options = {}) => {
    const { timeout = 8000 } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(resource, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        throw error;
    }
};

export const analyticsService = {
    // Get all practices for the dropdown and summary
    getPractices: async (daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/practices?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch practices');
            return response.json();
        } catch (error) {
            console.error("Error fetching practices:", error);
            return [];
        }
    },

    // Get payer performance for Executive Summary
    getPayers: async (daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/payers?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch payers');
            return response.json();
        } catch (error) {
            console.error("Error fetching payers:", error);
            return [];
        }
    },

    // Get specific practice performance summary
    getPracticePerformance: async (practiceGuid, daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/practice/${practiceGuid}/performance-summary?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch performance summary');
            return response.json();
        } catch (error) {
            console.error("Error fetching practice performance:", error);
            return null;
        }
    },

    // Get prioritized action items
    getActionItems: async (practiceGuid, daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/practice/${practiceGuid}/action-items?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch action items');
            return response.json();
        } catch (error) {
            console.error("Error fetching action items:", error);
            return [];
        }
    },

    // Get payer performance for a specific practice
    getPracticePayers: async (practiceGuid, daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/practice/${practiceGuid}/payer-performance?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch practice payer performance');
            return response.json();
        } catch (error) {
            console.error("Error fetching practice payers:", error);
            return [];
        }
    },

    // Get CPT performance for a specific practice
    getPracticeCPT: async (practiceGuid, daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/practice/${practiceGuid}/cpt-performance?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch practice CPT performance');
            return response.json();
        } catch (error) {
            console.error("Error fetching CPT performance:", error);
            return [];
        }
    },

    // Get comprehensive financial metrics (RCM)
    getFinancialMetrics: async (practiceGuid) => {
        try {
            const response = await fetchWithTimeout(`${API_BASE_URL}/api/practices/${practiceGuid}/financial-metrics`);
            if (!response.ok) throw new Error('Failed to fetch financial metrics');
            return response.json();
        } catch (error) {
            console.error("Error fetching financial metrics:", error);
            return null;
        }
    },

    // AI / Advanced Insights Endpoints
    getAiSummary: async (practiceId, daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/practice/${practiceId}/ai/summary?days_back=${daysBack}`);
            if (!response.ok) return null;
            return response.json();
        } catch (error) {
            console.error("AI Summary Error", error);
            return null;
        }
    },

    getAiActionItems: async (practiceId, daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/practice/${practiceId}/ai/actions?days_back=${daysBack}`);
            if (!response.ok) return { action_items: [] };
            return response.json();
        } catch (error) {
            console.error("AI Actions Error", error);
            return { action_items: [] };
        }
    },

    getAiDenialReasons: async (practiceId, daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/practice/${practiceId}/ai/denial-reasons?days_back=${daysBack}`);
            if (!response.ok) return { carc_codes: [] };
            return response.json();
        } catch (error) {
            console.error("AI Denial Reasons Error", error);
            return { carc_codes: [] };
        }
    },

    getAiHighRiskClaims: async (practiceId) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/practice/${practiceId}/ai/high-risk?limit=20`);
            if (!response.ok) return { high_risk_claims: [] };
            return response.json();
        } catch (error) {
            console.error("AI High Risk Error", error);
            return { high_risk_claims: [] };
        }
    },

    // Get Full Report Content (for embedding)
    getPracticeReport: async (practiceId, daysBack = 3650) => {
        try {
            // Increase timeout to 60 seconds for report generation
            const response = await fetchWithTimeout(
                `${API_BASE_URL}/api/v1/reports/practice/${practiceId}/insights/markdown?days_back=${daysBack}`,
                { timeout: 60000 }
            );
            if (!response.ok) throw new Error('Failed to fetch report content');
            const data = await response.json();
            return data.markdown; // Return the raw markdown string
        } catch (error) {
            console.error("Report Fetch Error", error);
            return null;
        }
    },

    // Get structured report data for interactive rendering
    getPracticeReportData: async (practiceId, daysBack = 365) => {
        try {
            const response = await fetchWithTimeout(
                `${API_BASE_URL}/api/v1/reports/practice/${practiceId}/insights/data?days_back=${daysBack}`,
                { timeout: 60000 }
            );
            if (!response.ok) throw new Error('Failed to fetch report data');
            return response.json();
        } catch (error) {
            console.error("Report Data Fetch Error", error);
            return null;
        }
    },

    // Download Detailed Report
    downloadReport: async (practiceId, daysBack = 365) => {
        try {
            const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/reports/practice/${practiceId}/insights/markdown?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to generate report');
            const data = await response.json();

            // Trigger Download
            const blob = new Blob([data.markdown], { type: 'text/markdown' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Practice_Insights_${practiceId}_${new Date().toISOString().split('T')[0]}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            return true;
        } catch (error) {
            console.error("Report Download Error", error);
            throw error;
        }
    },

    // --- Global Analytics ---

    getGlobalPerformanceSummary: async (daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/global/performance-summary?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch global summary');
            return response.json();
        } catch (error) {
            console.error("Error fetching global summary:", error);
            return null;
        }
    },

    getGlobalPayerPerformance: async (daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/global/payer-performance?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch global payers');
            return response.json();
        } catch (error) {
            console.error("Error fetching global payers:", error);
            return [];
        }
    },

    getGlobalCptPerformance: async (daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/global/cpt-performance?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch global CPTs');
            return response.json();
        } catch (error) {
            console.error("Error fetching global CPTs:", error);
            return [];
        }
    },

    getGlobalActionItems: async (daysBack = 90) => {
        try {
            const response = await fetchWithTimeout(`${ANALYTICS_BASE_URL}/global/action-items?days_back=${daysBack}`);
            if (!response.ok) throw new Error('Failed to fetch global action items');
            return response.json();
        } catch (error) {
            console.error("Error fetching global action items:", error);
            return { action_items: [] };
        }
    }
};
