import { API_URL } from '../config/constants.js';
import { logger } from '../services/logger.js';

// Stan odczytów dynamicznych
let dynamicReadingsActive = false;

// Funkcja dodająca wpis do logu odczytów
function addOdczytyLogEntry(data, type = 'new') {
    const odczytyLogEntries = document.getElementById('odczytyLogEntries');
    if (!odczytyLogEntries) return;

    const entry = document.createElement('div');
    entry.className = `odczyty-log-entry reading-${type}`;

    const now = new Date();
    const timeString = now.toLocaleTimeString('pl-PL');
    const dateString = now.toLocaleDateString('pl-PL');

    if (data && data.has_data) {
        entry.innerHTML = `
        <div class="odczyty-log-header">
            <span class="odczyty-log-device">Urządzenie: ${data.device_id}</span>
            <span class="odczyty-log-time">${dateString} ${timeString}</span>
        </div>
        <div class="odczyty-log-data">
            <div class="odczyty-log-field">
                <span class="odczyty-log-field-name">MV Reading:</span>
                <span class="odczyty-log-field-value">${data.mv_reading || '---'}</span>
            </div>
            <div class="odczyty-log-field">
                <span class="odczyty-log-field-name">Conv Digits:</span>
                <span class="odczyty-log-field-value">${data.conv_digits || '---'}</span>
            </div>
            <div class="odczyty-log-field">
                <span class="odczyty-log-field-name">Scale Weight:</span>
                <span class="odczyty-log-field-value">${data.scale_weight || '---'}</span>
            </div>
            <div class="odczyty-log-field">
                <span class="odczyty-log-field-name">Belt Weight:</span>
                <span class="odczyty-log-field-value">${data.belt_weight || '---'}</span>
            </div>
            <div class="odczyty-log-field">
                <span class="odczyty-log-field-name">Czas pomiaru:</span>
                <span class="odczyty-log-field-value">${data.current_time || '---'}</span>
            </div>
        </div>
    `;
    } else {
        entry.className = `odczyty-log-entry reading-${type}`;
        entry.innerHTML = `
        <div class="odczyty-log-header">
            <span class="odczyty-log-device">System</span>
            <span class="odczyty-log-time">${dateString} ${timeString}</span>
        </div>
        <div class="odczyty-log-data">
            <span class="odczyty-log-field-value">${data || 'Brak nowych danych'}</span>
        </div>
    `;
    }

    odczytyLogEntries.appendChild(entry);
    odczytyLogEntries.scrollTop = odczytyLogEntries.scrollHeight;

    // Ograniczenie liczby wpisów do 100
    const entries = odczytyLogEntries.children;
    if (entries.length > 100) {
        odczytyLogEntries.removeChild(entries[0]);
    }
}

// Funkcja aktualizująca status odczytów
function updateOdczytyStatus(status, message) {
    const odczytyStatus = document.getElementById('odczytyStatus');
    if (!odczytyStatus) return;

    odczytyStatus.className = `status-indicator ${status}`;
    odczytyStatus.textContent = message;
}

// Funkcja ładująca odczyty dynamiczne
export async function loadDynamicReadings() {
    try {
        const response = await fetch(`${API_URL}/dynamic-readings/readings`);
        if (response.ok) {
            const data = await response.json();

            if (data.has_data) {
                addOdczytyLogEntry(data, 'new');
                updateOdczytyStatus('active', 'Odczyty aktywne - dane otrzymane');
            } else {
                addOdczytyLogEntry('Brak nowych danych odczytów', 'update');
                updateOdczytyStatus('waiting', 'Tryb odczytów aktywny - oczekiwanie na dane');
            }
        } else {
            addOdczytyLogEntry('Błąd komunikacji z serwerem', 'error');
            updateOdczytyStatus('inactive', 'Błąd komunikacji');
        }
    } catch (error) {
        console.error('Błąd podczas ładowania odczytów:', error);
        addOdczytyLogEntry(`Błąd: ${error.message}`, 'error');
        updateOdczytyStatus('inactive', 'Błąd połączenia');
        logger.addEntry('Błąd podczas ładowania odczytów dynamicznych', 'error');
    }
}

// Aktywacja trybu odczytów
export async function activateReadingsMode() {
    try {
        const response = await fetch(`${API_URL}/dynamic-readings/activate`, {
            method: 'POST'
        });
        if (response.ok) {
            const data = await response.json();
            dynamicReadingsActive = true;
            updateOdczytyStatus('waiting', 'Tryb odczytów aktywowany');
            addOdczytyLogEntry('Tryb odczytów dynamicznych aktywowany', 'update');
            logger.addEntry('Tryb odczytów dynamicznych aktywowany', 'success');
        }
    } catch (error) {
        addOdczytyLogEntry(`Błąd aktywacji: ${error.message}`, 'error');
        logger.addEntry('Błąd aktywacji trybu odczytów', 'error');
    }
}

// Deaktywacja trybu odczytów
export async function deactivateReadingsMode() {
    try {
        const response = await fetch(`${API_URL}/dynamic-readings/deactivate`, {
            method: 'POST'
        });
        if (response.ok) {
            dynamicReadingsActive = false;
            updateOdczytyStatus('inactive', 'Tryb odczytów deaktywowany');
            addOdczytyLogEntry('Tryb odczytów dynamicznych deaktywowany', 'update');
            logger.addEntry('Tryb odczytów dynamicznych deaktywowany', 'info');
        }
    } catch (error) {
        addOdczytyLogEntry(`Błąd deaktywacji: ${error.message}`, 'error');
        logger.addEntry('Błąd deaktywacji trybu odczytów', 'error');
    }
}

// Inicjalizacja event listenerów dla odczytów
export function initReadingsEventListeners() {
    const refreshOdczytyBtn = document.getElementById('refreshOdczyty');
    const clearOdczytyLogBtn = document.getElementById('clearOdczytyLog');

    if (refreshOdczytyBtn) {
        refreshOdczytyBtn.addEventListener('click', () => {
            addOdczytyLogEntry('Ręczne odświeżanie odczytów...', 'update');
            loadDynamicReadings();
        });
    }

    if (clearOdczytyLogBtn) {
        clearOdczytyLogBtn.addEventListener('click', () => {
            const odczytyLogEntries = document.getElementById('odczytyLogEntries');
            if (odczytyLogEntries) {
                odczytyLogEntries.innerHTML = '';
                addOdczytyLogEntry('Log odczytów wyczyszczony', 'update');
            }
        });
    }
}

// Eksport stanu dla innych modułów
export function isDynamicReadingsActive() {
    return dynamicReadingsActive;
}