import { API_URL } from '../config/constants.js';
import { logger } from './logger.js';
import { isParametersTabActive } from '../utils/helpers.js';

// Stan trybu serwisowego
let serviceModeEnabled = false;
let serviceModeAutoRefreshInterval = null;

// UPROSZCZONA FUNKCJA - toggleServiceMode
async function toggleServiceMode(enabled) {
    try {
        const response = await fetchWithAuth(`${API_URL}/service-mode/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                enabled: enabled
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Odśwież status
        await refreshServiceModeStatus();

        logger.addEntry(`Tryb serwisowy: ${enabled ? 'WŁĄCZONY' : 'WYŁĄCZONY'}`, enabled ? 'success' : 'info');

        return data;

    } catch (error) {
        logger.addEntry(`❌ Błąd zmiany trybu serwisowego: ${error.message}`, 'error');

        // Przywróć poprzedni stan przełącznika
        const toggle = document.getElementById('serviceModeToggle');
        if (toggle) {
            toggle.checked = !enabled;
        }

        throw error;
    }
}

// Funkcja do odświeżania statusu z wykorzystaniem MachineStateObserver
async function refreshServiceModeStatus() {
    try {
        // Pobierz dane z MachineStateObserver
        const machineStateResponse = await fetchWithAuth(`${API_URL}/machine-state/status`);
        const serviceResponse = await fetchWithAuth(`${API_URL}/service-mode/status`);

        if (machineStateResponse.ok && serviceResponse.ok) {
            const machineData = await machineStateResponse.json();
            const serviceData = await serviceResponse.json();

            if (machineData.success) {
                const observationInfo = machineData.data;

                serviceModeEnabled = serviceData.enabled;

                const serviceModeToggle = document.getElementById('serviceModeToggle');
                if (serviceModeToggle) {
                    serviceModeToggle.checked = serviceData.enabled;
                }

                // Stwórz bardziej szczegółowy komunikat statusu
                const statusMessage = createDetailedStatusMessage(observationInfo, serviceData);

                updateServiceModeStatusDisplay(statusMessage, serviceData.active);

                // Dodaj szczegółowe informacje do loggera
                const stateVariables = observationInfo.state_variables;
                const networkObs = observationInfo.network_observations;

                logger.addEntry(
                    `📊 Stan aplikacji: ${observationInfo.observed_state} | ` +
                    `Request: ${networkObs.last_request_value} | ` +
                    `Command: ${networkObs.last_command_id_hex || 'brak'}`,
                    'info'
                );
            }
        }
    } catch (error) {
        console.error('Błąd podczas wczytywania statusu trybu serwisowego:', error);
        updateServiceModeStatusDisplay("Błąd komunikacji", false);
        logger.addEntry('❌ Błąd podczas odświeżania statusu trybu serwisowego', 'error');
    }
}

// Funkcja do tworzenia szczegółowego komunikatu statusu
function createDetailedStatusMessage(observationInfo, serviceData) {
    const currentState = observationInfo.observed_state;
    const stateVariables = observationInfo.state_variables;
    const networkObs = observationInfo.network_observations;

    //let statusMessage = `${serviceData.status_message}`;
    let statusMessage = '';

    // Dodaj informację o stanie przenośnika
    if (serviceData.conveyor_status) {
        switch (serviceData.conveyor_status) {
            case 'stopped':
                statusMessage += '🛑 Przenośnik: ZATRZYMANY';
                break;
            case 'running':
                statusMessage += '▶️ Przenośnik: W RUCHU';
                break;
            case 'error':
                statusMessage += '⚠️ Przenośnik: BŁĄD';
                break;
            case 'unknown':
                statusMessage += '❓ Przenośnik: NIEZNANY';
                break;
            default:
                statusMessage += `Przenośnik: ${serviceData.conveyor_status}`;
        }
        statusMessage += ' | ';
    }


    // Dodaj informację o stanie state machine
    switch (currentState) {
        case 'SERVICE_MODE':
            statusMessage += '  State Machine: Tryb serwisowy aktywny';
            break;
        case 'SERVICE_MODE_REQUEST_DYNAMIC':
            statusMessage += '  State Machine: Przełączanie na tryb dynamiczny';
            break;
        case 'DYNAMIC_MODE':
            statusMessage += '  State Machine: Tryb dynamiczny aktywny';
            break;
        case 'SERVICE_MODE_REQUEST_NORMAL':
            statusMessage += '  State Machine: Przełączanie na tryb normalny';
            break;
        case 'NORMAL_MODE':
            statusMessage += '  State Machine: Tryb normalny aktywny';
            break;
        case 'NORMAL_MODE_REQUEST_SERVICE':
            statusMessage += '  State Machine: Żądanie trybu serwisowego';
            break;
        case 'UNKNOWN_STATE':
            statusMessage += '  State Machine: Stan nieznany';
            break;
        default:
            statusMessage += `  State Machine: ${currentState}`;
    }

    // Dodaj informacje o ostatnich obserwacjach sieciowych
    if (networkObs.last_request_value !== null) {
        statusMessage += ` | Request: ${networkObs.last_request_value}`;
    }

    if (networkObs.last_command_id_hex) {
        statusMessage += ` | CMD: ${networkObs.last_command_id_hex}`;
    }

    return statusMessage;
}

// Funkcja do wczytywania statusu trybu serwisowego
async function loadServiceModeStatus(isManualRefresh = false) {
    try {
        await refreshServiceModeStatus();

        if (isManualRefresh) {
            logger.addEntry('✅ Status trybu serwisowego i State Machine odświeżony', 'success');
        }
    } catch (error) {
        console.error('Błąd podczas wczytywania statusu trybu serwisowego:', error);
        updateServiceModeStatusDisplay("Błąd komunikacji", false);

        if (isManualRefresh) {
            logger.addEntry('❌ Błąd podczas odświeżania statusu trybu serwisowego', 'error');
        }
    }
}

// Funkcja do aktualizacji wyświetlania statusu - rozszerzona
function updateServiceModeStatusDisplay(statusMessage, isActive = false) {
    const statusElement = document.getElementById('serviceModeStatus');
    if (!statusElement) return;

    const statusText = statusElement.querySelector('.status-text');

    if (statusText) {
        statusText.textContent = statusMessage;
        statusElement.className = 'service-mode-status';

        // Klasyfikacja na podstawie State Machine
        if (statusMessage.includes('SERVICE_MODE') && statusMessage.includes('aktywny')) {
            statusElement.classList.add('status-active');
        } else if (statusMessage.includes('DYNAMIC_MODE') || statusMessage.includes('dynamiczny')) {
            statusElement.classList.add('status-warning');
        } else if (statusMessage.includes('NORMAL_MODE') || statusMessage.includes('normalny')) {
            statusElement.classList.add('status-inactive');
        } else if (statusMessage.includes('UNKNOWN_STATE') || statusMessage.includes('nieznany')) {
            statusElement.classList.add('status-error');
        } else if (statusMessage.includes('Przełączanie') || statusMessage.includes('Żądanie')) {
            statusElement.classList.add('status-warning');
        } else if (isActive || statusMessage.includes('aktywny')) {
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

        // UPROSZCZONA LOGIKA - bezpośrednie wywołanie /toggle
        serviceModeToggle.addEventListener('change', async function () {
            const enabled = this.checked;

            try {
                // Użyj uproszczonej funkcji toggleServiceMode
                await toggleServiceMode(enabled);

            } catch (error) {
                // toggleServiceMode już obsługuje przywrócenie stanu przełącznika
                updateServiceModeStatusDisplay("Błąd komunikacji", false);
            }
        });
    }

    if (refreshServiceModeBtn) {
        refreshServiceModeBtn.addEventListener('click', async function () {
            logger.addEntry('🔄 Ręczne odświeżanie statusu trybu serwisowego i State Machine...', 'info');
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