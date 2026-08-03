import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import hi from './locales/hi.json'
import kn from './locales/kn.json'
import te from './locales/te.json'
import ta from './locales/ta.json'
import ml from './locales/ml.json'
import mr from './locales/mr.json'
import gu from './locales/gu.json'
import bn from './locales/bn.json'
import pa from './locales/pa.json'

const savedLang = localStorage.getItem('i18nextLng') || 'en'

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    hi: { translation: hi },
    kn: { translation: kn },
    te: { translation: te },
    ta: { translation: ta },
    ml: { translation: ml },
    mr: { translation: mr },
    gu: { translation: gu },
    bn: { translation: bn },
    pa: { translation: pa }
  },
  lng: savedLang,
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false
  }
})

i18n.on('languageChanged', (lng) => {
  localStorage.setItem('i18nextLng', lng)
  document.documentElement.lang = lng
})

export default i18n
