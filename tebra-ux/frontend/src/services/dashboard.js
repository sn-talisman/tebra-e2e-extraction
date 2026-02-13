import { API_BASE_URL } from '../config';

export const dashboardService = {
    getMetrics: async () => {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/metrics`);
        if (!response.ok) throw new Error('Failed to fetch dashboard metrics');
        return response.json();
    },

    getRecentActivity: async () => {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/recent-activity`);
        if (!response.ok) throw new Error('Failed to fetch recent activity');
        return response.json();
    },

    getStatusDistribution: async (daysBack = 90) => {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/status-distribution?days_back=${daysBack}`);
        if (!response.ok) throw new Error('Failed to fetch status distribution');
        return response.json();
    },

    getPracticePerformance: async (daysBack = 90) => {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/practice-performance?days_back=${daysBack}`);
        if (!response.ok) throw new Error('Failed to fetch practice performance');
        return response.json();
    }
};
