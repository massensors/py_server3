// sysytem ID :  1126326593
// Konfiguracja API
const API_URL = '';  // Puste dla relatywnych URLi

// Mapowanie adresów parametrów (musi być zgodne z backend)
const PARAMETER_MAPPING = {
    0: { name: "dummy", label: "Dummy", format: "1B" },
    1: { name: "filterRate", label: "Filter Rate", format: "1B" },
    2: { name: "scaleCapacity", label: "Scale Capacity", format: "8B" },
    3: { name: "autoZero", label: "Auto Zero", format: "8B" },
    4: { name: "deadBand", label: "Dead Band", format: "8B" },
    5: { name: "scaleType", label: "Scale Type", format: "1B" },
    6: { name: "loadcellSet", label: "Load Cell Set", format: "1B" },
    7: { name: "loadcellCapacity", label: "Load Cell Capacity", format: "8B" },
    8: { name: "trimm", label: "Trimm", format: "8B" },
    9: { name: "idlerSpacing", label: "Idler Spacing", format: "8B" },
    10: { name: "speedSource", label: "Speed Source", format: "1B" },
    11: { name: "wheelDiameter", label: "Wheel Diameter", format: "8B" },
    12: { name: "pulsesPerRev", label: "Pulses Per Rev", format: "8B" },
    13: { name: "beltLength", label: "Belt Length", format: "8B" },
    14: { name: "beltLengthPulses", label: "Belt Length Pulses", format: "8B" },
    15: { name: "currentTime", label: "Current Time", format: "19B" }
};

// Inicjalizacja
document.addEventListener('DOMContentLoaded', function() {
    // Elementy DOM - przenosimy tutaj, aby mieć pewność, że DOM jest już załadowany
    const deviceIdInput = document.getElementById('deviceId');
    const loadDeviceBtn = document.getElementById('loadDevice');
    const parametersGrid = document.querySelector('.parameters-grid');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const logEntries = document.getElementById('logEntries');
    const clearLogBtn = document.getElementById('clearLog');
    const refreshPomiaryBtn = document.getElementById('refreshPomiary');
    const pomiaryTable = document.getElementById('pomiaryTable').querySelector('tbody');

    // Obsługa zakładek
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Usuwamy klasę active z wszystkich przycisków i zawartości
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Dodajemy klasę active do klikniętego przycisku i odpowiedniej zawartości
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');

            // Jeśli przełączamy na zakładkę pomiary, wczytujemy dane pomiarowe
            if (tabId === 'pomiary') {
                const deviceId = deviceIdInput.value.trim();
                if (deviceId) {
                    loadPomiaryData();
                }
            }
        });
    });

    // Czyszczenie logów
    if (clearLogBtn) {
        clearLogBtn.addEventListener('click', () => {
            logEntries.innerHTML = '';
        });
    }

    // Wczytanie danych urządzenia
    if (loadDeviceBtn) {
        loadDeviceBtn.addEventListener('click', () => {
            const deviceId = deviceIdInput.value.trim();
            if (!deviceId) {
                addLogEntry('Błąd: Wprowadź ID urządzenia', 'error');
                return;
            }

            // Wczytujemy dane odpowiednie dla aktywnej zakładki
            const activeTab = document.querySelector('.tab-btn.active').getAttribute('data-tab');

            if (activeTab === 'parameters') {
                loadDeviceData();
            } else if (activeTab === 'pomiary') {
                loadPomiaryData();
            } else {
                // Dla zakładki monitor lub innych zakładek
                loadDeviceData();
            }
        });
    }

    // Odświeżanie danych pomiarowych
    if (refreshPomiaryBtn) {
        refreshPomiaryBtn.addEventListener('click', () => {
            console.log('Odświeżanie danych pomiarowych...');
            loadPomiaryData();
        });
    }

    // Wypełniamy grid parametrami
    createParametersGrid();

    // Funkcje pomocnicze

    // Tworzy siatkę parametrów
    function createParametersGrid() {
        // Czyścimy istniejące parametry
        if (parametersGrid) {
            parametersGrid.innerHTML = '';

            // Tworzymy elementy dla każdego parametru
            for (const [address, param] of Object.entries(PARAMETER_MAPPING)) {
                const paramItem = document.createElement('div');
                paramItem.className = 'parameter-item';
                paramItem.setAttribute('data-address', address);

                paramItem.innerHTML = `
                    <div class="param-header">
                        <span class="param-name">${param.label}</span>
                        <span class="param-address">[${address}]</span>
                    </div>
                    <div class="param-input">
                        <input type="text" class="param-value" data-format="${param.format}" placeholder="${param.format}">
                        <button class="update-btn">Aktualizuj</button>
                    </div>
                `;

                // Dodajemy obsługę przycisku aktualizacji
                paramItem.querySelector('.update-btn').addEventListener('click', () => {
                    const value = paramItem.querySelector('.param-value').value;
                    updateParameter(address, value);
                });

                parametersGrid.appendChild(paramItem);
            }
        }
    }

    // Wczytuje dane urządzenia z serwera
    async function loadDeviceData() {
        const deviceId = deviceIdInput.value.trim();

        if (!deviceId) {
            addLogEntry('Błąd: Wprowadź ID urządzenia', 'error');
            return;
        }

        try {
            addLogEntry(`Pobieranie parametrów dla urządzenia ${deviceId}...`, 'request');

            const response = await fetch(`${API_URL}/app/devices/${deviceId}/parameters`);
            const data = await response.json();

            if (data.status === 'error') {
                addLogEntry(`Błąd: ${data.message}`, 'error');
                return;
            }

            addLogEntry(`Pobrano parametry dla urządzenia ${deviceId}`, 'response');

            // Wypełniamy pola wartościami z serwera
            for (const [address, param] of Object.entries(data.parameters)) {
                const paramItem = document.querySelector(`.parameter-item[data-address="${address}"]`);
                if (paramItem) {
                    const valueInput = paramItem.querySelector('.param-value');
                    valueInput.value = param.value;
                }
            }
        } catch (error) {
            addLogEntry(`Błąd połączenia: ${error.message}`, 'error');
        }
    }

    // Wczytuje dane pomiarowe z serwera
    async function loadPomiaryData() {
        const deviceId = deviceIdInput.value.trim();

        if (!deviceId) {
            addLogEntry('Błąd: Wprowadź ID urządzenia', 'error');
            return;
        }

        try {
            addLogEntry(`Pobieranie danych pomiarowych dla urządzenia ${deviceId}...`, 'request');

            // Używamy nowego endpointu dla wszystkich rekordów
            const response = await fetch(`${API_URL}/measure-data/device/${deviceId}`);
            const data = await response.json();

            addLogEntry(`Pobrano dane pomiarowe dla urządzenia ${deviceId}`, 'response');

            // Czyścimy istniejące dane
            pomiaryTable.innerHTML = '';

            // Sprawdzamy czy otrzymaliśmy tablicę rekordów
            const records = Array.isArray(data) ? data : [data];

            // Dodajemy nowe dane do tabeli
            if (records.length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = '<td colspan="4" style="text-align: center;">Brak danych pomiarowych</td>';
                pomiaryTable.appendChild(emptyRow);
            } else {
                // Sortujemy dane według czasu (od najnowszych)
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
        } catch (error) {
            addLogEntry(`Błąd połączenia: ${error.message}`, 'error');

            // Czyścimy istniejące dane
            pomiaryTable.innerHTML = '';

            // Dodajemy komunikat o błędzie
            const errorRow = document.createElement('tr');
            errorRow.innerHTML = '<td colspan="4" style="text-align: center; color: #c0392b;">Błąd podczas pobierania danych</td>';
            pomiaryTable.appendChild(errorRow);
        }
    }

    // Aktualizuje parametr na serwerze
    async function updateParameter(address, value) {
        const deviceId = deviceIdInput.value.trim();

        if (!deviceId) {
            addLogEntry('Błąd: Wprowadź ID urządzenia', 'error');
            return;
        }

        try {
            const paramInfo = PARAMETER_MAPPING[address];
            addLogEntry(`Aktualizacja parametru ${paramInfo.label} (${address}) na wartość: ${value}`, 'request');

            const response = await fetch(`${API_URL}/app/devices/${deviceId}/parameters/${address}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ param_data: value })
            });

            const data = await response.json();

            if (data.status === 'error') {
                addLogEntry(`Błąd: ${data.message}`, 'error');
                return;
            }

            addLogEntry(`Parametr zaktualizowany: ${data.message}, nowa wartość: ${data.value}`, 'response');
        } catch (error) {
            addLogEntry(`Błąd połączenia: ${error.message}`, 'error');
        }
    }

    // Dodaje wpis do logów
    function addLogEntry(message, type = 'info') {
        if (!logEntries) return;

        const entry = document.createElement('div');
        entry.className = `log-entry log-${type}`;

        const timestamp = new Date().toLocaleTimeString();
        entry.textContent = `[${timestamp}] ${message}`;

        logEntries.appendChild(entry);
        logEntries.scrollTop = logEntries.scrollHeight; // Przewijamy na dół
    }

    // Formatuje datę i czas do czytelnego formatu
    function formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        return date.toLocaleString('pl-PL');
    }
});