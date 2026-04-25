# Frontend Internationalisation (i18n)

The frontend supports **English (EN)**, **Russian (RU)**, and **Georgian (KA)** via a lightweight custom i18n layer — no external library.

## Key Files

| File | Purpose |
|------|---------|
| `client/src/i18n/index.js` | Core: `useLangStore`, `useT()`, `useDateLocale()`, `pluralItems()` |
| `client/src/i18n/locales/en.js` | English strings (flat key → string map) |
| `client/src/i18n/locales/ru.js` | Russian strings |
| `client/src/i18n/locales/ka.js` | Georgian strings |

## Language Store

`useLangStore` is a Zustand store that persists the selected language to `localStorage` under the key `bar-pos-lang`. Default language: **English**.

The language switcher is shown on the Login screen and in the sidebar bottom section.

## `useT()` Hook

Returns a memoized `t(key, vars?)` function for looking up translation strings.

```js
const t = useT();
t('table.close')           // → "Close Table"
t('order.added', { item: 'Beer', qty: 2 })  // → "Added Beer ×2"
```

Variable substitution uses `{{name}}` syntax in locale strings.

## `useDateLocale()` Hook

Returns the BCP-47 locale tag for the currently selected language, for use with `toLocaleString()`.

| Language | Tag |
|----------|-----|
| EN | `en-US` |
| RU | `ru-RU` |
| KA | `ka-GE` |

## `pluralItems()` Helper

Handles plural forms for item counts (relevant for Russian/Georgian which have more complex plural rules than English).

## Adding a New Locale

1. Create `client/src/i18n/locales/<code>.js` with a flat key→string map mirroring `en.js`.
2. Register the new locale in `client/src/i18n/index.js` (import + add to the locale map and the language switcher options).
