// Nowy plik: /frontend/js/components/period-control.js

export class PeriodControl {
    constructor() {
        this.currentPeriod = null;
        this.startDate = null;
        this.endDate = null;

        // Dodaj opóźnienie dla pewności, że DOM jest gotowy
        setTimeout(() => {
            this.initEventListeners();
            this.setDefaultPeriod();
        }, 100);
    }

    initEventListeners() {
        console.log('🔧 Inicjalizacja event listeners dla kontroli okresu...');

        // Radio button handlers
        const periodRadios = document.querySelectorAll('input[name="period"]');
        console.log(`📻 Znaleziono ${periodRadios.length} radio buttons`);

        periodRadios.forEach(radio => {
            radio.addEventListener('change', () => this.handlePeriodChange(radio.value));
        });

        // Calendar button handlers - NOWE PODEJŚCIE
        this.setupCalendarHandlers();
    }

    setupCalendarHandlers() {
        const startDateBtn = document.getElementById('startDateBtn');
        const endDateBtn = document.getElementById('endDateBtn');
        const startDateInput = document.getElementById('startDateInput');
        const endDateInput = document.getElementById('endDateInput');

        console.log('📅 Sprawdzanie elementów kalendarza:', {
            startDateBtn: !!startDateBtn,
            endDateBtn: !!endDateBtn,
            startDateInput: !!startDateInput,
            endDateInput: !!endDateInput
        });

        if (startDateBtn && startDateInput) {
            startDateBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('📅 Kliknięto przycisk "od"');

                // Upewnij się, że radio "custom" jest zaznaczone
                const customRadio = document.getElementById('periodCustom');
                if (customRadio && !customRadio.checked) {
                    customRadio.checked = true;
                    this.handlePeriodChange('custom');
                }

                // Pokaż/ukryj input date
                this.toggleDateInput('start');
            });
        }

        if (endDateBtn && endDateInput) {
            endDateBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('📅 Kliknięto przycisk "do"');

                // Upewnij się, że radio "custom" jest zaznaczone
                const customRadio = document.getElementById('periodCustom');
                if (customRadio && !customRadio.checked) {
                    customRadio.checked = true;
                    this.handlePeriodChange('custom');
                }

                // Pokaż/ukryj input date
                this.toggleDateInput('end');
            });
        }

        // Event listenery dla input date
        if (startDateInput) {
            startDateInput.addEventListener('change', (e) => {
                console.log('📅 Zmieniono datę start:', e.target.value);
                this.handleCustomDateChange('start', e.target.value);
            });

            // Ukryj input po utracie focusa
            startDateInput.addEventListener('blur', () => {
                setTimeout(() => this.hideDateInput('start'), 200);
            });
        }

        if (endDateInput) {
            endDateInput.addEventListener('change', (e) => {
                console.log('📅 Zmieniono datę end:', e.target.value);
                this.handleCustomDateChange('end', e.target.value);
            });

            // Ukryj input po utracie focusa
            endDateInput.addEventListener('blur', () => {
                setTimeout(() => this.hideDateInput('end'), 200);
            });
        }
    }

    toggleDateInput(type) {
        const inputElement = type === 'start' ?
            document.getElementById('startDateInput') :
            document.getElementById('endDateInput');

        const displayElement = type === 'start' ?
            document.getElementById('startDateDisplay') :
            document.getElementById('endDateDisplay');

        if (!inputElement || !displayElement) {
            console.error('❌ Brak elementów dla:', type);
            return;
        }

        // Pokaż input, ukryj display
        inputElement.style.display = 'inline-block';
        inputElement.style.position = 'static';
        inputElement.style.width = '120px';
        inputElement.style.padding = '8px 12px';
        inputElement.style.border = '1px solid #ced4da';
        inputElement.style.borderRadius = '4px';
        inputElement.style.fontSize = '14px';

        displayElement.style.display = 'none';

        // Ustaw wartość domyślną jeśli nie ma
        if (!inputElement.value) {
            const today = new Date();
            inputElement.value = today.toISOString().split('T')[0];
        }

        // Focus na input
        setTimeout(() => {
            inputElement.focus();
            inputElement.showPicker?.(); // Spróbuj otworzyć picker jeśli dostępne
        }, 50);

        console.log('📅 Pokazano input date dla:', type);
    }

    hideDateInput(type) {
        const inputElement = type === 'start' ?
            document.getElementById('startDateInput') :
            document.getElementById('endDateInput');

        const displayElement = type === 'start' ?
            document.getElementById('startDateDisplay') :
            document.getElementById('endDateDisplay');

        if (!inputElement || !displayElement) return;

        // Ukryj input, pokaż display
        inputElement.style.display = 'none';
        displayElement.style.display = 'block';

        console.log('📅 Ukryto input date dla:', type);
    }

    handlePeriodChange(periodType) {
        console.log('📊 Zmiana okresu na:', periodType);
        this.currentPeriod = periodType;

        // Show/hide custom controls
        const customControls = document.getElementById('customPeriodControls');
        if (customControls) {
            if (periodType === 'custom') {
                customControls.classList.add('active');
                console.log('👁️ Pokazano kontrole niestandardowe');
            } else {
                customControls.classList.remove('active');
                console.log('👁️ Ukryto kontrole niestandardowe');
                // Ukryj też otwarte inputy
                this.hideDateInput('start');
                this.hideDateInput('end');
            }
        }

        // Calculate dates based on period type
        this.calculatePeriodDates(periodType);
        this.updatePeriodDisplay();
    }

    handleCustomDateChange(dateType, dateValue) {
        console.log(`📅 Zmiana daty ${dateType}:`, dateValue);

        if (dateType === 'start') {
            // ✅ POPRAWIONE: Utworz obiekt Date z prawidłowego formatu input[type="date"]
            this.startDate = dateValue ? new Date(dateValue + 'T00:00:00') : null;
            const display = document.getElementById('startDateDisplay');
            if (display) {
                if (dateValue) {
                    display.textContent = this.formatDate(new Date(dateValue + 'T00:00:00'));
                    display.classList.add('has-date');
                } else {
                    display.textContent = 'wybierz datę';
                    display.classList.remove('has-date');
                }
            }
        } else if (dateType === 'end') {
            // ✅ POPRAWIONE: Utworz obiekt Date z prawidłowego formatu input[type="date"]
            this.endDate = dateValue ? new Date(dateValue + 'T23:59:59') : null;
            const display = document.getElementById('endDateDisplay');
            if (display) {
                if (dateValue) {
                    display.textContent = this.formatDate(new Date(dateValue + 'T23:59:59'));
                    display.classList.add('has-date');
                } else {
                    display.textContent = 'wybierz datę';
                    display.classList.remove('has-date');
                }
            }
        }

        this.updatePeriodDisplay();

        // Ukryj input po zmianie
        setTimeout(() => this.hideDateInput(dateType), 100);
    }

    calculatePeriodDates(periodType) {
        const now = new Date();

        switch (periodType) {
            case 'current_month':
                this.startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                this.endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                break;

            case 'previous_month':
                this.startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                this.endDate = new Date(now.getFullYear(), now.getMonth(), 0);
                break;

            case 'current_year':
                this.startDate = new Date(now.getFullYear(), 0, 1);
                this.endDate = new Date(now.getFullYear(), 11, 31);
                break;

            case 'previous_year':
                this.startDate = new Date(now.getFullYear() - 1, 0, 1);
                this.endDate = new Date(now.getFullYear() - 1, 11, 31);
                break;

            case 'custom':
                // Dates are set by user selection
                break;
        }
    }

    updatePeriodDisplay() {
        const display = document.getElementById('currentPeriodDisplay');
        if (!display) return;

        let displayText = '';
        const periodNames = {
            'current_month': 'Bieżący miesiąc',
            'previous_month': 'Poprzedni miesiąc',
            'current_year': 'Bieżący rok',
            'previous_year': 'Poprzedni rok',
            'custom': 'Okres niestandardowy'
        };

        if (this.currentPeriod && periodNames[this.currentPeriod]) {
            displayText = periodNames[this.currentPeriod];

            if (this.startDate && this.endDate) {
                displayText += ` (${this.formatDate(this.startDate)} - ${this.formatDate(this.endDate)})`;
                display.classList.add('selected');
            } else if (this.currentPeriod === 'custom') {
                displayText = 'Wybierz daty';
                display.classList.remove('selected');
            } else {
                display.classList.add('selected');
            }
        } else {
            displayText = 'Wybierz okres';
            display.classList.remove('selected');
        }

        display.textContent = displayText;
    }

    setDefaultPeriod() {
        // Set default to current month
        const currentMonthRadio = document.getElementById('periodCurrentMonth');
        if (currentMonthRadio) {
            currentMonthRadio.checked = true;
            this.handlePeriodChange('current_month');
        }
    }

    formatDate(date) {
        return date.toLocaleDateString('pl-PL');
    }

    // ✅ KLUCZOWA POPRAWKA: Właściwy format daty dla API
    formatDateForAPI(date) {
        if (!date) return null;

        // Upewnij się, że to obiekt Date
        const dateObj = date instanceof Date ? date : new Date(date);

        // Sprawdź czy data jest prawidłowa
        if (isNaN(dateObj.getTime())) {
            console.error('❌ Nieprawidłowa data:', date);
            return null;
        }

        // Zwróć w formacie YYYY-MM-DD
        const year = dateObj.getFullYear();
        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
        const day = String(dateObj.getDate()).padStart(2, '0');

        const formatted = `${year}-${month}-${day}`;
        console.log('📅 Sformatowana data dla API:', formatted);

        return formatted;
    }

    getCurrentPeriod() {
        const result = {
            type: this.currentPeriod,
            startDate: this.startDate,
            endDate: this.endDate,
            startDateFormatted: this.formatDateForAPI(this.startDate),
            endDateFormatted: this.formatDateForAPI(this.endDate)
        };

        console.log('📊 getCurrentPeriod wynik:', result);
        return result;
    }

    isValidPeriod() {
        return this.startDate && this.endDate && this.startDate <= this.endDate;
    }
}