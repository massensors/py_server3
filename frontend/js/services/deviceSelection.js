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

        try {
            const response = await fetch(`${API_URL}/device-selection/select`, {
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

            logger.addEntry(
                `✅ Wybrano urządzenie: ${deviceId} ${data.device_exists ? '(istnieje w bazie)' : '(nowe urządzenie)'}`,
                'success'
            );

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
            const response = await fetch(`${API_URL}/device-selection/current`);

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
            const response = await fetch(`${API_URL}/device-selection/clear`, {
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
}

// Eksportuj instancję
export const deviceSelection = new DeviceSelection();