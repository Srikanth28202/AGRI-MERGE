import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { Languages, Check } from 'lucide-react'

const languages = [
  { code: 'en', labelKey: 'languageSwitcher.en' },
  { code: 'hi', labelKey: 'languageSwitcher.hi' },
  { code: 'kn', labelKey: 'languageSwitcher.kn' },
  { code: 'te', labelKey: 'languageSwitcher.te' },
  { code: 'ta', labelKey: 'languageSwitcher.ta' },
  { code: 'ml', labelKey: 'languageSwitcher.ml' },
  { code: 'mr', labelKey: 'languageSwitcher.mr' },
  { code: 'gu', labelKey: 'languageSwitcher.gu' },
  { code: 'bn', labelKey: 'languageSwitcher.bn' },
  { code: 'pa', labelKey: 'languageSwitcher.pa' }
]

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const currentLang = i18n.language

  const changeLanguage = (code) => {
    i18n.changeLanguage(code)
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(!isOpen)}
        className="p-2.5 bg-white/80 backdrop-blur-sm rounded-full shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100"
        title={t('languageSwitcher.' + currentLang) || currentLang}
      >
        <Languages className="w-4 h-4 text-neutral-600" />
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-40 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden z-50"
          >
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => changeLanguage(lang.code)}
                className={`w-full flex items-center justify-between px-4 py-3 text-sm transition-colors ${
                  currentLang === lang.code
                    ? 'bg-green-50 text-green-700 font-semibold'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span>{t(lang.labelKey)}</span>
                {currentLang === lang.code && (
                  <Check className="w-4 h-4 text-green-600" />
                )}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
