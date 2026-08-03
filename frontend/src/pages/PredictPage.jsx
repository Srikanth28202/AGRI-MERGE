import React from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import PredictionForm from '../components/PredictionForm'

export default function PredictPage({ onSubmit, loading, locations }) {
  const { t } = useTranslation()

  return (
    <section className="py-20 lg:py-28 section-padding min-h-screen">
      <div className="max-w-3xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-10"
        >
          <span className="inline-block px-4 py-1.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm font-medium rounded-full mb-4">
            {t('app.aiPrediction')}
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-neutral-900 dark:text-white mb-4">
            {t('app.getYour')} <span className="gradient-text">{t('app.cropRecommendation')}</span>
          </h2>
          <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
            {t('app.enterFarmDetails')}
          </p>
        </motion.div>

        <PredictionForm
          onSubmit={onSubmit}
          loading={loading}
          locations={locations}
        />
      </div>
    </section>
  )
}
