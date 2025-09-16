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

// Dodaj do istniejącego api.js lub utwórz nowy jeśli nie istnieje



export async function loadMeasureData(periodControl = null) {
    try {
        logger.addEntry(' Pobieranie danych pomiarowych z inteligentnym próbkowaniem...', 'info');

        // Pobierz okres z periodControl
        let period = null;
        if (periodControl) {
            period = periodControl.getCurrentPeriod();
        }

        // Przygotuj parametry URL
        const params = new URLSearchParams();

        if (period) {
            // Dodaj typ okresu
            if (period.type && period.type !== 'custom') {
                params.append('period_type', period.type);
            }

            // Dla okresu niestandardowego dodaj konkretne daty
            if (period.type === 'custom') {
                if (period.startDateFormatted && period.endDateFormatted) {
                    params.append('period_type', 'custom');
                    params.append('start_date', period.startDateFormatted);
                    params.append('end_date', period.endDateFormatted);
                } else {
                    logger.addEntry('⚠️ Niepełne daty dla okresu niestandardowego', 'warning');
                }
            }

            logger.addEntry(` Pobieranie danych dla okresu: ${period.type}`, 'info');
        }

        // Automatyczne dostosowanie limitu na podstawie okresu
        const maxResults = _calculateOptimalLimit(period);
        params.append('max_results', maxResults.toString());

        const url = `${API_URL}/measure-data/filtered/list?${params.toString()}`;
        logger.addEntry(` Żądanie: ${url}`, 'debug');

        const response = await fetch(url);

        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorData}`);
        }

        const data = await response.json();

        logger.addEntry(`✅ Pobrano ${data.shown_count} z ${data.total_count} dostępnych pomiarów`, 'success');
        logger.addEntry(` ${data.sampling_info}`, 'info');

        // Aktualizuj tabelę
        updateMeasureTable(data.data, {
            total_count: data.total_count,
            shown_count: data.shown_count,
            sampling_info: data.sampling_info,
            period_info: data.period_info,
            device_id: data.device_id
        });

        return data;

    } catch (error) {
        const errorMsg = `Błąd pobierania danych pomiarowych: ${error.message}`;
        logger.addEntry(errorMsg, 'error');
        console.error('Błąd loadMeasureData:', error);

        // Wyczyść tabelę w przypadku błędu
        updateMeasureTable([], {
            total_count: 0,
            shown_count: 0,
            sampling_info: 'Błąd ładowania',
            period_info: 'Błąd'
        });

        throw error;
    }
}

export async function loadMeasureSummary(periodControl = null) {
    try {
        logger.addEntry(' Pobieranie podsumowania pomiarów...', 'info');

        let period = null;
        if (periodControl) {
            period = periodControl.getCurrentPeriod();
        }

        const params = new URLSearchParams();

        if (period) {
            if (period.type && period.type !== 'custom') {
                params.append('period_type', period.type);
            }

            if (period.type === 'custom' && period.startDateFormatted && period.endDateFormatted) {
                params.append('period_type', 'custom');
                params.append('start_date', period.startDateFormatted);
                params.append('end_date', period.endDateFormatted);
            }
        }

        const url = `${API_URL}/measure-data/filtered/summary?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorData}`);
        }

        const data = await response.json();

        logger.addEntry(` Podsumowanie: ${data.total_records} rekordów dla okresu ${data.period_info}`, 'success');
        console.log('Podsumowanie danych:', data);

        return data;

    } catch (error) {
        const errorMsg = `Błąd pobierania podsumowania: ${error.message}`;
        logger.addEntry(errorMsg, 'error');
        console.error('Błąd loadMeasureSummary:', error);
        throw error;
    }
}

function _calculateOptimalLimit(period) {
    // Automatyczne dostosowanie limitu na podstawie okresu
    if (!period || !period.type) return 500; // domyślny

    switch (period.type) {
        case 'current_month':
        case 'previous_month':
            return 1000; // miesiąc - więcej szczegółów
        case 'current_year':
        case 'previous_year':
            return 800; // rok - mniej szczegółów
        case 'custom':
            // Dla niestandardowego okresu sprawdź różnicę dat
            if (period.startDate && period.endDate) {
                const daysDiff = Math.abs((period.endDate - period.startDate) / (1000 * 60 * 60 * 24));
                if (daysDiff <= 7) return 1000; // tydzień - wszystkie szczegóły
                if (daysDiff <= 31) return 800;  // miesiąc
                if (daysDiff <= 365) return 500; // rok
                return 300; // więcej niż rok - rzadkie próbkowanie
            }
            return 500;
        default:
            return 500;
    }
}

function updateMeasureTable(measures, metadata = {}) {
    const tableBody = document.querySelector('#pomiaryTable tbody');
    if (!tableBody) {
        logger.addEntry('❌ Nie znaleziono tabeli pomiarów', 'error');
        return;
    }

    // Wyczyść tabelę
    tableBody.innerHTML = '';

    // Zaktualizuj informacje o próbkowaniu w UI
    updateSamplingInfo(metadata);

    if (!measures || measures.length === 0) {
        const row = tableBody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 4;
        cell.textContent = 'Brak danych pomiarowych dla wybranego okresu';
        cell.style.textAlign = 'center';
        cell.style.color = '#6c757d';
        cell.style.fontStyle = 'italic';
        cell.style.padding = '20px';
        return;
    }

    // Dodaj wiersze z danymi
    measures.forEach((measure, index) => {
        const row = tableBody.insertRow();

        // Data i czas
        const timeCell = row.insertCell();
        timeCell.textContent = measure.currentTime || 'N/A';

        // Prędkość
        const speedCell = row.insertCell();
        speedCell.textContent = _formatNumericValue(measure.speed);

        // Natężenie
        const rateCell = row.insertCell();
        rateCell.textContent = _formatNumericValue(measure.rate);

        // Suma
        const totalCell = row.insertCell();
        totalCell.textContent = _formatNumericValue(measure.total);

        // Stylowanie co drugiej linii
        if (index % 2 === 0) {
            row.style.backgroundColor = '#f8f9fa';
        }
    });

    logger.addEntry(` Wyświetlono ${measures.length} rekordów`, 'info');
}

function updateSamplingInfo(metadata) {
    // Znajdź lub utwórz element do wyświetlania informacji o próbkowaniu
    let samplingInfo = document.getElementById('samplingInfo');
    if (!samplingInfo) {
        // Utwórz element jeśli nie istnieje
        samplingInfo = document.createElement('div');
        samplingInfo.id = 'samplingInfo';
        samplingInfo.className = 'sampling-info';

        const pomiaryContainer = document.querySelector('.pomiary-container');
        if (pomiaryContainer) {
            pomiaryContainer.insertBefore(samplingInfo, document.getElementById('pomiaryTable'));
        }
    }

    if (metadata.sampling_info || metadata.total_count !== undefined) {
        let infoText = '';

        if (metadata.total_count > 0) {
            infoText += ` ${metadata.total_count} rekordów w okresie: ${metadata.period_info || 'Wszystkie'}`;
        }

        if (metadata.sampling_info && metadata.shown_count < metadata.total_count) {
            infoText += ` |  ${metadata.sampling_info}`;
        }

        samplingInfo.innerHTML = `<small style="color: #6c757d; margin-bottom: 10px; display: block;">${infoText}</small>`;
    }
}

function _formatNumericValue(value) {
    try {
        const numValue = parseFloat(value);
        return isNaN(numValue) ? value : numValue.toFixed(2);
    } catch {
        return value || 'N/A';
    }
}

// Eksportuj funkcje
export { updateMeasureTable, updateSamplingInfo };