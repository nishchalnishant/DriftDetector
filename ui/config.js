// API Configuration
const API_CONFIG = {
    // Production API endpoints
    INFERENCE_API: 'http://4.187.158.249',
    DRIFT_API: 'http://4.187.158.249:8001',
    
    // Endpoints
    ENDPOINTS: {
        HEALTH: '/health',
        PREDICT: '/predict',
        BATCH_PREDICT: '/predict/batch',
        METRICS: '/metrics',
        DRIFT_HEALTH: '/health',
        DRIFT_LATEST: '/drift/latest',
        DRIFT_METRICS: '/metrics'
    },
    
    // Refresh intervals (ms)
    HEALTH_CHECK_INTERVAL: 30000,  // 30 seconds
    DRIFT_CHECK_INTERVAL: 60000,   // 1 minute
    
    // Request timeout
    TIMEOUT: 10000  // 10 seconds
};

// Helper function to build full URL
function getEndpointURL(service, endpoint) {
    const baseURL = service === 'drift' ? API_CONFIG.DRIFT_API : API_CONFIG.INFERENCE_API;
    return `${baseURL}${API_CONFIG.ENDPOINTS[endpoint]}`;
}
