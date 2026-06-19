/** @odoo-module **/

function formatAmount(value, symbol) {
    const amount = Number(value || 0);
    return `${Math.round(amount).toLocaleString('fr-FR')} ${symbol || 'Ar'}`;
}

function parseAmount(value) {
    const normalized = String(value || '')
        .replace(/[^\d,.-]/g, '')
        .replace(',', '.');
    return Number(normalized || 0);
}

function formatNumberInput(value, symbol) {
    const amount = Math.max(parseAmount(value), 0);
    return `${Math.round(amount).toLocaleString('fr-FR')} ${symbol || 'Ar'}`;
}

function parseBanks(card) {
    if (card.dataset.banksB64) {
        try {
            const json = decodeURIComponent(
                Array.prototype.map.call(atob(card.dataset.banksB64), (char) =>
                    `%${char.charCodeAt(0).toString(16).padStart(2, '0')}`
                ).join('')
            );
            return JSON.parse(json || '[]');
        } catch (error) {
            // Fall back to the plain JSON attribute below.
        }
    }
    try {
        return JSON.parse(card.dataset.banks || '[]');
    } catch (error) {
        return [];
    }
}

function calculate(card) {
    const priceMGA = Number(card.dataset.priceMga || 0);
    const mgaSymbol = card.dataset.mgaSymbol || 'Ar';
    const downType = card.querySelector('.js-loan-down-type').value;
    const downValue = parseAmount(card.querySelector('.js-loan-down-value').value);
    const durationYears = Math.max(Number(card.querySelector('.js-loan-duration').value || 0), 1);
    const interestRate = Math.max(Number(card.querySelector('.js-loan-interest').value || 0), 0);

    let downAmount = downType === 'percent' ? priceMGA * downValue / 100 : downValue;
    downAmount = Math.min(Math.max(downAmount, 0), priceMGA);

    const principal = Math.max(priceMGA - downAmount, 0);
    const months = durationYears * 12;
    const monthlyRate = interestRate / 100 / 12;
    let monthly = 0;

    if (principal > 0) {
        if (monthlyRate === 0) {
            monthly = principal / months;
        } else {
            monthly = principal * monthlyRate / (1 - Math.pow(1 + monthlyRate, -months));
        }
    }

    const totalCredit = monthly * months;
    const totalInterest = Math.max(totalCredit - principal, 0);
    const grand = principal + totalInterest;
    const capitalPercent = grand ? Math.round((principal / grand) * 100) : 100;
    const interestPercent = Math.max(100 - capitalPercent, 0);

    card.querySelector('.js-loan-down-amount').textContent = `Montant apport : ${formatAmount(downAmount, mgaSymbol)}`;
    card.querySelector('.js-loan-monthly').textContent = `${formatAmount(monthly, mgaSymbol)} / mois`;
    card.querySelector('.js-loan-principal').textContent = formatAmount(principal, mgaSymbol);
    card.querySelector('.js-loan-interest-total').textContent = formatAmount(totalInterest, mgaSymbol);
    card.querySelector('.js-loan-total').textContent = formatAmount(totalCredit, mgaSymbol);
    card.querySelector('.js-loan-capital-bar').style.width = `${capitalPercent}%`;
    card.querySelector('.js-loan-interest-bar').style.width = `${interestPercent}%`;
    card.querySelector('.js-loan-capital-label').textContent = `Capital ${capitalPercent}%`;
    card.querySelector('.js-loan-interest-label').textContent = `Intérêts ${interestPercent}%`;
}

function initCard(card) {
    const banks = parseBanks(card);
    const bankSelect = card.querySelector('.js-loan-bank');
    const price = Number(card.dataset.price || 0);
    const priceMGA = Number(card.dataset.priceMga || 0);
    const currencySymbol = card.dataset.currencySymbol || '';
    const mgaSymbol = card.dataset.mgaSymbol || 'Ar';
    const isMGA = card.dataset.isMga === '1';
    const exchangeRate = Number(card.dataset.exchangeRate || 1);
    const currencyCode = card.dataset.currencyCode || '';

    if (!banks.length) {
        card.classList.add('d-none');
        return;
    }

    card.querySelector('.js-loan-original-price').textContent = formatAmount(price, currencySymbol);
    const mgaPriceNode = card.querySelector('.js-loan-mga-price');
    if (mgaPriceNode) {
        mgaPriceNode.textContent = formatAmount(priceMGA, mgaSymbol);
    }
    const rateLabelNode = card.querySelector('.js-loan-rate-label');
    if (rateLabelNode && !isMGA) {
        rateLabelNode.textContent = `1 ${currencyCode} = ${Math.round(exchangeRate).toLocaleString('fr-FR')} ${mgaSymbol}`;
    }

    bankSelect.innerHTML = '';
    banks.forEach((bank, index) => {
        const option = document.createElement('option');
        option.value = String(index);
        option.textContent = bank.name;
        bankSelect.appendChild(option);
    });

    function applyBank() {
        const bank = banks[Number(bankSelect.value || 0)] || banks[0] || {};
        card.querySelector('.js-loan-interest').value = bank.interest_rate ?? 12;
        card.querySelector('.js-loan-duration').value = bank.duration_years ?? 20;
        card.querySelector('.js-loan-down-type').value = bank.down_payment_type || 'percent';
        setDownPaymentValue(card, bank.down_payment_value ?? 10);
        calculate(card);
    }

    function setDownPaymentValue(card, value) {
        const downInput = card.querySelector('.js-loan-down-value');
        const downType = card.querySelector('.js-loan-down-type').value;
        downInput.value = downType === 'fixed'
            ? formatNumberInput(value, mgaSymbol)
            : String(value ?? 0);
    }

    function syncDownPaymentInput() {
        const downInput = card.querySelector('.js-loan-down-value');
        const downType = card.querySelector('.js-loan-down-type').value;
        if (downType === 'fixed') {
            downInput.value = formatNumberInput(downInput.value, mgaSymbol);
        } else {
            downInput.value = String(parseAmount(downInput.value));
        }
        calculate(card);
    }

    bankSelect.addEventListener('change', applyBank);
    card.querySelector('.js-loan-calculate').addEventListener('click', () => calculate(card));
    card.querySelectorAll('input, select').forEach((input) => {
        input.addEventListener('input', () => calculate(card));
        input.addEventListener('change', () => {
            if (input.classList.contains('js-loan-down-value') || input.classList.contains('js-loan-down-type')) {
                syncDownPaymentInput();
            } else {
                calculate(card);
            }
        });
    });

    applyBank();
}

function initLoanSimulators() {
    document.querySelectorAll('.packimmo-loan-card').forEach(initCard);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLoanSimulators);
} else {
    initLoanSimulators();
}
