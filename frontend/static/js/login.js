// Control de Red - Login JavaScript
// Author: Héctor Alejandro Pérez (@halexespejo-cmd)

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');

    form.addEventListener('submit', handleLogin);

    // Check if already logged in
    if (api.token) {
        window.location.href = '/dashboard';
    }
});

async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');
    const btnLogin = document.querySelector('.btn-login');

    // Clear previous errors
    errorMessage.classList.remove('active');
    errorMessage.textContent = '';

    // Validate
    if (!username || !password) {
        showError('Por favor completa todos los campos');
        return;
    }

    try {
        // Show loading
        btnLogin.classList.add('loading');
        btnLogin.disabled = true;

        // Login
        await api.login(username, password);

        // Success - redirect
        window.location.href = '/dashboard';

    } catch (error) {
        console.error('Login failed:', error);
        showError('Usuario o contraseña incorrectos');
    } finally {
        btnLogin.classList.remove('loading');
        btnLogin.disabled = false;
    }
}

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.classList.add('active');
}
