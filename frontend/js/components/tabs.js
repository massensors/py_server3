import { getDeviceId } from '../utils/helpers.js';
import { loadPomiaryData } from '../services/api.js';
import { activateReadingsMode, deactivateReadingsMode, isDynamicReadingsActive } from './readings.js';
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

    if (tabId === 'odczyty') {
        activateReadingsMode();
        // addOdczytyLogEntry jest wewnętrzna w readings.js
    } else {
        if (isDynamicReadingsActive()) {
            deactivateReadingsMode();
        }
    }
}