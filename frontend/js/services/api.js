import { API_URL, PARAMETER_MAPPING, ALIAS_ADDRESS_MAPPING } from '../config/constants.js';
import { getDeviceId, formatDateTime } from '../utils/helpers.js';
import { logger } from './logger.js';

// Wczytuje dane urządzenia z serwera
export async function loadDeviceData() {
    const deviceId = getDeviceId();

    if (!deviceId) {
        logger.addEntry('Błąd: Wprowadź ID urządzenia', 'error');
        return;
    }

    try {
        logger.addEntry(`Pobieranie parametrów dla urządzenia ${deviceId}...`, 'request');

        const response = await fetch(`${API_URL}/app/devices/${deviceId}/parameters`);
        const data = await response.json();

        if (data.status === 'error') {
            logger.addEntry(`Błąd: ${data.message}`, 'error');
            return;
        }

        logger.addEntry(`Pobrano parametry dla urządzenia ${deviceId}`, 'response');

        // Wypełniamy pola wartościami z serwera
        for (const [address, param] of Object.entries(data.parameters)) {
            const paramItem = document.querySelector(`.parameter-item[data-address="${address}"]`);
            if (paramItem) {
                const valueInput = paramItem.querySelector('.param-value');
                if (valueInput) {
                    valueInput.value = param.value;
                }
            }
        }
    } catch (error) {
        logger.addEntry(`Błąd połączenia: ${error.message}`, 'error');
    }
}

// Wczytuje dane aliasów z serwera
export async function loadAliasyData() {
    const deviceId = getDeviceId();

    if (!deviceId) {
        logger.addEntry('Błąd: Wprowadź ID urządzenia', 'error');
        return;
    }

    try {
        logger.addEntry(`Pobieranie aliasów dla urządzenia ${deviceId}...`, 'request');

        const response = await fetch(`${API_URL}/aliases/${deviceId}`);

        if (!response.ok) {
            throw new Error(`Status: ${response.status}`);
        }

        const data = await response.json();
        logger.addEntry(`Pobrano aliasy dla urządzenia ${deviceId}`, 'response');

        // Wypełniamy pola wartościami z serwera
        const ALIAS_FIELDS = [
            {name: "company", label: "Firma"},
            {name: "location", label: "Lokalizacja"},
            {name: "productName", label: "Nazwa produktu"},
            {name: "scaleId", label: "ID wagi"}
        ];

        for (const field of ALIAS_FIELDS) {
            const aliasItem = document.querySelector(`.alias-item[data-field="${field.name}"]`);
            if (aliasItem && data[field.name]) {
                const valueInput = aliasItem.querySelector('.alias-value');
                if (valueInput) {
                    valueInput.value = data[field.name];
                }
            }
        }
    } catch (error) {
        logger.addEntry(`Błąd podczas pobierania aliasów: ${error.message}`, 'error');
    }
}

// Wczytuje dane pomiarowe z serwera
export async function loadPomiaryData() {
    const deviceId = getDeviceId();

    if (!deviceId) {
        logger.addEntry('Błąd: Wprowadź ID urządzenia', 'error');
        return;
    }

    try {
        logger.addEntry(`Pobieranie danych pomiarowych dla urządzenia ${deviceId}...`, 'request');

        const response = await fetch(`${API_URL}/measure-data/device/${deviceId}`);
        const data = await response.json();

        logger.addEntry(`Pobrano dane pomiarowe dla urządzenia ${deviceId}`, 'response');

        const pomiaryTable = document.getElementById('pomiaryTable')?.querySelector('tbody');
        if (pomiaryTable) {
            pomiaryTable.innerHTML = '';

            const records = Array.isArray(data) ? data : [data];

            if (records.length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = '<td colspan="4" style="text-align: center;">Brak danych pomiarowych</td>';
                pomiaryTable.appendChild(emptyRow);
            } else {
                records.sort((a, b) => new Date(b.currentTime) - new Date(a.currentTime));

                records.forEach(record => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${formatDateTime(record.currentTime)}</td>
                        <td>${record.speed}</td>
                        <td>${record.rate}</td>
                        <td>${record.total}</td>
                    `;
                    pomiaryTable.appendChild(row);
                });
            }
        }
    } catch (error) {
        logger.addEntry(`Błąd połączenia: ${error.message}`, 'error');

        const pomiaryTable = document.getElementById('pomiaryTable')?.querySelector('tbody');
        if (pomiaryTable) {
            pomiaryTable.innerHTML = '';
            const errorRow = document.createElement('tr');
            errorRow.innerHTML = '<td colspan="4" style="text-align: center; color: #c0392b;">Błąd podczas pobierania danych</td>';
            pomiaryTable.appendChild(errorRow);
        }
    }
}

// Aktualizuje parametr na serwerze
export async function updateParameter(address, value) {
    const deviceId = getDeviceId();

    if (!deviceId) {
        logger.addEntry('Błąd: Wprowadź ID urządzenia', 'error');
        return;
    }

    try {
        const paramInfo = PARAMETER_MAPPING[address];
        logger.addEntry(`Aktualizacja parametru ${paramInfo.label} (${address}) na wartość: ${value}`, 'request');

        const response = await fetch(`${API_URL}/app/devices/${deviceId}/parameters/${address}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({param_data: value})
        });

        const data = await response.json();

        if (data.status === 'error') {
            logger.addEntry(`Błąd: ${data.message}`, 'error');
            return;
        }

        logger.addEntry(`Parametr zaktualizowany w bazie: ${data.message}, nowa wartość: ${data.value}`, 'response');

    } catch (error) {
        logger.addEntry(`Błąd połączenia: ${error.message}`, 'error');
    }
}

// Aktualizuje alias na serwerze
export async function updateAlias(fieldName, value) {
    const deviceId = getDeviceId();

    if (!deviceId) {
        logger.addEntry('Błąd: Wprowadź ID urządzenia', 'error');
        return;
    }

    if (!value.trim()) {
        logger.addEntry('Błąd: Wprowadź wartość pola', 'error');
        return;
    }

    const fieldAddress = ALIAS_ADDRESS_MAPPING[fieldName];
    if (!fieldAddress) {
        logger.addEntry(`Błąd: Nieznane pole '${fieldName}'`, 'error');
        return;
    }

    try {
        logger.addEntry(`Aktualizacja pola '${fieldName}' (adres ${fieldAddress}) na wartość: ${value}`, 'request');

        const updateResponse = await fetch(`${API_URL}/aliases/${deviceId}/field/${fieldAddress}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                field_address: fieldAddress,
                field_value: value
            })
        });

        if (!updateResponse.ok) {
            const errorData = await updateResponse.json();
            throw new Error(errorData.detail || `Status: ${updateResponse.status}`);
        }

        const result = await updateResponse.json();

        if (result.status === 'success') {
            logger.addEntry(`✓ ${result.message}`, 'success');
            if (result.old_value !== result.new_value) {
                logger.addEntry(`Zmiana [${result.field_address}]: '${result.old_value}' → '${result.new_value}'`, 'info');
            }
        } else {
            logger.addEntry(`Nieoczekiwana odpowiedź: ${result.message}`, 'warning');
        }

    } catch (error) {
        logger.addEntry(`Błąd podczas aktualizacji pola '${fieldName}' (adres ${fieldAddress}): ${error.message}`, 'error');
    }
}