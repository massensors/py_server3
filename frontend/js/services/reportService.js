import { logger } from './logger.js';
import { API_URL } from '../config/constants.js';
import { getDeviceId } from '../utils/helpers.js';

class ReportService {
    constructor() {
        this.API_URL = API_URL;
    }

    /**
     * Generuje i pobiera raport CSV dla wybranego okresu
     */
    async generateReport(periodControl) {
        try {
            const deviceId = getDeviceId();
            if (!deviceId) {
                throw new Error('Brak wybranego urządzenia');
            }

            // Pobierz aktualny okres z kontrolki
            const periodData = periodControl.getCurrentPeriod();
            if (!periodData) {
                throw new Error('Wybierz okres dla raportu');
            }

            logger.addEntry('📄 Generowanie raportu CSV...', 'info');

            // Przygotuj parametry zapytania
            const params = new URLSearchParams();
            params.append('period_type', periodData.type);

            if (periodData.type === 'custom') {
                if (!periodData.startDate || !periodData.endDate) {
                    throw new Error('Wybierz daty początku i końca okresu');
                }
                params.append('start_date', periodData.startDate);
                params.append('end_date', periodData.endDate);
            }

            // Wywołaj endpoint
            const response = await fetch(`${this.API_URL}/reports/generate-report?${params}`, {
                method: 'GET',
                headers: {
                    'Accept': 'text/csv'
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            // Pobierz nazwę pliku z nagłówka odpowiedzi
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'raport.csv';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }

            // Pobierz zawartość CSV
            const csvContent = await response.blob();

            // Automatycznie pobierz plik
            this.downloadFile(csvContent, filename);

            logger.addEntry(`✅ Raport CSV został wygenerowany: ${filename}`, 'success');

            return {
                success: true,
                filename: filename
            };

        } catch (error) {
            logger.addEntry(`❌ Błąd generowania raportu: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Pobiera plik przez przeglądarkę
     */
    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;

        // Dodaj do DOM, kliknij i usuń
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Zwolnij URL
        window.URL.revokeObjectURL(url);
    }
}

// Export instancji serwisu
export const reportService = new ReportService();