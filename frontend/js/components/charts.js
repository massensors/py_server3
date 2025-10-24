import { logger } from '../services/logger.js';
import { API_URL } from '../config/constants.js';
import { getDeviceId } from '../utils/helpers.js';
import { formatDateForAPI } from '../services/api.js';

/**
 * Moduł obsługi wykresów pomiarowych
 * Zawiera funkcje do ładowania i wyświetlania wykresów wydajności i sumy przyrostowej
 */

/**
 * Ładuje i wyświetla wykres wydajności (rate) dla wybranego okresu
 * @param {PeriodControl} periodControl - Kontroler okresu pomiarowego
 * @returns {Promise<Object>} - Dane wykresu
 */
export async function loadRateChart(periodControl = null) {
    try {
        logger.addEntry(' Pobieranie danych wykresu wydajności...', 'info');

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
                if (period.startDate && period.endDate) {
                    params.append('period_type', 'custom');
                    const startFormatted = formatDateForAPI(period.startDate);
                    const endFormatted = formatDateForAPI(period.endDate);

                    if (startFormatted && endFormatted) {
                        params.append('start_date', startFormatted);
                        params.append('end_date', endFormatted);
                    }
                } else {
                    logger.addEntry(' Niepełne daty dla okresu niestandardowego', 'warning');
                }
            }
        }

        // Dostosuj liczbę punktów do szerokości ekranu
        const maxPoints = window.innerWidth > 1600 ? 1000 : 500;
        params.append('max_points', maxPoints.toString());

        const url = `${API_URL}/measure-data/filtered/rate-chart-data?${params.toString()}`;
        logger.addEntry(` Żądanie wykresu wydajności: ${url}`, 'debug');

        const response = await fetch(url);

        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorData}`);
        }

        const data = await response.json();

        logger.addEntry(` Pobrano ${data.timestamps.length} punktów dla wykresu wydajności`, 'success');
        logger.addEntry(` Zakres: 0 - ${data.max_rate.toFixed(2)}, Średnia: ${data.avg_rate.toFixed(2)}`, 'info');

        // Wyświetl wykres
        displayRateChart(data);

        return data;

    } catch (error) {
        const errorMsg = `Błąd pobierania danych wykresu wydajności: ${error.message}`;
        logger.addEntry(errorMsg, 'error');
        console.error('Błąd loadRateChart:', error);
        throw error;
    }
}

/**
 * ✅ POPRAWIONA FUNKCJA - Formatowanie etykiet czasu dla wykresów
 * Na osi X pokazuje tylko unikalne daty, w tooltipach pełne informacje z godziną
 * @param {Array<string>} timestamps - Lista timestampów
 * @returns {Array<string>} - Sformatowane etykiety
 */
function formatChartLabels(timestamps) {
    if (!timestamps || timestamps.length === 0) {
        return [];
    }

    // Konwertuj na obiekty Date
    const dates = timestamps.map(ts => new Date(ts));

    // Sprawdź zakres czasowy (w dniach)
    const firstDate = dates[0];
    const lastDate = dates[dates.length - 1];
    const daysDiff = (lastDate - firstDate) / (1000 * 60 * 60 * 24);

    // STRATEGIA: Pokaż datę tylko przy pierwszym wystąpieniu tego dnia
    let lastDisplayedDate = null;

    return dates.map((date, index) => {
        const currentDate = date.toLocaleDateString('pl-PL', {
            day: '2-digit',
            month: '2-digit',
            year: daysDiff > 365 ? '2-digit' : undefined  // Rok tylko jeśli okres > 1 rok
        });

        // Pokaż datę tylko jeśli:
        // 1. To pierwszy punkt
        // 2. Data różni się od ostatnio wyświetlonej
        // 3. To ostatni punkt (dla pewności)
        if (index === 0 || currentDate !== lastDisplayedDate || index === dates.length - 1) {
            lastDisplayedDate = currentDate;
            return currentDate;
        }

        // Dla pozostałych punktów tego samego dnia - pusta etykieta
        return '';
    });
}

/**
 * Wyświetla wykres wydajności w canvas
 * @param {Object} data - Dane wykresu z API
 */
function displayRateChart(data) {
    const chartCanvas = document.getElementById('rateChart');

    if (!chartCanvas) {
        logger.addEntry('❌ Nie znaleziono elementu canvas dla wykresu wydajności', 'error');
        return;
    }

    // Zniszcz poprzedni wykres jeśli istnieje
    if (window.rateChartInstance) {
        window.rateChartInstance.destroy();
    }

    // ✅ Użyj nowej funkcji formatowania (tylko unikalne daty na osi)
    const labels = formatChartLabels(data.timestamps);

    const ctx = chartCanvas.getContext('2d');

    // Przygotuj datasets - wydajność i opcjonalnie prędkość
    const datasets = [
        {
            label: 'Wydajność (Rate)',
            data: data.rate_values,
            borderColor: '#2ecc71',
            backgroundColor: 'rgba(46, 204, 113, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.1,
            pointRadius: data.timestamps.length > 200 ? 0 : 2,
            pointHoverRadius: 5,
            yAxisID: 'y'
        }
    ];

    // Dodaj prędkość jako drugą linię (opcjonalnie)
    if (data.speed_values && data.speed_values.length > 0) {
        datasets.push({
            label: 'Prędkość (Speed)',
            data: data.speed_values,
            borderColor: '#e74c3c',
            backgroundColor: 'rgba(231, 76, 60, 0.1)',
            borderWidth: 1.5,
            fill: false,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 4,
            yAxisID: 'y1',
            borderDash: [5, 5]  // Linia przerywana
        });
    }

    window.rateChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Wydajność produkcji - ${data.period_info}`,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: function(context) {
                            // ✅ W tooltipie ZAWSZE pokazuj pełną datę i godzinę
                            const timestamp = data.timestamps[context[0].dataIndex];
                            const date = new Date(timestamp);
                            return date.toLocaleString('pl-PL', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit'
                            });
                        },
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y.toFixed(2);
                            return `${label}: ${value}`;
                        },
                        afterBody: function(tooltipItems) {
                            if (tooltipItems.length > 0) {
                                const index = tooltipItems[0].dataIndex;
                                const rate = data.rate_values[index];
                                const speed = data.speed_values[index];

                                // Określ status produkcji
                                let status = '⚪ Przestój';
                                if (rate > 0 && speed > 0) {
                                    status = '🟢 Produkcja aktywna';
                                } else if (speed > 0) {
                                    status = '🟡 Urządzenie pracuje';
                                }

                                return [`Status: ${status}`];
                            }
                            return [];
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Data'
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkip: false,  // ✅ Nie pomijaj automatycznie etykiet
                        callback: function(value, index, ticks) {
                            // Pokaż tylko niepuste etykiety
                            const label = this.getLabelForValue(value);
                            return label || undefined;  // undefined ukrywa etykietę
                        }
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Wydajność (Rate)',
                        color: '#2ecc71'
                    },
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2);
                        },
                        color: '#2ecc71'
                    },
                    grid: {
                        color: 'rgba(46, 204, 113, 0.1)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Prędkość (Speed)',
                        color: '#e74c3c'
                    },
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2);
                        },
                        color: '#e74c3c'
                    },
                    grid: {
                        drawOnChartArea: false  // Nie rysuj siatki dla drugiej osi
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });

    logger.addEntry('✅ Wykres wydajności został wyświetlony', 'success');
}

/**
 * Ładuje i wyświetla wykres sumy przyrostowej dla wybranego okresu
 * @param {PeriodControl} periodControl - Kontroler okresu pomiarowego
 * @returns {Promise<Object>} - Dane wykresu
 */
export async function loadIncrementalChart(periodControl = null) {
    try {
        logger.addEntry(' Pobieranie danych wykresu sumy przyrostowej...', 'info');

        let period = null;
        if (periodControl) {
            period = periodControl.getCurrentPeriod();
        }

        const params = new URLSearchParams();

        if (period) {
            if (period.type && period.type !== 'custom') {
                params.append('period_type', period.type);
            }

            if (period.type === 'custom') {
                if (period.startDate && period.endDate) {
                    params.append('period_type', 'custom');
                    const startFormatted = formatDateForAPI(period.startDate);
                    const endFormatted = formatDateForAPI(period.endDate);

                    if (startFormatted && endFormatted) {
                        params.append('start_date', startFormatted);
                        params.append('end_date', endFormatted);
                    }
                }
            }
        }

        const maxPoints = window.innerWidth > 1600 ? 1000 : 500;
        params.append('max_points', maxPoints.toString());

        const url = `${API_URL}/measure-data/filtered/chart-data?${params.toString()}`;

        const response = await fetch(url);

        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorData}`);
        }

        const data = await response.json();

        logger.addEntry(` Pobrano ${data.timestamps.length} punktów dla wykresu sumy przyrostowej`, 'success');

        displayIncrementalChart(data);

        return data;

    } catch (error) {
        const errorMsg = `Błąd pobierania danych wykresu sumy przyrostowej: ${error.message}`;
        logger.addEntry(errorMsg, 'error');
        console.error('Błąd loadIncrementalChart:', error);
        throw error;
    }
}
/**
 * Wyświetla wykres sumy przyrostowej w canvas
 * @param {Object} data - Dane wykresu z API
 */
function displayIncrementalChart(data) {
    const chartCanvas = document.getElementById('incrementalChart');

    if (!chartCanvas) {
        logger.addEntry(' Nie znaleziono elementu canvas dla wykresu sumy przyrostowej', 'error');
        return;
    }

    if (window.incrementalChartInstance) {
        window.incrementalChartInstance.destroy();
    }

    // ✅ UŻYJ NOWEJ FUNKCJI formatowania
    const labels = formatChartLabels(data.timestamps);

    const ctx = chartCanvas.getContext('2d');

    window.incrementalChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Suma przyrostowa',
                data: data.incremental_values,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1,
                pointRadius: data.timestamps.length > 200 ? 0 : 2,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Suma przyrostowa - ${data.period_info}`,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: function(context) {
                            // W tooltip pokaż pełną datę i godzinę
                            const timestamp = data.timestamps[context[0].dataIndex];
                            const date = new Date(timestamp);
                            return date.toLocaleString('pl-PL', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit'
                            });
                        },
                        label: function(context) {
                            return `Suma: ${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Data'
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkip: false,
                        callback: function(value, index, ticks) {
                            const label = this.getLabelForValue(value);
                            return label || undefined;
                        }
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Suma przyrostowa'
                    },
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2);
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });

    logger.addEntry(' Wykres sumy przyrostowej został wyświetlony', 'success');
}

/**
 * Niszczy wszystkie aktywne wykresy
 * Przydatne przy zmianie zakładek lub odświeżaniu
 */
export function destroyAllCharts() {
    if (window.rateChartInstance) {
        window.rateChartInstance.destroy();
        window.rateChartInstance = null;
    }
    if (window.incrementalChartInstance) {
        window.incrementalChartInstance.destroy();
        window.incrementalChartInstance = null;
    }
    logger.addEntry(' Wykresy zostały usunięte', 'debug');
}