import { TabManager } from './components/tabs.js';
import { Logger } from './components/logger.js';
import { parameterService } from './services/parameter.service.js';
import { readingsService } from './services/reading.service.js';
import { GridManager } from './components/grids.js';
// Główny plik aplikacji - inicjalizacja i konfiguracja
import { initializeApp } from './main.js';

document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
});


export class MeasurementApp {
    constructor() {
        this.logger = new Logger('logEntries');
        this.tabManager = new TabManager();
        this.gridManager = new GridManager();

        this.deviceIdInput = document.getElementById('deviceId');
        this.loadDeviceBtn = document.getElementById('loadDevice');

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupTabHandlers();
        this.setupReadingsService();
        this.gridManager.createParametersGrid();
        this.gridManager.createAliasyGrid();
    }

    setupEventListeners() {
        if (this.loadDeviceBtn) {
            this.loadDeviceBtn.addEventListener('click', () => this.handleLoadDevice());
        }

        // Czyszczenie logów
        const clearLogBtn = document.getElementById('clearLog');
        if (clearLogBtn) {
            clearLogBtn.addEventListener('click', () => this.logger.clear());
        }
    }

    setupTabHandlers() {
        this.tabManager.onTabChange('parameters', () => {
            readingsService.deactivate();
            this.logger.info('Przełączono na parametry');
        });

        this.tabManager.onTabChange('odczyty', () => {
            readingsService.activate();
            this.logger.info('Przełączono na odczyty');
        });

        this.tabManager.onTabChange('pomiary', (tabId) => {
            readingsService.deactivate();
            const deviceId = this.getDeviceId();
            if (deviceId) {
                this.loadPomiaryData(deviceId);
            }
        });
    }

    setupReadingsService() {
        readingsService.onStatusChange((status, message) => {
            this.updateReadingsStatus(status, message);
        });

        readingsService.onDataReceived((data) => {
            this.handleReadingsData(data);
        });
    }

    async handleLoadDevice() {
        const deviceId = this.getDeviceId();
        if (!deviceId) {
            this.logger.error('Błąd: Wprowadź ID urządzenia');
            return;
        }

        const activeTab = this.tabManager.getActiveTab();

        try {
            switch (activeTab) {
                case 'parameters':
                    await this.loadDeviceParameters(deviceId);
                    break;
                case 'aliasy':
                    await this.loadAliasyData(deviceId);
                    break;
                case 'pomiary':
                    await this.loadPomiaryData(deviceId);
                    break;
                default:
                    await this.loadDeviceParameters(deviceId);
            }
        } catch (error) {
            this.logger.error(`Błąd podczas ładowania danych: ${error.message}`);
        }
    }

    async loadDeviceParameters(deviceId) {
        this.logger.request(`Pobieranie parametrów dla urządzenia ${deviceId}...`);

        try {
            const parameters = await parameterService.loadDeviceParameters(deviceId);
            this.gridManager.updateParametersGrid(parameters);
            this.logger.success(`Pobrano parametry dla urządzenia ${deviceId}`);
        } catch (error) {
            this.logger.error(`Błąd: ${error.message}`);
            throw error;
        }
    }

    getDeviceId() {
        return this.deviceIdInput ? this.deviceIdInput.value.trim() : '';
    }

    updateReadingsStatus(status, message) {
        const statusElement = document.getElementById('odczytyStatus');
        if (statusElement) {
            statusElement.className = `status-indicator ${status}`;
            statusElement.textContent = message;
        }
    }

    handleReadingsData(data) {
        // Implementacja obsługi danych odczytów
        if (data) {
            this.logger.info('Otrzymano nowe dane odczytów');
        }
    }
}