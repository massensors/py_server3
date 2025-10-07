//Konfiguracja aplikacji
// export const CONFIG = {
//     API_URL: 'http://localhost:8080',
//     REFRESH_INTERVAL: 2000,
//     MAX_LOG_ENTRIES: 100,
//     SYSTEM_ID: 1126326593
// };

// Konfiguracja API
export const API_URL = '';  // Puste dla relatywnych URLi


// Mapowanie parametrów
export const PARAMETER_MAPPING = {
   // 0: {name: "dummy", label: "Dummy", format: "1B"},
    1: {name: "filterRate", label: "Filter Rate", format: "1B"},
    2: {name: "scaleCapacity", label: "Scale Capacity", format: "8B"},
    // ... pozostałe parametry
    3: {name: "autoZero", label: "Auto Zero", format: "8B"},
    4: {name: "deadBand", label: "Dead Band", format: "8B"},
    5: {name: "scaleType", label: "Scale Type", format: "1B"},
    6: {name: "loadcellSet", label: "Load Cell Set", format: "1B"},
    7: {name: "loadcellCapacity", label: "Load Cell Capacity", format: "8B"},
    8: {name: "trimm", label: "Trimm", format: "8B"},
    9: {name: "idlerSpacing", label: "Idler Spacing", format: "8B"},
    10: {name: "speedSource", label: "Speed Source", format: "1B"},
    11: {name: "wheelDiameter", label: "Wheel Diameter", format: "8B"},
    12: {name: "pulsesPerRev", label: "Pulses Per Rev", format: "8B"},
    13: {name: "beltLength", label: "Belt Length", format: "8B"},
    14: {name: "beltLengthPulses", label: "Belt Length Pulses", format: "8B"},
   // 15: {name: "currentTime", label: "Current Time", format: "19B"}
};




// Mapowanie aliasów
export const ALIAS_FIELDS = [
    {name: "company", label: "Firma"},
    {name: "location", label: "Lokalizacja"},
    {name: "productName", label: "Nazwa produktu"},
    {name: "scaleId", label: "ID wagi"}
];

export const ALIAS_ADDRESS_MAPPING = {
    'company': 16,
    'location': 17,
    'productName': 18,
    'scaleId': 19
};