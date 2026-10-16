/**
 * WebSocket Client for Real-time Updates
 * Author: Héctor Alejandro Pérez (@halexespejo-cmd)
 */

class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectDelay = 3000;
        this.maxReconnectDelay = 30000;
        this.reconnectAttempts = 0;
        this.listeners = {};
        this.isConnecting = false;
    }

    connect(token = null) {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }

        this.isConnecting = true;
        const wsUrl = token ? `${this.url}?token=${token}` : this.url;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 3000;
                this.emit('open');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message:', data);
                    
                    // Emit event by type
                    if (data.type) {
                        this.emit(data.type, data);
                    }
                    
                    // General message event
                    this.emit('message', data);
                } catch (e) {
                    console.error('WebSocket parse error:', e);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnecting = false;
                this.emit('error', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket closed');
                this.isConnecting = false;
                this.ws = null;
                this.emit('close');
                this.scheduleReconnect();
            };
        } catch (e) {
            console.error('WebSocket connection error:', e);
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, this.maxReconnectDelay);
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected');
        }
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event, callback) {
        if (!this.listeners[event]) return;
        
        if (callback) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        } else {
            delete this.listeners[event];
        }
    }

    emit(event, data) {
        if (!this.listeners[event]) return;
        
        this.listeners[event].forEach(callback => {
            try {
                callback(data);
            } catch (e) {
                console.error(`Error in ${event} listener:`, e);
            }
        });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Global WebSocket instance
let wsClient = null;

function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    wsClient = new WebSocketClient(wsUrl);
    
    // Get token from localStorage
    const token = localStorage.getItem('token');
    wsClient.connect(token);
    
    // Connection status
    wsClient.on('open', () => {
        showNotification('Connected to real-time updates', 'success');
    });
    
    wsClient.on('close', () => {
        showNotification('Disconnected from server', 'warning');
    });
    
    // Scan events
    wsClient.on('scan_event', (data) => {
        handleScanEvent(data);
    });
    
    // Device events
    wsClient.on('device_discovered', (data) => {
        handleDeviceDiscovered(data);
    });
    
    wsClient.on('device_blocked', (data) => {
        handleDeviceBlocked(data);
    });
    
    wsClient.on('device_unblocked', (data) => {
        handleDeviceUnblocked(data);
    });
    
    // Heartbeat
    wsClient.on('heartbeat', (data) => {
        console.log('Heartbeat:', data.timestamp);
    });
    
    return wsClient;
}

function handleScanEvent(data) {
    const { status, data: eventData } = data;
    
    if (status === 'scan_started') {
        showNotification('Network scan started...', 'info');
        // Show loading indicator
        const scanButton = document.querySelector('.scan-button');
        if (scanButton) {
            scanButton.disabled = true;
            scanButton.textContent = 'Scanning...';
        }
    } else if (status === 'scan_completed') {
        showNotification(
            `Scan completed! Found ${eventData.devices_found} devices`,
            'success'
        );
        // Refresh devices list
        if (typeof loadDevicesPage === 'function') {
            loadDevicesPage();
        }
        // Re-enable button
        const scanButton = document.querySelector('.scan-button');
        if (scanButton) {
            scanButton.disabled = false;
            scanButton.textContent = 'Scan Network';
        }
    } else if (status === 'scan_failed') {
        showNotification(`Scan failed: ${eventData.error}`, 'error');
        const scanButton = document.querySelector('.scan-button');
        if (scanButton) {
            scanButton.disabled = false;
            scanButton.textContent = 'Scan Network';
        }
    }
}

function handleDeviceDiscovered(data) {
    showNotification(`New device discovered: ${data.data.mac}`, 'info');
    // Refresh devices if on devices page
    if (typeof loadDevicesPage === 'function' && window.location.hash === '#devices') {
        loadDevicesPage();
    }
}

function handleDeviceBlocked(data) {
    showNotification(`Device blocked: ${data.data.mac}`, 'success');
}

function handleDeviceUnblocked(data) {
    showNotification(`Device unblocked: ${data.data.mac}`, 'success');
}
