import { loadDeviceData, loadAliasyData, loadPomiaryData } from './services/api.js';
import { logger } from './services/logger.js';
import { createParametersGrid, createAliasyGrid } from './components/grids.js';
import { initTabHandlers } from './components/tabs.js';
import { initReadingsEventListeners, isDynamicReadingsActive, deactivateReadingsMode } from './components/readings.js';
import { initServiceMode } from './services/serviceMode.js';
import { getDeviceId } from './utils/helpers.js';
import { API_URL } from './config/constants.js';

// Główna inicjalizacja aplikacji
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Inicjalizacja aplikacji...');

    // Inicjalizacja wszystkich komponentów
    initializeComponents();
    initializeEventListeners();

    console.log('✅ Aplikacja zainicjalizowana pomyślnie');
});

// Inicjalizuje wszystkie komponenty
function initializeComponents() {
    // Siatki parametrów i aliasów
    createParametersGrid();
    createAliasyGrid();

    // Zakładki
    initTabHandlers();

    // Odczyty dynamiczne
    initReadingsEventListeners();

    // Tryb serwisowy
    initServiceMode();
}

// Inicjalizuje główne event listenery
function initializeEventListeners() {
    // Przycisk wczytywania danych urządzenia
    const loadDeviceBtn = document.getElementById('loadDevice');
    if (loadDeviceBtn) {
        loadDeviceBtn.addEventListener('click', handleLoadDevice);
    }

    // Przycisk odświeżania pomiarów
    const refreshPomiaryBtn = document.getElementById('refreshPomiary');
    if (refreshPomiaryBtn) {
        refreshPomiaryBtn.addEventListener('click', () => {
            console.log('Odświeżanie danych pomiarowych...');
            loadPomiaryData();
        });
    }

    // Przycisk czyszczenia logów
    const clearLogBtn = document.getElementById('clearLog');
    if (clearLogBtn) {
        clearLogBtn.addEventListener('click', () => {
            logger.clear();
        });
    }

    // Event listener dla zamknięcia strony
    window.addEventListener('beforeunload', function () {
        if (isDynamicReadingsActive()) {
            fetch(`${API_URL}/dynamic-readings/deactivate`, {
                method: 'POST',
                keepalive: true
            });
        }
    });
}

// Obsługuje wczytywanie danych urządzenia
function handleLoadDevice() {
    const deviceId = getDeviceId();
    if (!deviceId) {
        logger.addEntry('Błąd: Wprowadź ID urządzenia', 'error');
        return;
    }

    // Określ aktywną zakładkę
    const activeTabBtn = document.querySelector('.tab-btn.active');
    const activeTab = activeTabBtn ? activeTabBtn.getAttribute('data-tab') : 'parameters';

    // Wczytaj odpowiednie dane
    switch (activeTab) {
        case 'parameters':
            loadDeviceData();
            break;
        case 'pomiary':
            loadPomiaryData();
            break;
        case 'aliasy':
            loadAliasyData();
            break;
        default:
            loadDeviceData();
            break;
    }
}