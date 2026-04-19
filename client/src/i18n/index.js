import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { useCallback } from 'react'
import en from './locales/en'
import ru from './locales/ru'
import ka from './locales/ka'

const LOCALES = { en, ru, ka }

export const LANGUAGES = [
  { code: 'en', label: 'EN', name: 'English' },
  { code: 'ru', label: 'RU', name: 'Русский' },
  { code: 'ka', label: 'KA', name: 'ქართული' },
]

export const useLangStore = create(
  persist(
    (set) => ({
      lang: 'en',
      setLang: (lang) => set({ lang }),
    }),
    { name: 'bar-pos-lang' }
  )
)

/** Returns a stable translation function for the current language.
 *  Usage: const t = useT()
 *         t('key')
 *         t('key_with_vars', { name: 'foo', total: '9.99' })
 */
export function useT() {
  const lang = useLangStore((s) => s.lang)
  return useCallback(
    (key, vars) => {
      const locale = LOCALES[lang] ?? LOCALES.en
      let str = locale[key] ?? LOCALES.en[key] ?? key
      if (vars) {
        Object.entries(vars).forEach(([k, v]) => {
          str = str.replaceAll(`{{${k}}}`, v)
        })
      }
      return str
    },
    [lang]
  )
}

/** Returns the BCP-47 locale tag for date/time formatting (e.g. 'ru-RU'). */
export function useDateLocale() {
  const lang = useLangStore((s) => s.lang)
  return (LOCALES[lang] ?? LOCALES.en)._dateLocale
}

/** Pluralise order-item count per-locale rules.
 *  Accepts the raw t function so it can be called inside components. */
export function pluralItems(n, t) {
  if (n === 1) return t('td_items_one')
  if (n >= 2 && n <= 4) return t('td_items_few')
  return t('td_items_many')
}
