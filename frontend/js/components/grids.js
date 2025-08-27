import { PARAMETER_MAPPING, ALIAS_FIELDS } from '../config/constants.js';
import { updateParameter, updateAlias } from '../services/api.js';

// Tworzy siatkę parametrów
export function createParametersGrid() {
    const parametersGrid = document.querySelector('.parameters-grid');
    if (!parametersGrid) return;

    parametersGrid.innerHTML = '';

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

        paramItem.querySelector('.update-btn').addEventListener('click', () => {
            const value = paramItem.querySelector('.param-value').value;
            updateParameter(address, value);
        });

        parametersGrid.appendChild(paramItem);
    }
}

// Tworzy siatkę aliasów
export function createAliasyGrid() {
    const aliasyGrid = document.querySelector('.aliasy-grid');
    if (!aliasyGrid) return;

    aliasyGrid.innerHTML = '';

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

        aliasItem.querySelector('.update-btn').addEventListener('click', () => {
            const value = aliasItem.querySelector('.alias-value').value;
            updateAlias(field.name, value);
        });

        aliasyGrid.appendChild(aliasItem);
    }
}