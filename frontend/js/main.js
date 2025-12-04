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
import { devicesService } from './services/devicesService.js';
import { loadRateChart, loadIncrementalChart, destroyAllCharts } from './components/charts.js';


// =====  FUNKCJE UWIERZYTELNIANIA =====
// Funkcja pomocnicza do obsługi błędów uwierzytelniania
function handleAuthError(error, context = '') {
    console.error(`Błąd uwierzytelniania ${context}:`, error);

    // Sprawdź czy to błąd 401 lub 403
    if (error.status === 401 || error.status === 403) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return true;
    }
    return false;
}

// Używaj funkcji globalnej zamiast lokalnej definicji
async function fetchWithAuth(url, options = {}) {
    // Sprawdź czy funkcja globalna jest dostępna
    if (typeof window.fetchWithAuth === 'function') {
        return window.fetchWithAuth(url, options);
    }

    // Fallback jeśli funkcja globalna nie jest dostępna
    console.warn('window.fetchWithAuth nie jest dostępna, używam fallback');
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return Promise.reject('No token');
    }

    const authOptions = {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': 'Bearer ' + token
        }
    };

    return fetch(url, authOptions).then(response => {
        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
        return response;
    });
}


// Globalna zmienna dla kontroli okresu
let periodControl;

let devicesAutoRefresh = null;


// Główna inicjalizacja aplikacji
document.addEventListener('DOMContentLoaded', function () {


    // Inicjalizacja wszystkich komponentów
    initializeComponents();
    initializeEventListeners();
    initializeDeviceSelection();
    initializeDevicesAutoRefresh();


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
        refreshPomiaryBtn.addEventListener('click', async () => {

            await loadMeasureData(periodControl); // ← NOWA FUNKCJA
            await loadRateChart(periodControl); // ✅ DODAJ wykres wydajności
            // await loadIncrementalChart(periodControl); // Opcjonalnie suma przyrostowa

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
            //console.log('🔄 Generowanie raportu CSV...');
            await reportService.generateReport(periodControl);
        } catch (error) {
            console.error('Błąd generowania raportu:', error);
        }
    });
}
      // ✅ NOWE - Nasłuchuj zmiany zakładek i czyść wykresy
    document.addEventListener('tabChanged', (event) => {
        if (event.detail.tab !== 'pomiary') {
            // Zniszcz wykresy gdy użytkownik opuszcza zakładkę Pomiary
            destroyAllCharts();
        }
    });


    // Event listener dla zamknięcia strony
    window.addEventListener('beforeunload', function () {
        if (isDynamicReadingsActive()) {
            fetch(`${API_URL}/dynamic-readings/deactivate`, {
                method: 'POST',
                keepalive: true
            });
        }

        // DODAJ - Zatrzymaj auto-refresh przy zamykaniu strony
        stopDevicesAutoRefresh();

    });
}
// NOWE - Inicjalizacja obsługi wyboru urządzeń
function initializeDeviceSelection() {
    // Event listenery dla wyboru urządzenia
    document.addEventListener('deviceSelected', (event) => {
        const { deviceId, data } = event.detail;
        //console.log('📱 Wybrano urządzenie:', deviceId, data);

        // Aktualizuj UI - pokaż informacje o urządzeniu
        updateDeviceInfoUI(deviceId, data);
    });

    document.addEventListener('deviceDeselected', () => {
       // console.log('📱 Usunięto wybór urządzenia');
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
                await loadMeasureData(periodControl)
                await loadRateChart(periodControl); // ✅ DODAJ wykres
                break;
            case 'aliasy':
                loadAliasyData();
                break;
            default:
                loadDeviceData();
                break;
        }
    } catch (error) {// ZMIENIONE - Dodaj obsługę błędów uwierzytelniania
        if (!handleAuthError(error, 'wyboru urządzenia')) {
            logger.addEntry(`Błąd wyboru urządzenia: ${error.message}`, 'error');
        }
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

//------------111
// DODAJ NOWĄ FUNKCJĘ - Inicjalizacja auto-refresh dla zakładki urządzeń
function initializeDevicesAutoRefresh() {
    //console.log('🔄 Inicjalizacja auto-refresh listy urządzeń...');

    // Startuj auto-refresh
    startDevicesAutoRefresh();

    // Nasłuchuj zmiany zakładek - odśwież natychmiast po przejściu do zakładki urządzeń
    document.addEventListener('tabChanged', (event) => {
        if (event.detail && event.detail.tab === 'urzadzenia') {
            //console.log('📱 Przełączono na zakładkę Urządzenia - odświeżanie listy...');
            refreshDevicesList();
        }
    });
}

// DODAJ NOWĄ FUNKCJĘ - Start auto-refresh
function startDevicesAutoRefresh() {
    // Jeśli już działa, zatrzymaj poprzedni
    if (devicesAutoRefresh) {
        clearInterval(devicesAutoRefresh);
    }

    // Ustaw interwał na 10 sekund
    devicesAutoRefresh = setInterval(async () => {
        const urzadzeniaTab = document.querySelector('.tab-btn[data-tab="urzadzenia"]');

        // Odświeżaj tylko jeśli zakładka jest aktywna
        if (urzadzeniaTab && urzadzeniaTab.classList.contains('active')) {
            await refreshDevicesList();
        }
    }, 10000); // 10 sekund

    //console.log('✅ Auto-refresh urządzeń uruchomiony (co 10s)');
}

// DODAJ NOWĄ FUNKCJĘ - Stop auto-refresh
function stopDevicesAutoRefresh() {
    if (devicesAutoRefresh) {
        clearInterval(devicesAutoRefresh);
        devicesAutoRefresh = null;
       // console.log('⏹️ Auto-refresh urządzeń zatrzymany');
    }
}

// DODAJ NOWĄ FUNKCJĘ - Odświeżanie listy urządzeń
async function refreshDevicesList() {
    try {
        const devices = await devicesService.loadDevicesList();
        const listContainer = document.getElementById('urzadzeniaList');
        const countElement = document.getElementById('devicesCount');

        if (listContainer && devices) {
            devicesService.displayDevicesList(devices, listContainer, countElement);
           // console.log(`🔄 Lista urządzeń odświeżona: ${devices.length} urządzeń`);
        }
    } catch (error) {

        if (!handleAuthError(error, 'odświeżania listy urządzeń')) {
            //console.error(' Błąd auto-refresh urządzeń:', error);
        }
    }
}
//-------------222

// **EXPORT periodControl dla innych modułów**
export { periodControl, fetchWithAuth, handleAuthError };
