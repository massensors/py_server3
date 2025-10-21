import { logger } from './logger.js';

class DevicesService {
    constructor() {
        this.API_URL = '/api';
        this.BASE_URL = ''; // Dodaj BASE_URL bez /api dla niektórych endpointów
    }

    async loadDevicesList() {
        try {
            logger.addEntry('Ładowanie listy urządzeń...', 'request');

            const response = await fetch(`${this.API_URL}/devices/status`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

             const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Błąd pobierania urządzeń');
            }
            logger.addEntry(`Załadowano listę ${result.devices.length} urządzeń`, 'success');

            return result.devices;
        } catch (error) {
            logger.addEntry(`Błąd ładowania urządzeń: ${error.message}`, 'error');
            throw error;
        }
    }

    async loadDevicesCount() {
        try {
            const response = await fetch(`${this.API_URL}/devices/count`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            return result.count;
        } catch (error) {
            logger.addEntry(`Błąd ładowania liczby urządzeń: ${error.message}`, 'error');
            throw error;
        }
    }

    async searchDevices(searchParams) {
        try {
            const queryParams = new URLSearchParams();

            if (searchParams.company) queryParams.append('company', searchParams.company);
            if (searchParams.location) queryParams.append('location', searchParams.location);
            if (searchParams.product_name) queryParams.append('product_name', searchParams.product_name);
            if (searchParams.scale_id) queryParams.append('scale_id', searchParams.scale_id);

            const response = await fetch(`${this.API_URL}/devices/search/by-alias?${queryParams}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const devices = await response.json();
            logger.addEntry(`Znaleziono ${devices.length} urządzeń`, 'success');

            return devices;
        } catch (error) {
            logger.addEntry(`Błąd wyszukiwania urządzeń: ${error.message}`, 'error');
            throw error;
        }
    }

    // POPRAWIONA FUNKCJA - używa BASE_URL zamiast API_URL
    async selectAndLoadDevice(deviceId) {
        try {
            logger.addEntry(`Automatyczne wczytywanie danych dla urządzenia: ${deviceId}`, 'info');

            // 1. Wywołaj endpoint /device-selection/select (BEZ /api prefix!)
            const selectionResponse = await fetch(`${this.BASE_URL}/device-selection/select`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: deviceId
                })
            });

            if (!selectionResponse.ok) {
                throw new Error(`Błąd wyboru urządzenia: ${selectionResponse.status}`);
            }

            const selectionData = await selectionResponse.json();
            logger.addEntry(`Wybrano urządzenie: ${selectionData.message}`, 'success');

            // 2. Wywołaj endpoint /app/devices/{deviceId}/parameters (BEZ /api prefix!)
            const parametersResponse = await fetch(`${this.BASE_URL}/app/devices/${deviceId}/parameters`);

            if (!parametersResponse.ok) {
                throw new Error(`Błąd pobierania parametrów: ${parametersResponse.status}`);
            }

            const parametersData = await parametersResponse.json();

            if (parametersData.status === 'error') {
                logger.addEntry(`Błąd parametrów: ${parametersData.message}`, 'error');
                return { success: false, error: parametersData.message };
            }

            logger.addEntry(`Pobrano parametry dla urządzenia ${deviceId}`, 'success');

            // 3. Wypełnij pola parametrów
            this.fillParametersData(parametersData.parameters);

            // 4. Przełącz na zakładkę "Parametry"
            //this.switchToParametersTab();
            this.switchToPomiaryTab();
            return {
                success: true,
                selectionData,
                parametersData
            };

        } catch (error) {
            logger.addEntry(`Błąd automatycznego wczytania: ${error.message}`, 'error');
            return { success: false, error: error.message };
        }
    }

    // FUNKCJA DO WYPEŁNIANIA PARAMETRÓW
    fillParametersData(parameters) {
        for (const [address, param] of Object.entries(parameters)) {
            const paramItem = document.querySelector(`.parameter-item[data-address="${address}"]`);
            if (paramItem) {
                const valueInput = paramItem.querySelector('.param-value');
                if (valueInput) {
                    valueInput.value = param.value;
                }
            }
        }
    }

    // FUNKCJA DO PRZEŁĄCZANIA NA ZAKŁADKĘ PARAMETRY
    switchToParametersTab() {
        const parametersTab = document.querySelector('[data-tab="parameters"]');
        const parametersContent = document.getElementById('parameters');

        if (parametersTab && parametersContent) {
            // Usuń aktywne klasy z wszystkich zakładek
            document.querySelectorAll('.tab-btn').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Aktywuj zakładkę "Parametry"
            parametersTab.classList.add('active');
            parametersContent.classList.add('active');
        }
    }
    // NOWA FUNKCJA DO PRZEŁĄCZANIA NA ZAKŁADKĘ POMIARY
    switchToPomiaryTab() {
        console.log('🔄 devicesService.switchToPomiaryTab() - przełączam na Pomiary');

        const pomiaryTab = document.querySelector('[data-tab="pomiary"]');
        const pomiaryContent = document.getElementById('pomiary');

        if (pomiaryTab && pomiaryContent) {
            // Usuń aktywne klasy z wszystkich zakładek
            document.querySelectorAll('.tab-btn').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Aktywuj zakładkę "Pomiary"
            pomiaryTab.classList.add('active');
            pomiaryContent.classList.add('active');

            console.log('✅ Przełączono na zakładkę Pomiary');

            // Opcjonalnie: wczytaj dane pomiarowe
            // Możesz tutaj dodać logikę wczytywania danych jeśli potrzebujesz

        } else {
            console.error('❌ Nie znaleziono elementów zakładki Pomiary');
        }
    }

    displayDevicesList(devices, containerElement, devicesCountElement) {
        if (!containerElement) return;

        // Aktualizacja licznika urządzeń
        if (devicesCountElement) {
            devicesCountElement.textContent = devices.length || 0;
        }

        if (!devices || devices.length === 0) {
            containerElement.innerHTML = `
                <div class="no-devices-message">
                    Brak urządzeń w bazie danych
                </div>
            `;
            return;
        }

        containerElement.innerHTML = '';

        devices.forEach(device => {
            const deviceRow = this.createDeviceRow(device);
            containerElement.appendChild(deviceRow);
        });
    }

    createDeviceRow(device) {
        const deviceRow = document.createElement('div');
        deviceRow.className = 'device-row';
        deviceRow.setAttribute('data-device-id', device.deviceId);

        // Dodaj klasę online/offline
        if (device.online) {
            deviceRow.classList.add('device-online');
        } else {
            deviceRow.classList.add('device-offline');
        }

        // Dodaj style dla hover i cursor
        deviceRow.style.cursor = 'pointer';


        // Status online/offline
        const onlineClass = device.online ? 'online' : 'offline';
        const onlineText = device.online ? '🟢 ONLINE' : '🔴 OFFLINE';

        // Formatowanie czasu ostatniej aktywności
        let lastSeenText = '';
        if (device.last_seen) {
            const secondsAgo = device.seconds_since_last_seen;
            if (secondsAgo < 60) {
                lastSeenText = `${secondsAgo}s temu`;
            } else {
                const minutesAgo = Math.floor(secondsAgo / 60);
                lastSeenText = `${minutesAgo}m temu`;
            }
        } else {
            lastSeenText = 'nigdy';
        }
        // Tworzenie listy aliasów
        let aliasesHtml = this.formatAliases({
            company: device.company,
            location: device.location,
            productName: device.productName,
            scaleId: device.scaleId
        });

        deviceRow.innerHTML = `
            <div class="device-info">
                <div class="device-header-row">
                    <div class="device-id">${device.deviceId}</div>
                    <span class="device-status-badge ${onlineClass}">${onlineText}</span>
                </div>
                <div class="device-aliases">${aliasesHtml}</div>
                <div class="device-last-seen">Ostatnia aktywność: ${lastSeenText}</div>
            </div>
            <button class="device-select-btn">Wybierz</button>
        `;

        // Event listenery
        this.attachRowEventListeners(deviceRow, device.deviceId);

        return deviceRow;

    }

    formatAliases(aliases) {
        if (!aliases || Object.keys(aliases).length === 0) {
            return '<span class="device-alias-empty">Brak aliasów</span>';
        }

        const aliasItems = [];

        if (aliases.company) aliasItems.push(`Firma: ${aliases.company}`);
        if (aliases.location) aliasItems.push(`Lokalizacja: ${aliases.location}`);
        if (aliases.productName) aliasItems.push(`Produkt: ${aliases.productName}`);
        if (aliases.scaleId) aliasItems.push(`ID wagi: ${aliases.scaleId}`);

        return aliasItems.map(alias =>
            `<span class="device-alias-item">${alias}</span>`
        ).join('');
    }

    attachRowEventListeners(deviceRow, deviceId) {
        const selectBtn = deviceRow.querySelector('.device-select-btn');

        // Event listener dla przycisku "Wybierz"
        selectBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.handleDeviceSelection(deviceId);
        });

        // Event listener dla kliknięcia na cały wiersz
        deviceRow.addEventListener('click', () => {
            this.handleDeviceSelection(deviceId);
        });
    }

    // FUNKCJA OBSŁUGI WYBORU URZĄDZENIA
    async handleDeviceSelection(deviceId) {
        // Ustaw wartość w polu deviceId
        const deviceIdInput = document.getElementById('deviceId');
        if (deviceIdInput) {
            deviceIdInput.value = deviceId;
        }

        // Usuń poprzednie zaznaczenie
        document.querySelectorAll('.device-row.selected').forEach(row => {
            row.classList.remove('selected');
        });

        // Zaznacz nowy wiersz
        const selectedRow = document.querySelector(`[data-device-id="${deviceId}"]`);
        if (selectedRow) {
            selectedRow.classList.add('selected');
        }

        // GŁÓWNA FUNKCJONALNOŚĆ - automatyczne wczytanie danych
        await this.selectAndLoadDevice(deviceId);
    }

    // STARA FUNKCJA - zachowana dla kompatybilności
    selectDevice(deviceId) {
        const deviceIdInput = document.getElementById('deviceId');
        if (!deviceIdInput) return;

        // Usuń poprzednie zaznaczenie
        document.querySelectorAll('.device-row.selected').forEach(row => {
            row.classList.remove('selected');
        });

        // Zaznacz nowy wiersz
        const selectedRow = document.querySelector(`[data-device-id="${deviceId}"]`);
        if (selectedRow) {
            selectedRow.classList.add('selected');
        }

        // Skopiuj ID do pola input
        deviceIdInput.value = deviceId;

        logger.addEntry(`Wybrano urządzenie: ${deviceId}`, 'info');
    }

    showLoadingState(containerElement) {
        if (containerElement) {
            containerElement.innerHTML = '<div class="loading-message">Ładowanie listy urządzeń...</div>';
        }
    }

    showErrorState(containerElement, error) {
        if (containerElement) {
            containerElement.innerHTML = `
                <div class="error-message">
                    <strong>Błąd ładowania listy urządzeń</strong><br>
                    ${error.message}
                </div>
            `;
        }
    }
}

export const devicesService = new DevicesService();