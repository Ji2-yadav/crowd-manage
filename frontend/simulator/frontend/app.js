// Configuration
const CONFIG = {
    API_BASE_URL: 'https://simulator-backend-880917788492.us-central1.run.app',
    POLL_INTERVAL: 2000, // 2 seconds
    DENSITY_THRESHOLDS: {
        LOW: 2.5,
        MEDIUM: 1.5,
        HIGH: 1.2,
        CRITICAL: 1.0
    }
};

// Application State
const AppState = {
    selectedEventType: null,
    currentState: null,
    isConnected: false
};

// Event Type Definitions
const EVENT_TYPES = {
    Overcrowding: { icon: '👥', color: '#ffb86c' },
    MedicalEmergency: { icon: '🏥', color: '#ff5555' },
    Fire: { icon: '🔥', color: '#ff5555' },
    SecurityThreat: { icon: '🚨', color: '#bd93f9' },
    Stampede: { icon: '⚠️', color: '#ff5555' }
};

// API Service
class ApiService {
    static async fetchState() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/state`);
            if (!response.ok) throw new Error('Failed to fetch state');
            return await response.json();
        } catch (error) {
            console.error('Error fetching state:', error);
            throw error;
        }
    }

    static async triggerEvent(eventType, zoneId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/event`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: eventType, zone: zoneId })
            });
            if (!response.ok) throw new Error('Failed to trigger event');
            return await response.json();
        } catch (error) {
            console.error('Error triggering event:', error);
            throw error;
        }
    }

    static async toggleGate(gateId, status) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/actions/toggle-gate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ gate_id: gateId, status })
            });
            if (!response.ok) throw new Error('Failed to toggle gate');
            return await response.json();
        } catch (error) {
            console.error('Error toggling gate:', error);
            throw error;
        }
    }
}

// Logger Service
class Logger {
    static log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span>
            <span class="log-${type}">${message}</span>
        `;
        
        const logContainer = document.getElementById('event-log');
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
        
        // Also log to console
        console.log(`[${timestamp}] ${message}`);
    }
}

// Zone Renderer
class ZoneRenderer {
    static getDensityClass(density) {
        if (density === 0) return 'density-low'; // Empty zone
        if (density >= CONFIG.DENSITY_THRESHOLDS.LOW) return 'density-low';
        if (density >= CONFIG.DENSITY_THRESHOLDS.MEDIUM) return 'density-medium';
        if (density >= CONFIG.DENSITY_THRESHOLDS.HIGH) return 'density-high';
        return 'density-critical';
    }

    static getDensityPercentage(density) {
        // Special case: density 0 means empty zone
        if (density === 0) return 0;
        
        // Inverse relationship - lower density means more crowded
        const maxDensity = 5; // 5 sqm per person is very spacious
        const percentage = Math.min(100, Math.max(0, (1 - density / maxDensity) * 100));
        return percentage;
    }

    static renderZone(zoneId, zoneData) {
        const hasAlerts = zoneData.active_alerts && zoneData.active_alerts.length > 0;
        const hasFire = zoneData.active_alerts && zoneData.active_alerts.includes('Fire');
        
        return `
            <div class="zone ${hasFire ? 'has-fire' : ''}" data-zone-id="${zoneId}">
                <div class="zone-name">${zoneId.replace(/_/g, ' ').toUpperCase()}</div>
                <div class="zone-stats">
                    <div>People: ${zoneData.num_people.toLocaleString()}</div>
                    <div>Density: ${zoneData.density_sqm_per_person.toFixed(2)} m²/person</div>
                    <div>Risk: ${zoneData.bottleneck_risk}</div>
                </div>
                <div class="density-bar">
                    <div class="density-fill ${this.getDensityClass(zoneData.density_sqm_per_person)}" 
                         style="width: ${this.getDensityPercentage(zoneData.density_sqm_per_person)}%"></div>
                </div>
                ${hasAlerts ? `
                    <div class="zone-alerts">
                        ${zoneData.active_alerts.map(alert => `
                            <div class="alert-indicator" title="${alert}">
                                ${EVENT_TYPES[alert]?.icon || '⚠️'}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    static renderAllZones(zones) {
        // Update SVG zones instead of creating HTML
        Object.entries(zones).forEach(([zoneId, zoneData]) => {
            const zoneGroup = document.querySelector(`[data-zone="${zoneId}"]`);
            if (!zoneGroup) return;
            
            // Update zone shape color based on density
            const zoneShape = zoneGroup.querySelector('.zone-shape');
            const densityClass = this.getDensityClass(zoneData.density_sqm_per_person);
            
            // Remove all density classes and add the current one
            zoneShape.classList.remove('density-low', 'density-medium', 'density-high', 'density-critical');
            zoneShape.classList.add(densityClass);
            
            // Add fire animation if needed
            if (zoneData.active_alerts && zoneData.active_alerts.includes('Fire')) {
                zoneShape.classList.add('has-fire');
            } else {
                zoneShape.classList.remove('has-fire');
            }
            
            // Update people count
            const peopleText = zoneGroup.querySelector('.zone-people');
            peopleText.textContent = `${zoneData.num_people.toLocaleString()} people`;
            
            // Update alerts
            const alertsGroup = zoneGroup.querySelector('.zone-alerts-group');
            alertsGroup.innerHTML = '';
            
            if (zoneData.active_alerts && zoneData.active_alerts.length > 0) {
                zoneData.active_alerts.forEach((alert, index) => {
                    const alertG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                    alertG.setAttribute('transform', `translate(${index * 32}, 0)`);
                    
                    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                    rect.setAttribute('class', `zone-alert-icon ${alert === 'MedicalEmergency' ? 'medical-emergency' : ''}`);
                    rect.setAttribute('width', '28');
                    rect.setAttribute('height', '28');
                    rect.setAttribute('rx', '6');
                    
                    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    text.setAttribute('x', '14');
                    text.setAttribute('y', '14');
                    text.setAttribute('class', 'zone-alert-emoji');
                    text.textContent = EVENT_TYPES[alert]?.icon || '⚠️';
                    
                    alertG.appendChild(rect);
                    alertG.appendChild(text);
                    alertsGroup.appendChild(alertG);
                });
            }
        });
    }
}

// Info Panel Renderer
class InfoPanelRenderer {
    static renderZoneDetails(zoneId, zoneData) {
        const detailsEl = document.getElementById('zone-details');
        detailsEl.innerHTML = `
            <h3>${zoneId.replace(/_/g, ' ').toUpperCase()}</h3>
            <p><strong>Area:</strong> ${zoneData.area_sqm.toLocaleString()} m²</p>
            <p><strong>People:</strong> ${zoneData.num_people.toLocaleString()}</p>
            <p><strong>Density:</strong> ${zoneData.density_sqm_per_person.toFixed(2)} m²/person</p>
            <p><strong>Risk Level:</strong> <span class="risk-${zoneData.bottleneck_risk}">${zoneData.bottleneck_risk}</span></p>
            ${zoneData.active_alerts && zoneData.active_alerts.length > 0 ? `
                <p><strong>Active Alerts:</strong></p>
                <ul>
                    ${zoneData.active_alerts.map(alert => `<li>${alert}</li>`).join('')}
                </ul>
            ` : ''}
        `;
    }

    static renderPersonnel(personnel) {
        const listEl = document.getElementById('personnel-list');
        listEl.innerHTML = Object.entries(personnel)
            .map(([id, person]) => `
                <div class="personnel-item">
                    <div>
                        <strong>${person.name}</strong><br>
                        <small>${person.type} - ${person.current_zone}</small>
                    </div>
                    <span class="status-badge status-${person.status}">${person.status}</span>
                </div>
            `).join('');
    }

    static renderGates(gates) {
        const listEl = document.getElementById('gates-list');
        listEl.innerHTML = Object.entries(gates)
            .map(([id, gate]) => `
                <div class="gate-item" data-gate-id="${id}">
                    <div>
                        <strong>${id.replace(/_/g, ' ')}</strong><br>
                        <small>${gate.type} - ${gate.zone_id}</small>
                    </div>
                    <span class="status-badge status-${gate.status}">${gate.status}</span>
                </div>
            `).join('');
    }
}

// Event Handlers
class EventHandlers {
    static setupEventButtons() {
        document.querySelectorAll('.event-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Remove active class from all buttons
                document.querySelectorAll('.event-btn').forEach(b => b.classList.remove('active'));
                
                // Add active class to clicked button
                btn.classList.add('active');
                
                // Update selected event type
                AppState.selectedEventType = btn.dataset.event;
                document.getElementById('selected-event-type').textContent = AppState.selectedEventType;
                
                Logger.log(`Selected event type: ${AppState.selectedEventType}`, 'info');
            });
        });
    }

    static setupZoneClicks() {
        document.getElementById('zones-container').addEventListener('click', async (e) => {
            // Check if click is on SVG zone
            const zoneGroup = e.target.closest('.zone-group');
            if (!zoneGroup) return;

            const zoneId = zoneGroup.dataset.zone;
            
            // Always show zone details
            if (AppState.currentState && AppState.currentState.zones[zoneId]) {
                InfoPanelRenderer.renderZoneDetails(zoneId, AppState.currentState.zones[zoneId]);
                
                // Update visual selection
                document.querySelectorAll('.zone-group').forEach(z => z.classList.remove('selected'));
                zoneGroup.classList.add('selected');
            }

            // If an event type is selected, trigger it
            if (AppState.selectedEventType) {
                try {
                    const result = await ApiService.triggerEvent(AppState.selectedEventType, zoneId);
                    Logger.log(`Event triggered: ${AppState.selectedEventType} in ${zoneId}`, 'success');
                    
                    // Clear selection
                    AppState.selectedEventType = null;
                    document.getElementById('selected-event-type').textContent = 'None';
                    document.querySelectorAll('.event-btn').forEach(b => b.classList.remove('active'));
                    
                    // Refresh state immediately
                    await updateState();
                } catch (error) {
                    Logger.log(`Failed to trigger event: ${error.message}`, 'error');
                }
            } else {
                Logger.log(`Zone clicked: ${zoneId}`, 'info');
            }
        });
    }

    static setupGateClicks() {
        document.getElementById('gates-list').addEventListener('click', async (e) => {
            const gateEl = e.target.closest('.gate-item');
            if (!gateEl) return;

            const gateId = gateEl.dataset.gateId;
            const currentGate = AppState.currentState.gates[gateId];
            const newStatus = currentGate.status === 'open' ? 'closed' : 'open';

            try {
                await ApiService.toggleGate(gateId, newStatus);
                Logger.log(`Gate ${gateId} ${newStatus}`, 'success');
                await updateState();
            } catch (error) {
                Logger.log(`Failed to toggle gate: ${error.message}`, 'error');
            }
        });
    }
}

// Main update function
async function updateState() {
    try {
        const state = await ApiService.fetchState();
        AppState.currentState = state;
        
        // Update connection status
        if (!AppState.isConnected) {
            AppState.isConnected = true;
            const statusEl = document.getElementById('connection-status');
            statusEl.textContent = 'Connected';
            statusEl.classList.add('connected');
            Logger.log('Connected to server', 'success');
        }
        
        // Update UI
        ZoneRenderer.renderAllZones(state.zones);
        InfoPanelRenderer.renderPersonnel(state.personnel);
        InfoPanelRenderer.renderGates(state.gates);
        
        // Update last update time
        document.getElementById('last-update').textContent = 
            `Last update: ${new Date().toLocaleTimeString()}`;
            
    } catch (error) {
        AppState.isConnected = false;
        const statusEl = document.getElementById('connection-status');
        statusEl.textContent = 'Disconnected';
        statusEl.classList.remove('connected');
        Logger.log('Connection lost', 'error');
    }
}

// Initialize application
function initializeApp() {
    Logger.log('Initializing Project Drishti Dashboard...', 'info');
    
    // Setup event handlers
    EventHandlers.setupEventButtons();
    EventHandlers.setupZoneClicks();
    EventHandlers.setupGateClicks();
    
    // Start polling for updates
    updateState();
    setInterval(updateState, CONFIG.POLL_INTERVAL);
    
    Logger.log('Dashboard initialized successfully', 'success');
}

// Start the application when DOM is ready
document.addEventListener('DOMContentLoaded', initializeApp);