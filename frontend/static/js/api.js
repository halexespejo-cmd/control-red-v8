// Control de Red - API Client
// Author: Héctor Alejandro Pérez (@halexespejo-cmd)

const API_BASE = window.location.origin;

class APIClient {
    constructor() {
        this.token = localStorage.getItem('auth_token');
    }

    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Token expired
            this.logout();
            window.location.href = '/login';
            throw new Error('Unauthorized');
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
        }

        return data;
    }

    // Auth
    async login(username, password) {
        const data = await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        this.token = data.access_token;
        localStorage.setItem('auth_token', this.token);
        return data;
    }

    async register(username, email, password, is_admin = false) {
        return await this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password, is_admin })
        });
    }

    async getMe() {
        return await this.request('/api/auth/me');
    }

    logout() {
        this.token = null;
        localStorage.removeItem('auth_token');
    }

    // Devices
    async getDevices(filters = {}) {
        const params = new URLSearchParams();
        if (filters.blocked_only) params.append('blocked_only', 'true');
        if (filters.category) params.append('category', filters.category);

        const query = params.toString();
        return await this.request(`/api/devices/${query ? '?' + query : ''}`);
    }

    async getDevice(mac) {
        return await this.request(`/api/devices/${mac}`);
    }

    async updateDevice(mac, data) {
        return await this.request(`/api/devices/${mac}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async blockDevice(mac) {
        return await this.request(`/api/devices/${mac}/block`, {
            method: 'POST'
        });
    }

    async unblockDevice(mac) {
        return await this.request(`/api/devices/${mac}/unblock`, {
            method: 'POST'
        });
    }

    async scanNetwork() {
        return await this.request('/api/devices/scan', {
            method: 'POST'
        });
    }

    async getNetworkInfo() {
        return await this.request('/api/devices/network/info');
    }

    // Background Tasks
    async triggerBackgroundScan() {
        return await this.request('/api/tasks/scan', {
            method: 'POST'
        });
    }

    async getTaskStatus(taskId) {
        return await this.request(`/api/tasks/status/${taskId}`);
    }

    // Status
    async getStatus() {
        return await this.request('/api/status');
    }
}

// Export singleton
window.api = new APIClient();
