import { PeriodControl } from './components/period-control.js';

import { loadDeviceData, loadAliasyData, loadPomiaryData } from './services/api.js';
import { logger } from './services/logger.js';
import { createParametersGrid, createAliasyGrid } from './components/grids.js';
import { initTabHandlers } from './components/tabs.js';
import { initReadingsEventListeners, isDynamicReadingsActive, deactivateReadingsMode } from './components/readings.js';
import { initServiceMode } from './services/serviceMode.js';
import { getDeviceId } from './utils/helpers.js';
import { API_URL } from './config/constants.js';
import { deviceSelection } from './services/deviceSelection.js';
import { loadMeasureData } from './services/api.js'; // dodaj import
import { reportService } from './services/reportService.js';


// Globalna zmienna dla kontroli okresu
let periodControl;


// Główna inicjalizacja aplikacji
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Inicjalizacja aplikacji...');

    // Inicjalizacja wszystkich komponentów
    initializeComponents();
    initializeEventListeners();
    initializeDeviceSelection();


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

    // Kontrola okresu dla zakładki pomiary
    periodControl = new PeriodControl();
    console.log('📅 Kontrola okresu zainicjalizowana');

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
             loadMeasureData(periodControl); // ← NOWA FUNKCJA

            //loadPomiaryData();
        });
    }

    // Przycisk czyszczenia logów
    const clearLogBtn = document.getElementById('clearLog');
    if (clearLogBtn) {
        clearLogBtn.addEventListener('click', () => {
            logger.clear();
        });
    }
    // Przycisk generowania raportu
    const generateReportBtn = document.getElementById('generateReport');
      if (generateReportBtn) {
      generateReportBtn.addEventListener('click', async () => {
        try {
            console.log('🔄 Generowanie raportu CSV...');
            await reportService.generateReport(periodControl);
        } catch (error) {
            console.error('Błąd generowania raportu:', error);
        }
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
// NOWE - Inicjalizacja obsługi wyboru urządzeń
function initializeDeviceSelection() {
    // Event listenery dla wyboru urządzenia
    document.addEventListener('deviceSelected', (event) => {
        const { deviceId, data } = event.detail;
        console.log('📱 Wybrano urządzenie:', deviceId, data);

        // Aktualizuj UI - pokaż informacje o urządzeniu
        updateDeviceInfoUI(deviceId, data);
    });

    document.addEventListener('deviceDeselected', () => {
        console.log('📱 Usunięto wybór urządzenia');
        clearDeviceInfoUI();
    });

    // Pobierz aktualny wybór przy starcie
    deviceSelection.getCurrentSelection().catch(console.error);
}




// Obsługuje wczytywanie danych urządzenia - ZMODYFIKOWANE
async function handleLoadDevice() {
    const deviceId = getDeviceId();
    if (!deviceId) {
        logger.addEntry('Błąd: Wprowadź ID urządzenia', 'error');
        return;
    }

    try {
        // NOWE - Najpierw wybierz urządzenie w backendzie
        await deviceSelection.selectDevice(deviceId);

        // Określ aktywną zakładkę
        const activeTabBtn = document.querySelector('.tab-btn.active');
        const activeTab = activeTabBtn ? activeTabBtn.getAttribute('data-tab') : 'parameters';

        // Wczytaj odpowiednie dane
        switch (activeTab) {
            case 'parameters':
                loadDeviceData();
                break;
            case 'pomiary':
                //loadPomiaryData();
                loadMeasureData(periodControl)

                break;
            case 'aliasy':
                loadAliasyData();
                break;
            default:
                loadDeviceData();
                break;
        }
    } catch (error) {
        logger.addEntry(`Błąd wyboru urządzenia: ${error.message}`, 'error');
    }
}

// NOWE - Aktualizuj UI z informacjami o urządzeniu
function updateDeviceInfoUI(deviceId, data) {
    // Dodaj wskaźnik wybranego urządzenia
    const deviceInput = document.getElementById('deviceId');
    if (deviceInput) {
        deviceInput.style.borderColor = data.device_exists ? '#28a745' : '#ffc107';
        deviceInput.title = data.device_exists ? 'Urządzenie istnieje w bazie' : 'Nowe urządzenie';
    }

    // Jeśli masz miejsce na informacje o urządzeniu, wyświetl je
    if (data.device_info && data.device_info.alias) {
        const alias = data.device_info.alias;
        logger.addEntry(`📋 Info: ${alias.company} | ${alias.location} | ${alias.productName}`, 'info');
    }
}

// NOWE - Wyczyść UI informacji o urządzeniu
function clearDeviceInfoUI() {
    const deviceInput = document.getElementById('deviceId');
    if (deviceInput) {
        deviceInput.style.borderColor = '';
        deviceInput.title = '';
    }
}

// **EXPORT periodControl dla innych modułów**
export { periodControl };
