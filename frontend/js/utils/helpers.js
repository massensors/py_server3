// Formatuje datę i czas do czytelnego formatu
export function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    return date.toLocaleString('pl-PL');
}

// Pobiera wartość device ID z formularza
export function getDeviceId() {
    const deviceIdInput = document.getElementById('deviceId');
    return deviceIdInput ? deviceIdInput.value.trim() : '';
}

// Sprawdza czy zakładka Parametry jest aktywna
export function isParametersTabActive() {
    const activeTab = document.querySelector('.tab-btn.active');
    return activeTab && activeTab.getAttribute('data-tab') === 'parameters';
}