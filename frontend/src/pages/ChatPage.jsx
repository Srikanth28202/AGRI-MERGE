import React from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Bot, ArrowLeft, Sparkles } from 'lucide-react'
import Chatbot from '../components/Chatbot'

export default function ChatPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  return (
    <section className="py-20 lg:py-28 section-padding min-h-screen">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-10"
        >
          <motion.button
            whileHover={{ x: -3 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate('/')}
            className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-green-700 transition-colors mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            {t('navbar.home')}
          </motion.button>

          <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-sm font-medium rounded-full mb-4">
            <Sparkles className="w-4 h-4" />
            {t('hero.aiSupport')}
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-neutral-900 dark:text-white mb-4">
            {t('chatbot.headerTitle')}
          </h2>
          <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
            {t('hero.subheadline')}
          </p>
          <div className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-white dark:bg-neutral-800 rounded-full shadow-sm border border-gray-100">
            <Bot className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
              {t('chatbot.welcome').split('\n')[0]}
            </span>
          </div>
        </motion.div>

        <Chatbot fullPage onClose={() => navigate('/')} />
      </div>
    </section>
  )
}
