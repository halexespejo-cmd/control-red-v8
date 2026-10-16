// Control de Red - Dashboard JavaScript
// Author: Héctor Alejandro Pérez (@halexespejo-cmd)

// State
let currentTheme = localStorage.getItem('theme') || 'light';
let refreshInterval = null;
let charts = {};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Check auth
    if (!api.token) {
        window.location.href = '/login';
        return;
    }

    // Apply theme
    document.documentElement.setAttribute('data-theme', currentTheme);

    // Load user info
    try {
        const user = await api.getMe();
        document.getElementById('userName').textContent = user.username;
    } catch (error) {
        console.error('Failed to load user:', error);
    }

    // Setup event listeners
    setupEventListeners();

    // Initialize charts
    initializeCharts();

    // Load initial data
    await refreshDashboard();

    // Initialize WebSocket for real-time updates
    initWebSocket();

    // Auto-refresh every 30 seconds (fallback si WebSocket falla)
    refreshInterval = setInterval(refreshDashboard, 30000);
});

function setupEventListeners() {
    // Sidebar toggle
    document.getElementById('btnToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('collapsed');
    });

    // Theme toggle
    document.getElementById('btnTheme').addEventListener('click', toggleTheme);

    // Scan button
    document.getElementById('btnScan').addEventListener('click', handleScan);

    // Logout
    document.getElementById('btnLogout').addEventListener('click', handleLogout);

    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            navigateToPage(page);
        });
    });

    // Device filters
    document.getElementById('filterCategory')?.addEventListener('change', filterDevices);
    document.getElementById('filterStatus')?.addEventListener('change', filterDevices);
    document.getElementById('searchDevices')?.addEventListener('input', filterDevices);
}

function navigateToPage(page) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');

    // Update pages
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`page-${page}`)?.classList.add('active');

    // Update title
    const titles = {
        dashboard: 'Dashboard',
        devices: 'Dispositivos',
        network: 'Red',
        users: 'Usuarios',
        settings: 'Configuración'
    };
    document.getElementById('pageTitle').textContent = titles[page];

    // Load page data
    if (page === 'devices') {
        loadDevices();
    } else if (page === 'network') {
        loadNetworkInfo();
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);

    const icon = document.querySelector('#btnTheme i');
    icon.className = currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

async function refreshDashboard() {
    try {
        showLoading(true);

        // Get devices
        const devicesData = await api.getDevices();
        const devices = devicesData.devices || [];

        // Update stats
        document.getElementById('statTotal').textContent = devices.length;
        document.getElementById('statActive').textContent = devices.filter(d => !d.is_blocked).length;
        document.getElementById('statBlocked').textContent = devices.filter(d => d.is_blocked).length;

        // Get network info
        const networkInfo = await api.getNetworkInfo();
        document.getElementById('statNetwork').textContent = networkInfo.ssid || networkInfo.gateway || 'N/A';

        // Update charts
        updateCategoryChart(devices);
        updateActivityChart(devices);

        // Update activity list
        updateActivityList(devices);

    } catch (error) {
        console.error('Failed to refresh dashboard:', error);
        showToast('Error al actualizar datos', 'error');
    } finally {
        showLoading(false);
    }
}

function initializeCharts() {
    // Category chart
    const ctxCategory = document.getElementById('chartCategory').getContext('2d');
    charts.category = new Chart(ctxCategory, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#6366f1',
                    '#10b981',
                    '#f59e0b',
                    '#ef4444',
                    '#8b5cf6'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Activity chart
    const ctxActivity = document.getElementById('chartActivity').getContext('2d');
    charts.activity = new Chart(ctxActivity, {
        type: 'line',
        data: {
            labels: ['6h', '12h', '18h', '24h', '30h', '36h'],
            datasets: [{
                label: 'Dispositivos Activos',
                data: [0, 0, 0, 0, 0, 0],
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function updateCategoryChart(devices) {
    const categories = {};
    devices.forEach(device => {
        const cat = device.category || 'unknown';
        categories[cat] = (categories[cat] || 0) + 1;
    });

    charts.category.data.labels = Object.keys(categories);
    charts.category.data.datasets[0].data = Object.values(categories);
    charts.category.update();
}

function updateActivityChart(devices) {
    // Mock data - in production, get from API
    const activeCount = devices.filter(d => !d.is_blocked).length;
    charts.activity.data.datasets[0].data = [
        activeCount - 2,
        activeCount - 1,
        activeCount,
        activeCount + 1,
        activeCount,
        activeCount
    ];
    charts.activity.update();
}

function updateActivityList(devices) {
    const list = document.getElementById('activityList');
    list.innerHTML = '';

    // Show last 5 devices
    devices.slice(0, 5).forEach(device => {
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.innerHTML = `
            <div class="activity-icon" style="background: ${device.is_blocked ? '#fee2e2' : '#d1fae5'}; color: ${device.is_blocked ? '#ef4444' : '#10b981'}">
                <i class="fas fa-${device.is_blocked ? 'ban' : 'check'}"></i>
            </div>
            <div style="flex: 1">
                <div style="font-weight: 600">${device.custom_name || device.hostname || device.mac}</div>
                <div style="font-size: 0.875rem; color: var(--text-secondary)">${device.ip} - ${device.category || 'unknown'}</div>
            </div>
            <div style="color: var(--text-secondary); font-size: 0.875rem">
                ${formatDateTime(device.last_seen)}
            </div>
        `;
        list.appendChild(item);
    });
}

async function loadDevices() {
    try {
        showLoading(true);
        const data = await api.getDevices();
        const devices = data.devices || [];

        const tbody = document.getElementById('devicesTableBody');
        tbody.innerHTML = '';

        devices.forEach(device => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div style="font-weight: 600">${device.custom_name || device.hostname || 'Unknown'}</div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary)">${device.vendor || 'N/A'}</div>
                </td>
                <td>${device.ip || 'N/A'}</td>
                <td><code>${device.mac}</code></td>
                <td>${device.category || 'unknown'}</td>
                <td>
                    <span class="badge ${device.is_blocked ? 'danger' : 'success'}">
                        ${device.is_blocked ? 'Bloqueado' : 'Activo'}
                    </span>
                </td>
                <td>
                    <button class="btn-action ${device.is_blocked ? 'btn-primary' : 'btn-danger'}" 
                            onclick="toggleDeviceBlock('${device.mac}', ${device.is_blocked})">
                        ${device.is_blocked ? 'Desbloquear' : 'Bloquear'}
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Failed to load devices:', error);
        showToast('Error al cargar dispositivos', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadNetworkInfo() {
    try {
        const info = await api.getNetworkInfo();
        document.getElementById('infoGateway').textContent = info.gateway || 'N/A';
        document.getElementById('infoMyIP').textContent = info.my_ip || 'N/A';
        document.getElementById('infoSSID').textContent = info.ssid || 'N/A';
        document.getElementById('infoRange').textContent = info.network_range || 'N/A';
    } catch (error) {
        console.error('Failed to load network info:', error);
    }
}

async function toggleDeviceBlock(mac, isBlocked) {
    try {
        showLoading(true);
        
        if (isBlocked) {
            await api.unblockDevice(mac);
            showToast('Dispositivo desbloqueado', 'success');
        } else {
            await api.blockDevice(mac);
            showToast('Dispositivo bloqueado', 'success');
        }

        // Reload devices
        await loadDevices();
        await refreshDashboard();
    } catch (error) {
        console.error('Failed to toggle device:', error);
        showToast('Error al cambiar estado', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleScan() {
    try {
        showLoading(true);
        showToast('Iniciando escaneo...', 'info');

        await api.scanNetwork();

        showToast('Escaneo completado', 'success');
        await refreshDashboard();
    } catch (error) {
        console.error('Scan failed:', error);
        showToast('Error al escanear', 'error');
    } finally {
        showLoading(false);
    }
}

function handleLogout() {
    api.logout();
    window.location.href = '/login';
}

function filterDevices() {
    // TODO: Implement client-side filtering
}

// Utilities
function showLoading(show) {
    document.getElementById('loadingOverlay').classList.toggle('active', show);
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function formatDateTime(date) {
    if (!date) return 'N/A';
    const d = new Date(date);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);

    if (diff < 60) return 'Ahora';
    if (diff < 3600) return `${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} horas`;
    return `${Math.floor(diff / 86400)} días`;
}

// Cleanup
window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
