// Google Cloud Speech Services for STT and TTS
class SpeechServices {
    constructor() {
        this.recognition = null;
        this.isRecording = false;
        this.audioContext = null;
        this.ttsAudio = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        // Initialize Web Speech API for STT (fallback)
        this.initializeSpeechRecognition();
        // Initialize MediaRecorder for GCP STT
        this.initializeMediaRecorder();
    }
    
    initializeSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.error('Speech Recognition API not supported');
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
        this.recognition.onstart = () => {
            console.log('Speech recognition started');
            this.isRecording = true;
        };
        
        this.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0])
                .map(result => result.transcript)
                .join('');
            
            if (event.results[0].isFinal) {
                this.onTranscriptReceived(transcript);
            } else {
                this.onInterimTranscript(transcript);
            }
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isRecording = false;
            this.onRecordingStateChange(false);
        };
        
        this.recognition.onend = () => {
            console.log('Speech recognition ended');
            this.isRecording = false;
            this.onRecordingStateChange(false);
        };
    }
    
    startRecording() {
        if (this.isRecording) {
            this.stopRecording();
            return;
        }
        
        // Try to use MediaRecorder for GCP STT
        if (this.mediaRecorder && this.mediaRecorder.state === 'inactive') {
            try {
                this.audioChunks = [];
                this.mediaRecorder.start();
                this.isRecording = true;
                this.onRecordingStateChange(true);
                
                // Stop recording after 60 seconds max
                setTimeout(() => {
                    if (this.isRecording) {
                        this.stopRecording();
                    }
                }, 60000);
            } catch (error) {
                console.error('MediaRecorder error:', error);
                // Fallback to Web Speech API
                this.startWebSpeechRecognition();
            }
        } else {
            // Fallback to Web Speech API
            this.startWebSpeechRecognition();
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.onRecordingStateChange(false);
        } else if (this.recognition && this.isRecording) {
            this.recognition.stop();
        }
    }
    
    async initializeMediaRecorder() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                this.audioChunks = [];
                
                // Convert to base64 and send to backend
                const reader = new FileReader();
                reader.onloadend = async () => {
                    const base64Audio = reader.result.split(',')[1];
                    await this.sendAudioToBackend(base64Audio);
                };
                reader.readAsDataURL(audioBlob);
            };
        } catch (error) {
            console.error('MediaRecorder initialization error:', error);
        }
    }
    
    async sendAudioToBackend(base64Audio) {
        try {
            const response = await fetch(CHAT_API_URL + '/speech-to-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    audio: base64Audio
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.transcript) {
                    this.onTranscriptReceived(data.transcript);
                }
            } else {
                console.error('STT API error:', await response.text());
                // Fallback to Web Speech API
                this.startWebSpeechRecognition();
            }
        } catch (error) {
            console.error('STT request error:', error);
            // Fallback to Web Speech API
            this.startWebSpeechRecognition();
        }
    }
    
    startWebSpeechRecognition() {
        if (this.recognition && !this.isRecording) {
            try {
                this.recognition.start();
                this.onRecordingStateChange(true);
            } catch (error) {
                console.error('Web Speech recognition error:', error);
            }
        }
    }
    
    // Text-to-Speech using Google Cloud TTS API
    async speakText(text, voiceSettings = {}) {
        try {
            // First try Google Cloud TTS
            return await this.googleCloudTTS(text, voiceSettings);
        } catch (error) {
            console.error('GCP TTS error, falling back to Web Speech:', error);
            
            // Fallback to Web Speech API
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = voiceSettings.languageCode || 'en-US';
            utterance.rate = voiceSettings.speakingRate || 1.0;
            utterance.pitch = voiceSettings.pitch || 1.0;
            
            // Cancel any ongoing speech
            window.speechSynthesis.cancel();
            
            return new Promise((resolve, reject) => {
                utterance.onend = () => resolve();
                utterance.onerror = (event) => reject(event);
                window.speechSynthesis.speak(utterance);
            });
        }
    }
    
    // Google Cloud TTS API call
    async googleCloudTTS(text, voiceSettings = {}) {
        try {
            const response = await fetch(CHAT_API_URL + '/text-to-speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    voice: {
                        languageCode: voiceSettings.languageCode || 'en-US',
                        name: voiceSettings.voiceName || 'en-US-Neural2-F',
                        ssmlGender: voiceSettings.ssmlGender || 'FEMALE'
                    },
                    audioConfig: {
                        audioEncoding: 'MP3',
                        speakingRate: voiceSettings.speakingRate || 1.0,
                        pitch: voiceSettings.pitch || 0.0
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error('TTS API request failed');
            }
            
            const data = await response.json();
            
            // Play the audio
            const audio = new Audio('data:audio/mp3;base64,' + data.audioContent);
            this.ttsAudio = audio;
            
            return new Promise((resolve, reject) => {
                audio.onended = () => {
                    this.ttsAudio = null;
                    resolve();
                };
                audio.onerror = (error) => {
                    this.ttsAudio = null;
                    reject(error);
                };
                audio.play().catch(reject);
            });
        } catch (error) {
            console.error('Google Cloud TTS error:', error);
            throw error; // Let the calling function handle fallback
        }
    }
    
    // Callbacks to be overridden
    onTranscriptReceived(transcript) {
        console.log('Final transcript:', transcript);
    }
    
    onInterimTranscript(transcript) {
        console.log('Interim transcript:', transcript);
    }
    
    onRecordingStateChange(isRecording) {
        console.log('Recording state:', isRecording);
    }
    
    // Stop any ongoing TTS
    stopSpeaking() {
        window.speechSynthesis.cancel();
        if (this.ttsAudio) {
            this.ttsAudio.pause();
            this.ttsAudio = null;
        }
    }
}

// Export for use in chat app
window.SpeechServices = SpeechServices;