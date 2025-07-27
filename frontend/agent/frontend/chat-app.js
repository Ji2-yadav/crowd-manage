// Chat application JavaScript
const CHAT_API_URL = 'https://agent-backend-880917788492.us-central1.run.app';
const BACKEND_API_URL = 'https://simulator-backend-880917788492.us-central1.run.app';

// Generate a unique session ID
const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const chatForm = document.getElementById('chat-form');
const resetBtn = document.getElementById('reset-btn');
const functionCallsContent = document.getElementById('function-calls-content');
const toggleFunctionsBtn = document.getElementById('toggle-functions');
const functionCallsPanel = document.getElementById('function-calls');
const voiceBtn = document.getElementById('voice-btn');

// Initialize speech services
const speechServices = new SpeechServices();

// Check API connectivity
async function checkAPIStatus() {
    try {
        const response = await fetch(BACKEND_API_URL + '/state');
        if (response.ok) {
            document.getElementById('backend-api-status').textContent = 'Connected ✓';
            document.getElementById('backend-api-status').style.color = '#4CAF50';
        }
    } catch (error) {
        document.getElementById('backend-api-status').textContent = 'Disconnected ✗';
        document.getElementById('backend-api-status').style.color = '#f44336';
    }
}

// Add message to chat
function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    if (isUser) {
        messageContent.innerHTML = `<strong>Commander:</strong> ${escapeHtml(content)}`;
    } else {
        messageContent.innerHTML = `<strong>Drishti AI:</strong> ${formatMessage(content)}`;
        
        // Add TTS button for assistant messages
        const ttsButton = document.createElement('button');
        ttsButton.className = 'tts-button';
        ttsButton.title = 'Read message aloud';
        ttsButton.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
            </svg>
        `;
        
        ttsButton.addEventListener('click', async () => {
            if (ttsButton.classList.contains('playing')) {
                speechServices.stopSpeaking();
                ttsButton.classList.remove('playing');
            } else {
                ttsButton.classList.add('playing');
                try {
                    // Extract text content without HTML
                    const textContent = messageContent.textContent.replace('Drishti AI: ', '');
                    await speechServices.speakText(textContent);
                    ttsButton.classList.remove('playing');
                } catch (error) {
                    console.error('TTS error:', error);
                    ttsButton.classList.remove('playing');
                }
            }
        });
        
        messageContent.appendChild(ttsButton);
    }
    
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message content (convert markdown-like formatting)
function formatMessage(content) {
    // Escape HTML first
    let formatted = escapeHtml(content);
    
    // Convert markdown-like formatting
    formatted = formatted
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
    
    return formatted;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Add function calls to chat as action messages
function displayFunctionCalls(functionCalls) {
    if (!functionCalls || functionCalls.length === 0) return;
    
    functionCalls.forEach(call => {
        const actionDiv = document.createElement('div');
        actionDiv.className = 'message action';
        
        const icon = getFunctionIcon(call.function_name);
        const actionName = formatActionName(call.function_name);
        const args = call.args ? Object.entries(call.args)
            .map(([key, value]) => `${key}: ${value}`)
            .join(', ') : '';
        
        let content = `<div class="action-header"><span class="action-icon">${icon}</span> <strong>${actionName}</strong></div>`;
        
        if (args) {
            content += `<div class="action-args">${args}</div>`;
        }
        
        // Don't display tool results in the frontend
        // The agent will summarize the results in their response
        
        if (call.error) {
            content += `<div class="action-error">❌ ${escapeHtml(call.error)}</div>`;
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content action-content';
        messageContent.innerHTML = content;
        
        actionDiv.appendChild(messageContent);
        chatMessages.appendChild(actionDiv);
    });
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format action names to be more readable
function formatActionName(functionName) {
    const nameMap = {
        'get_zone_summary': 'Checking Zone Status',
        'get_personnel_status': 'Finding Available Personnel',
        'dispatch_unit': 'Dispatching Unit',
        'make_announcement': 'Making Announcement',
        'toggle_gate': 'Toggling Gate',
        'evacuate_zone': 'Initiating Evacuation',
        'activate_crowd_control_protocol': 'Activating Crowd Control',
        'list_all_zones': 'Listing Zones',
        'get_personnel_by_zone': 'Checking Zone Personnel',
        'list_gates_in_zone': 'Checking Zone Gates',
        'get_map': 'Getting Map'
    };
    return nameMap[functionName] || functionName;
}

// Function removed - no longer displaying tool results in frontend

// Get icon for function
function getFunctionIcon(functionName) {
    const icons = {
        'get_zone_summary': '📊',
        'get_personnel_status': '👥',
        'dispatch_unit': '🚨',
        'make_announcement': '📢',
        'toggle_gate': '🚪',
        'evacuate_zone': '🚸',
        'activate_crowd_control_protocol': '⚠️',
        'list_all_zones': '🗺️',
        'get_personnel_by_zone': '👮',
        'list_gates_in_zone': '🚪',
        'get_map': '🗺️'
    };
    return icons[functionName] || '🔧';
}

// Poll for queue updates
async function pollForUpdates(loadingDiv) {
    let complete = false;
    
    while (!complete) {
        try {
            const response = await fetch(CHAT_API_URL + '/poll', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });
            
            const data = await response.json();
            
            // Process items from queue
            for (const item of data.items) {
                if (item.type === 'function_call') {
                    // Remove loading if still present
                    if (loadingDiv && loadingDiv.parentNode) {
                        loadingDiv.remove();
                        loadingDiv = null;
                    }
                    // Display function call immediately
                    displayFunctionCalls([item.content]);
                } else if (item.type === 'text') {
                    // Remove loading if still present
                    if (loadingDiv && loadingDiv.parentNode) {
                        loadingDiv.remove();
                        loadingDiv = null;
                    }
                    // Display text response
                    addMessage(item.content, false);
                } else if (item.type === 'error') {
                    if (loadingDiv && loadingDiv.parentNode) {
                        loadingDiv.remove();
                        loadingDiv = null;
                    }
                    addMessage(`Error: ${item.content}`, false);
                    complete = true;
                }
            }
            
            complete = data.complete;
            
            // Small delay between polls
            if (!complete) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        } catch (error) {
            if (loadingDiv && loadingDiv.parentNode) {
                loadingDiv.remove();
            }
            addMessage(`Polling error: ${error.message}`, false);
            complete = true;
        }
    }
    
    // Clean up loading indicator if still present
    if (loadingDiv && loadingDiv.parentNode) {
        loadingDiv.remove();
    }
}

// Send message to chat API
async function sendMessage(message) {
    // Add user message to chat
    addMessage(message, true);
    
    // Show loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading';
    loadingDiv.innerHTML = '<div class="message-content"><strong>Drishti AI:</strong> <span class="dots">...</span></div>';
    chatMessages.appendChild(loadingDiv);
    
    try {
        const response = await fetch(CHAT_API_URL + '/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'processing') {
            // Start polling for updates
            await pollForUpdates(loadingDiv);
        } else if (data.error) {
            loadingDiv.remove();
            addMessage(`Error: ${data.error}`, false);
        } else {
            // Fallback to old behavior if needed
            loadingDiv.remove();
            if (data.function_calls && data.function_calls.length > 0) {
                displayFunctionCalls(data.function_calls);
            }
            if (data.response) {
                addMessage(data.response, false);
            }
        }
    } catch (error) {
        loadingDiv.remove();
        addMessage(`Connection error: ${error.message}`, false);
    }
}

// Handle form submission
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    messageInput.value = '';
    await sendMessage(message);
});

// Handle reset button
resetBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to reset the conversation?')) {
        try {
            await fetch(CHAT_API_URL + '/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });
            
            // Clear chat messages
            chatMessages.innerHTML = `
                <div class="message assistant">
                    <div class="message-content">
                        <strong>Drishti AI:</strong> Command center online. I'm monitoring all zones for potential safety issues. How can I assist you today?
                    </div>
                </div>
            `;
            
            // No need to clear function panel anymore
        } catch (error) {
            console.error('Error resetting session:', error);
        }
    }
});

// Remove function panel toggle since we're showing actions inline

// Add some example commands as placeholders
const exampleCommands = [
    "What's the status of all zones?",
    "Show me the hall 1 lower zone",
    "Is there a medical emergency in any zone?",
    "Check crowd density in entrance lobby",
    "Dispatch medical unit to food court",
    "Open emergency exits in hall 2"
];

// Randomly set placeholder
messageInput.placeholder = exampleCommands[Math.floor(Math.random() * exampleCommands.length)];

// Poll for alerts
async function pollForAlerts() {
    try {
        const response = await fetch(CHAT_API_URL + '/poll-alerts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        
        const data = await response.json();
        
        // Process each alert
        for (const alert of data.alerts) {
            // Display alert notification as assistant message
            addMessage(alert.message, false);
            
            // Show loading indicator for agent's response
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message assistant loading';
            loadingDiv.innerHTML = '<div class="message-content"><strong>Drishti AI:</strong> <span class="dots">...</span></div>';
            chatMessages.appendChild(loadingDiv);
            
            // Start polling for the agent's response to this alert
            await pollForUpdates(loadingDiv);
        }
    } catch (error) {
        console.error('Error polling for alerts:', error);
    }
}

// Check API status on load
checkAPIStatus();
setInterval(checkAPIStatus, 5000); // Check every 5 seconds

// Poll for alerts every 2 seconds
setInterval(pollForAlerts, 2000);

// Voice input handling
voiceBtn.addEventListener('click', () => {
    speechServices.startRecording();
});

// Configure speech services callbacks
speechServices.onTranscriptReceived = (transcript) => {
    messageInput.value = transcript;
    // Optionally auto-submit
    if (transcript.trim()) {
        sendMessage(transcript);
    }
};

speechServices.onInterimTranscript = (transcript) => {
    // Show interim results in the input field
    messageInput.value = transcript;
};

speechServices.onRecordingStateChange = (isRecording) => {
    if (isRecording) {
        voiceBtn.classList.add('recording');
        voiceBtn.title = 'Stop recording';
    } else {
        voiceBtn.classList.remove('recording');
        voiceBtn.title = 'Start voice input';
    }
};