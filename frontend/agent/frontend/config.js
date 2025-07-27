// Configuration for API endpoints
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'https://agent-backend-880917788492.us-central1.run.app' 
    : 'https://agent-dot-YOUR_PROJECT_ID.appspot.com';

// GCP Configuration
const GCP_CONFIG = {
    projectId: 'photosyn2',
    speechConfig: {
        encoding: 'WEBM_OPUS',
        sampleRateHertz: 48000,
        languageCode: 'en-US',
        model: 'latest_long',
        useEnhanced: true,
        enableAutomaticPunctuation: true
    },
    ttsConfig: {
        voice: {
            languageCode: 'en-US',
            name: 'en-US-Neural2-F',
            ssmlGender: 'FEMALE'
        },
        audioConfig: {
            audioEncoding: 'MP3',
            speakingRate: 1.0,
            pitch: 0.0,
            volumeGainDb: 0.0
        }
    }
};