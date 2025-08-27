// System logowania
class Logger {
    constructor() {
        this.logEntries = document.getElementById('logEntries');
    }

    addEntry(message, type = 'info') {
        if (!this.logEntries) return;

        const entry = document.createElement('div');
        entry.className = `log-entry log-${type}`;
        entry.innerHTML = `
            <span class="log-time">${new Date().toLocaleTimeString()}</span>
            <span class="log-message">${message}</span>
        `;
        this.logEntries.appendChild(entry);
        this.logEntries.scrollTop = this.logEntries.scrollHeight;
    }

    clear() {
        if (this.logEntries) {
            this.logEntries.innerHTML = '';
        }
    }
}

export const logger = new Logger();