const SYMBOLS = {
    RUB: '₽',
    USD: '$',
    EUR: '€',
    GEL: '₾'
}

const code = import.meta.env.VITE_CURRENCY ?? 'RUB'

export const CURRENCY = SYMBOLS[code] ?? code
