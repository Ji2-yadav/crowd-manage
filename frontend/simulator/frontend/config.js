// Configuration for API endpoints
const CONFIG = {
    // Update these URLs after deploying backend services
    API_BASE_URL: window.location.hostname === 'localhost' 
        ? 'https://simulator-backend-880917788492.us-central1.run.app' 
        : 'https://simulator-dot-YOUR_PROJECT_ID.appspot.com',
    POLL_INTERVAL: 2000,
    DENSITY_THRESHOLDS: {
        LOW: 2.5,
        MEDIUM: 1.5,
        HIGH: 1.2,
        CRITICAL: 1.0
    }
};