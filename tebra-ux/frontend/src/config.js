/**
 * Centralized configuration for the Talisman Analytics frontend.
 * Dynamically determines the API base URL based on the current hostname.
 */

const getApiBaseUrl = () => {
    // If we're on localhost, we can still use localhost for the backend,
    // but if we're on a LAN IP, we need the backend to be on that same IP.
    const hostname = window.location.hostname;
    return `http://${hostname}:8000`;
};

export const API_BASE_URL = getApiBaseUrl();
export const ANALYTICS_BASE_URL = `${API_BASE_URL}/api/v1/analytics`;

export default {
    API_BASE_URL,
    ANALYTICS_BASE_URL
};
