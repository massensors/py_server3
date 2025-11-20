import { API_URL } from '../config/constants.js';
import { logger } from './logger.js';

class DeviceSelection {
    constructor() {
        this.selectedDeviceId = null;
        this.deviceInfo = null;
    }

    /**
     * Wybierz urządzenie i zapisz w backendzie
     */
    async selectDevice(deviceId) {
        if (!deviceId || deviceId.trim() === '') {
            throw new Error('Device ID nie może być pusty');
        }

        // Zapamiętaj poprzednie ID (jeśli istnieje)
        const previousDeviceId = this.selectedDeviceId;

        try {
            const response = await fetchWithAuth(`${API_URL}/device-selection/select`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: deviceId.trim()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            this.selectedDeviceId = data.selected_device_id;
            this.deviceInfo = data.device_info;

            // Dodatkowe logowanie dla diagnostyki
            console.log(`DeviceSelection: ustawiono selectedDeviceId=${this.selectedDeviceId}`);

            logger.addEntry(
                `✅ Wybrano urządzenie: ${deviceId} ${data.device_exists ? '(istnieje w bazie)' : '(nowe urządzenie)'}`,
                'success'
            );

            // Sprawdź czy trzeba wyłączyć tryb serwisowy poprzedniego urządzenia
            if (previousDeviceId && previousDeviceId !== deviceId) {
                await this._checkAndDisablePreviousServiceMode(previousDeviceId);
            }

            // Wywołaj event dla innych komponentów
            this._notifyDeviceSelected(deviceId, data);

            return data;

        } catch (error) {
            logger.addEntry(`❌ Błąd wyboru urządzenia: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Pobierz aktualnie wybrane urządzenie z backendu
     */
    async getCurrentSelection() {
        try {
            const response = await fetchWithAuth(`${API_URL}/device-selection/current`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            this.selectedDeviceId = data.selected_device_id;
            this.deviceInfo = data.device_info;

            return data;

        } catch (error) {
            logger.addEntry(`❌ Błąd pobierania wybranego urządzenia: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Wyczyść wybór urządzenia
     */
    async clearSelection() {
        try {
            const response = await fetchWithAuth(`${API_URL}/device-selection/clear`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            this.selectedDeviceId = null;
            this.deviceInfo = null;

            logger.addEntry('🗑️ Usunięto wybór urządzenia', 'info');

            // Wywołaj event
            this._notifyDeviceDeselected();

            return data;

        } catch (error) {
            logger.addEntry(`❌ Błąd usuwania wyboru: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Pobierz ID wybranego urządzenia (lokalnie)
     */
    getSelectedDeviceId() {
        return this.selectedDeviceId;
    }

    /**
     * Sprawdź czy urządzenie jest wybrane
     */
    hasSelection() {
        return this.selectedDeviceId !== null;
    }

    /**
     * Pobierz informacje o urządzeniu
     */
    getDeviceInfo() {
        return this.deviceInfo;
    }

    /**
     * Powiadamianie o wybraniu urządzenia
     */
    _notifyDeviceSelected(deviceId, data) {
        const event = new CustomEvent('deviceSelected', {
            detail: { deviceId, data }
        });
        document.dispatchEvent(event);
    }

    /**
     * Powiadamianie o usunięciu wyboru
     */
    _notifyDeviceDeselected() {
        const event = new CustomEvent('deviceDeselected');
        document.dispatchEvent(event);
    }

    /**
     * Sprawdza czy poprzednie urządzenie było w trybie serwisowym i wyłącza go
     * jeśli jesteśmy w zakładce parametry
     */
    async _checkAndDisablePreviousServiceMode(previousDeviceId) {
        try {
            // Sprawdź czy jesteśmy na zakładce parametry
            const parametersTab = document.querySelector('.tab-btn[data-tab="parameters"]');
            const isParametersActive = parametersTab && parametersTab.classList.contains('active');

            if (isParametersActive) {
                // Sprawdź status trybu serwisowego
                const response = await fetchWithAuth(`${API_URL}/service-mode/status`);
                if (response.ok) {
                    const data = await response.json();

                    // Jeśli tryb serwisowy jest włączony, wyłącz go dla poprzedniego urządzenia
                    if (data.enabled) {
                        logger.addEntry(`🔄 Wyłączanie trybu serwisowego dla poprzedniego urządzenia...`, 'info');

                        // Użyj nowego endpointu do wyłączenia trybu serwisowego
                        const disableResponse = await fetchWithAuth(`${API_URL}/service-mode/toggle-for-device`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({enabled: false})
                        });

                        if (disableResponse.ok) {
                            logger.addEntry(`✅ Tryb serwisowy wyłączony dla poprzedniego urządzenia`, 'success');
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Błąd podczas sprawdzania trybu serwisowego:", error);
        }
    }
    // Dodaj nowe metody do klasy DeviceSelection

    /**
     * Włącz tryb serwisowy dla wybranego urządzenia
     */
    async enableServiceMode() {
        try {
            const response = await fetchWithAuth(`${API_URL}/device-selection/service-mode/enable`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            logger.addEntry(
                `✅ Włączono tryb serwisowy dla urządzenia: ${data.device_id}`,
                'success'
            );

            return data;

        } catch (error) {
            logger.addEntry(`❌ Błąd włączania trybu serwisowego: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Wyłącz tryb serwisowy dla wybranego urządzenia
     */
    async disableServiceMode() {
        try {
            const response = await fetchWithAuth(`${API_URL}/device-selection/service-mode/disable`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            logger.addEntry(
                `⭕ Wyłączono tryb serwisowy dla urządzenia: ${data.device_id}`,
                'info'
            );

            return data;

        } catch (error) {
            logger.addEntry(`❌ Błąd wyłączania trybu serwisowego: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Pobierz status trybu serwisowego
     */
    async getServiceModeStatus() {
        try {
            const response = await fetchWithAuth(`${API_URL}/device-selection/service-mode/status`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            logger.addEntry(`❌ Błąd pobierania statusu trybu serwisowego: ${error.message}`, 'error');
            throw error;
        }
    }





}

// Eksportuj instancję
export const deviceSelection = new DeviceSelection();