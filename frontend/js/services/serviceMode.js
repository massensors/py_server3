import { API_URL } from '../config/constants.js';
import { logger } from './logger.js';
import { isParametersTabActive } from '../utils/helpers.js';

// Stan trybu serwisowego
let serviceModeEnabled = false;
let serviceModeAutoRefreshInterval = null;

// Funkcja do wczytywania statusu trybu serwisowego
async function loadServiceModeStatus(isManualRefresh = false) {
    try {
        const response = await fetch(`${API_URL}/service-mode/status`);
        if (response.ok) {
            const data = await response.json();
            serviceModeEnabled = data.enabled;

            const serviceModeToggle = document.getElementById('serviceModeToggle');
            if (serviceModeToggle) {
                serviceModeToggle.checked = data.enabled;
            }

            updateServiceModeStatusDisplay(data.status_message, data.active);

            if (isManualRefresh) {
                logger.addEntry('Status trybu serwisowego odświeżony', 'success');
            }
        }
    } catch (error) {
        console.error('Błąd podczas wczytywania statusu trybu serwisowego:', error);
        updateServiceModeStatusDisplay("Błąd komunikacji", false);

        if (isManualRefresh) {
            logger.addEntry('Błąd podczas odświeżania statusu trybu serwisowego', 'error');
        }
    }
}

// Funkcja do aktualizacji wyświetlania statusu
function updateServiceModeStatusDisplay(statusMessage, isActive = false) {
    const statusElement = document.getElementById('serviceModeStatus');
    if (!statusElement) return;

    const statusText = statusElement.querySelector('.status-text');

    if (statusText) {
        statusText.textContent = statusMessage;
        statusElement.className = 'service-mode-status';

        if (isActive || statusMessage.includes('aktywny')) {
            statusElement.classList.add('status-active');
        } else if (statusMessage.includes('ruchu')) {
            statusElement.classList.add('status-warning');
        } else if (statusMessage.includes('błąd') || statusMessage.includes('Błąd') || statusMessage.includes('Nieaktywny')) {
            statusElement.classList.add('status-error');
        } else {
            statusElement.classList.add('status-inactive');
        }
    }
}

function startAutoRefresh() {
    return; // Wyłączone
}

function stopAutoRefresh() {
    if (serviceModeAutoRefreshInterval) {
        clearInterval(serviceModeAutoRefreshInterval);
        serviceModeAutoRefreshInterval = null;
    }
}

// Inicjalizuje obsługę trybu serwisowego
export function initServiceMode() {
    const serviceModeToggle = document.getElementById('serviceModeToggle');
    const refreshServiceModeBtn = document.getElementById('refreshServiceMode');

    if (serviceModeToggle) {
        loadServiceModeStatus(true);

        serviceModeToggle.addEventListener('change', async function () {
            const enabled = this.checked;

            try {
                const response = await fetch(`${API_URL}/service-mode/toggle`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({enabled: enabled})
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                serviceModeEnabled = data.enabled;

                updateServiceModeStatusDisplay(data.status_message, data.active);

                logger.addEntry(
                    `Tryb serwisowy ${serviceModeEnabled ? 'WŁĄCZONY' : 'WYŁĄCZONY'} - ${data.status_message}`,
                    serviceModeEnabled ? 'success' : 'info'
                );

            } catch (error) {
                this.checked = !enabled;
                updateServiceModeStatusDisplay("Błąd komunikacji", false);
                logger.addEntry(`Błąd podczas przełączania trybu serwisowego: ${error.message}`, 'error');
            }
        });
    }

    if (refreshServiceModeBtn) {
        refreshServiceModeBtn.addEventListener('click', async function () {
            logger.addEntry('Ręczne odświeżanie statusu trybu serwisowego...', 'info');
            await loadServiceModeStatus(true);
        });
    }

    // Event listeners dla lifecycle
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            stopAutoRefresh();
        } else if (isParametersTabActive()) {
            startAutoRefresh();
        }
    });

    window.addEventListener('beforeunload', function () {
        stopAutoRefresh();
    });
}