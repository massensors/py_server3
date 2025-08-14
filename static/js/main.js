// sysytem ID :  1126326593
// Konfiguracja API
const API_URL = '';  // Puste dla relatywnych URLi

// Stan trybu serwisowego
let serviceModeEnabled = false;

// Interval dla automatycznego odświeżania
let serviceModeAutoRefreshInterval = null;

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

// Mapowanie pól aliasów
const ALIAS_FIELDS = [
    { name: "company", label: "Firma" },
    { name: "location", label: "Lokalizacja" },
    { name: "productName", label: "Nazwa produktu" },
    { name: "scaleId", label: "ID wagi" }
];

// Inicjalizacja
document.addEventListener('DOMContentLoaded', function() {
    // Elementy DOM
    const deviceIdInput = document.getElementById('deviceId');
    const loadDeviceBtn = document.getElementById('loadDevice');
    const parametersGrid = document.querySelector('.parameters-grid');
    const aliasyGrid = document.querySelector('.aliasy-grid');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const logEntries = document.getElementById('logEntries');
    const clearLogBtn = document.getElementById('clearLog');
    const refreshPomiaryBtn = document.getElementById('refreshPomiary');
    const pomiaryTable = document.getElementById('pomiaryTable').querySelector('tbody');
    const serviceModeToggle = document.getElementById('serviceModeToggle');
    const refreshServiceModeBtn = document.getElementById('refreshServiceMode');

    // ===== FUNKCJE POMOCNICZE =====

    // Funkcja do wczytywania statusu trybu serwisowego
    async function loadServiceModeStatus(isManualRefresh = false) {
        try {
            const response = await fetch(`${API_URL}/service-mode/status`);
            if (response.ok) {
                const data = await response.json();
                serviceModeEnabled = data.enabled;
                if (serviceModeToggle) {
                    serviceModeToggle.checked = data.enabled;
                }
                updateServiceModeStatusDisplay(data.status_message, data.active);

                // Loguj tylko ręczne odświeżenia, nie automatyczne
                if (isManualRefresh) {
                    addLogEntry('Status trybu serwisowego odświeżony', 'success');
                }
            }
        } catch (error) {
            console.error('Błąd podczas wczytywania statusu trybu serwisowego:', error);
            updateServiceModeStatusDisplay("Błąd komunikacji", false);

            if (isManualRefresh) {
                addLogEntry('Błąd podczas odświeżania statusu trybu serwisowego', 'error');
            }
        }
    }

    // Funkcja do aktualizacji wyświetlania statusu
    function updateServiceModeStatusDisplay(statusMessage, isActive = false) {
        const statusElement = document.getElementById('serviceModeStatus');
        if (!statusElement) return;

        const statusText = statusElement.querySelector('.status-text');

        if (statusText) {
            statusText.textContent = statusMessage;

            // Resetowanie klas CSS
            statusElement.className = 'service-mode-status';

            // Dodanie odpowiedniej klasy w zależności od statusu
            if (isActive || statusMessage.includes('aktywny')) {
                statusElement.classList.add('status-active');
            } else if (statusMessage.includes('ruchu')) {
                statusElement.classList.add('status-warning');
            } else if (statusMessage.includes('błąd') || statusMessage.includes('Błąd') || statusMessage.includes('Nieaktywny')) {
                statusElement.classList.add('status-error');
            } else {
                statusElement.classList.add('status-inactive');
            }
        }
    }

    // Funkcja startująca automatyczne odświeżanie
    function startAutoRefresh() {
        // Zatrzymaj poprzedni interval jeśli istnieje
        if (serviceModeAutoRefreshInterval) {
            clearInterval(serviceModeAutoRefreshInterval);
        }

        // Rozpocznij nowy interval (odświeżaj co 2 sekundy)
        serviceModeAutoRefreshInterval = setInterval(() => {
            loadServiceModeStatus(false); // false = automatyczne odświeżanie (bez logowania)
        }, 2000);
    }

    // Funkcja zatrzymująca automatyczne odświeżanie
    function stopAutoRefresh() {
        if (serviceModeAutoRefreshInterval) {
            clearInterval(serviceModeAutoRefreshInterval);
            serviceModeAutoRefreshInterval = null;
        }
    }

    // Sprawdza czy zakładka Parametry jest aktywna
    function isParametersTabActive() {
        const activeTab = document.querySelector('.tab-btn.active');
        return activeTab && activeTab.getAttribute('data-tab') === 'parameters';
    }

    // Funkcja dodająca wpis do logu
    function addLogEntry(message, type = 'info') {
        if (!logEntries) return;

        const entry = document.createElement('div');
        entry.className = `log-entry log-${type}`;
        entry.innerHTML = `
            <span class="log-time">${new Date().toLocaleTimeString()}</span>
            <span class="log-message">${message}</span>
        `;
        logEntries.appendChild(entry);
        logEntries.scrollTop = logEntries.scrollHeight;
    }

    // Formatuje datę i czas do czytelnego formatu
    function formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        return date.toLocaleString('pl-PL');
    }

    // ===== INICJALIZACJA TRYBU SERWISOWEGO =====

    // Obsługa przełącznika trybu serwisowego
    if (serviceModeToggle) {
        // Inicjalizacja - pobierz aktualny stan z serwera
        loadServiceModeStatus(true);

        // Rozpocznij automatyczne odświeżanie (zakładka Parametry jest aktywna domyślnie)
       // startAutoRefresh();

        // JEDYNY event listener dla serviceModeToggle
        serviceModeToggle.addEventListener('change', async function() {
            const enabled = this.checked;

            try {
                const response = await fetch(`${API_URL}/service-mode/toggle`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ enabled: enabled })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                serviceModeEnabled = data.enabled;

                // Aktualizacja wyświetlania statusu
                updateServiceModeStatusDisplay(data.status_message, data.active);

                addLogEntry(
                    `Tryb serwisowy ${serviceModeEnabled ? 'WŁĄCZONY' : 'WYŁĄCZONY'} - ${data.status_message}`,
                    serviceModeEnabled ? 'success' : 'info'
                );

            } catch (error) {
                // W przypadku błędu, przywróć poprzedni stan przełącznika
                this.checked = !enabled;
                updateServiceModeStatusDisplay("Błąd komunikacji", false);
                addLogEntry(`Błąd podczas przełączania trybu serwisowego: ${error.message}`, 'error');
            }
        });
    }

    // Obsługa przycisku odświeżania trybu serwisowego
    if (refreshServiceModeBtn) {
        refreshServiceModeBtn.addEventListener('click', async function() {
            addLogEntry('Ręczne odświeżanie statusu trybu serwisowego...', 'info');
            await loadServiceModeStatus(true); // true = ręczne odświeżanie (z logowaniem)
        });
    }

    // ===== OBSŁUGA ZAKŁADEK =====

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

            // Zarządzanie automatycznym odświeżaniem w zależności od zakładki
            if (tabId === 'parameters') {
                // Włącz automatyczne odświeżanie dla zakładki Parametry
                startAutoRefresh();
                addLogEntry('Automatyczne odświeżanie trybu serwisowego włączone', 'info');
            } else {
                // Wyłącz automatyczne odświeżanie dla innych zakładek
                stopAutoRefresh();
                addLogEntry('Automatyczne odświeżanie trybu serwisowego wyłączone', 'info');
            }

            // Jeśli przełączamy na zakładkę pomiary, wczytujemy dane pomiarowe
            if (tabId === 'pomiary') {
                const deviceId = deviceIdInput ? deviceIdInput.value.trim() : '';
                if (deviceId) {
                    loadPomiaryData();
                }
            }
        });
    });

    // Zatrzymaj automatyczne odświeżanie gdy strona jest ukrywana
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopAutoRefresh();
        } else if (isParametersTabActive()) {
            // Wznów automatyczne odświeżanie tylko jeśli zakładka Parametry jest aktywna
            startAutoRefresh();
        }
    });

    // Zatrzymaj automatyczne odświeżanie przed zamknięciem strony
    window.addEventListener('beforeunload', function() {
        stopAutoRefresh();
    });

    // ===== POZOSTAŁE EVENT LISTENERY =====

    // Czyszczenie logów
    if (clearLogBtn) {
        clearLogBtn.addEventListener('click', () => {
            if (logEntries) {
                logEntries.innerHTML = '';
            }
        });
    }

    // Wczytanie danych urządzenia
    if (loadDeviceBtn) {
        loadDeviceBtn.addEventListener('click', () => {
            const deviceId = deviceIdInput ? deviceIdInput.value.trim() : '';
            if (!deviceId) {
                addLogEntry('Błąd: Wprowadź ID urządzenia', 'error');
                return;
            }

            // Wczytujemy dane odpowiednie dla aktywnej zakładki
            const activeTabBtn = document.querySelector('.tab-btn.active');
            const activeTab = activeTabBtn ? activeTabBtn.getAttribute('data-tab') : 'parameters';

            if (activeTab === 'parameters') {
                loadDeviceData();
            } else if (activeTab === 'pomiary') {
                loadPomiaryData();
            } else if (activeTab === 'aliasy') {
                loadAliasyData();
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

    // ===== INICJALIZACJA GRID'ÓW =====

    // Wypełniamy grid parametrami
    createParametersGrid();

    // Wypełniamy grid aliasami
    createAliasyGrid();

    // ===== FUNKCJE TWORZĄCE GRID'Y =====

    // Tworzy siatkę parametrów
    function createParametersGrid() {
        if (!parametersGrid) return;

        // Czyścimy istniejące parametry
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

    // Tworzy siatkę aliasów
    function createAliasyGrid() {
        if (!aliasyGrid) return;

        // Czyścimy istniejące aliasy
        aliasyGrid.innerHTML = '';

        // Tworzymy elementy dla każdego pola aliasu
        for (const field of ALIAS_FIELDS) {
            const aliasItem = document.createElement('div');
            aliasItem.className = 'alias-item';
            aliasItem.setAttribute('data-field', field.name);

            aliasItem.innerHTML = `
                <div class="alias-header">
                    <span class="alias-name">${field.label}</span>
                </div>
                <div class="alias-input">
                    <input type="text" class="alias-value" placeholder="${field.label}">
                    <button class="update-btn">Aktualizuj</button>
                </div>
            `;

            // Dodajemy obsługę przycisku aktualizacji
            aliasItem.querySelector('.update-btn').addEventListener('click', () => {
                const value = aliasItem.querySelector('.alias-value').value;
                updateAlias(field.name, value);
            });

            aliasyGrid.appendChild(aliasItem);
        }
    }

    // ===== FUNKCJE ŁADOWANIA DANYCH =====

    // Wczytuje dane urządzenia z serwera
    async function loadDeviceData() {
        const deviceId = deviceIdInput ? deviceIdInput.value.trim() : '';

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
                    if (valueInput) {
                        valueInput.value = param.value;
                    }
                }
            }
        } catch (error) {
            addLogEntry(`Błąd połączenia: ${error.message}`, 'error');
        }
    }

    // Wczytuje dane aliasów z serwera
    async function loadAliasyData() {
        const deviceId = deviceIdInput ? deviceIdInput.value.trim() : '';

        if (!deviceId) {
            addLogEntry('Błąd: Wprowadź ID urządzenia', 'error');
            return;
        }

        try {
            addLogEntry(`Pobieranie aliasów dla urządzenia ${deviceId}...`, 'request');

            const response = await fetch(`${API_URL}/aliases/${deviceId}`);

            if (!response.ok) {
                throw new Error(`Status: ${response.status}`);
            }

            const data = await response.json();

            addLogEntry(`Pobrano aliasy dla urządzenia ${deviceId}`, 'response');

            // Wypełniamy pola wartościami z serwera
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
            addLogEntry(`Błąd podczas pobierania aliasów: ${error.message}`, 'error');
        }
    }

    // Wczytuje dane pomiarowe z serwera
    async function loadPomiaryData() {
        const deviceId = deviceIdInput ? deviceIdInput.value.trim() : '';

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
            if (pomiaryTable) {
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
            }
        } catch (error) {
            addLogEntry(`Błąd połączenia: ${error.message}`, 'error');

            // Czyścimy istniejące dane
            if (pomiaryTable) {
                pomiaryTable.innerHTML = '';

                // Dodajemy komunikat o błędzie
                const errorRow = document.createElement('tr');
                errorRow.innerHTML = '<td colspan="4" style="text-align: center; color: #c0392b;">Błąd podczas pobierania danych</td>';
                pomiaryTable.appendChild(errorRow);
            }
        }
    }

    // ===== FUNKCJE AKTUALIZACJI =====

    // Aktualizuje parametr na serwerze
    async function updateParameter(address, value) {
        const deviceId = deviceIdInput ? deviceIdInput.value.trim() : '';

        if (!deviceId) {
            addLogEntry('Błąd: Wprowadź ID urządzenia', 'error');
            return;
        }

        try {
            const paramInfo = PARAMETER_MAPPING[address];
            addLogEntry(`Aktualizacja parametru ${paramInfo.label} (${address}) na wartość: ${value}`, 'request');

            // 1. Aktualizacja w bazie danych (standardowy sposób)
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

            addLogEntry(`Parametr zaktualizowany w bazie: ${data.message}, nowa wartość: ${data.value}`, 'response');

            // 2. Wywołanie funkcji _handle_service_data z param_address i param_data


        } catch (error) {
            addLogEntry(`Błąd połączenia: ${error.message}`, 'error');
        }
    }

    // Aktualizuje alias na serwerze
    async function updateAlias(fieldName, value) {
        const deviceId = deviceIdInput ? deviceIdInput.value.trim() : '';

        if (!deviceId) {
            addLogEntry('Błąd: Wprowadź ID urządzenia', 'error');
            return;
        }

        try {
            // Najpierw pobieramy aktualne dane aliasów
            const response = await fetch(`${API_URL}/aliases/${deviceId}`);
            if (!response.ok) {
                throw new Error(`Status: ${response.status}`);
            }

            const currentData = await response.json();

            // Przygotowujemy nowe dane z zaktualizowanym polem
            const updatedData = {
                deviceId: deviceId,
                company: currentData.company || '',
                location: currentData.location || '',
                productName: currentData.productName || '',
                scaleId: currentData.scaleId || ''
            };

            // Aktualizujemy tylko wybrane pole
            updatedData[fieldName] = value;

            addLogEntry(`Aktualizacja aliasu ${fieldName} na wartość: ${value}`, 'request');

            // Wysyłamy zaktualizowane dane
            const updateResponse = await fetch(`${API_URL}/aliases/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updatedData)
            });

            const updateResult = await updateResponse.json();

            if (updateResponse.ok) {
                addLogEntry(`Alias zaktualizowany: ${fieldName} = ${value}`, 'response');
            } else {
                addLogEntry(`Błąd: ${updateResult.detail || 'Nieznany błąd'}`, 'error');
            }
        } catch (error) {
            addLogEntry(`Błąd podczas aktualizacji aliasu: ${error.message}`, 'error');
        }
    }
});