import { getDeviceId } from '../utils/helpers.js';
import { loadPomiaryData } from '../services/api.js';
import { activateReadingsMode, deactivateReadingsMode, isDynamicReadingsActive } from './readings.js';
import { devicesService } from '../services/devicesService.js';
import { logger } from '../services/logger.js';

// Inicjalizuje obsługę zakładek
export function initTabHandlers() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Usuwamy klasę active z wszystkich przycisków i zawartości
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Dodajemy klasę active do klikniętego przycisku i odpowiedniej zawartości
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');

            // Obsługa specyficzna dla każdej zakładki
            handleTabSwitch(tabId);
        });
    });
}

// Obsługuje przełączenie na konkretną zakładkę
function handleTabSwitch(tabId) {
    if (tabId === 'aliasy' || tabId === 'parameters') {
        deactivateReadingsMode();
        logger.addEntry('Tryb odczytów wyłączony', 'info');
    }

    if (tabId === 'pomiary') {
        const deviceId = getDeviceId();
        if (deviceId) {
            loadPomiaryData();
        }
    }
    if (tabId === 'urzadzenia') {
        deactivateReadingsMode();
        loadDevicesTab();
        logger.addEntry('Przełączono na zakładkę urządzeń', 'info');
    }


    if (tabId === 'odczyty') {
        activateReadingsMode();
        // addOdczytyLogEntry jest wewnętrzna w readings.js
    } else {
        if (isDynamicReadingsActive()) {
            deactivateReadingsMode();
        }
    }
}

// Funkcja ładująca zawartość zakładki urządzeń
async function loadDevicesTab() {
    const urzadzeniaList = document.getElementById('urzadzeniaList');
    const devicesCount = document.getElementById('devicesCount');
    const refreshBtn = document.getElementById('refreshUrzadzenia');

    // Pokaż stan ładowania
    devicesService.showLoadingState(urzadzeniaList);

    try {
        const devices = await devicesService.loadDevicesList();
        devicesService.displayDevicesList(devices, urzadzeniaList, devicesCount);
    } catch (error) {
        devicesService.showErrorState(urzadzeniaList, error);
    }

    // Dodaj event listener dla przycisku odświeżania jeśli jeszcze nie ma
    if (refreshBtn && !refreshBtn.hasAttribute('data-listener-added')) {
        refreshBtn.addEventListener('click', () => {
            loadDevicesTab();
        });
        refreshBtn.setAttribute('data-listener-added', 'true');
    }
}
