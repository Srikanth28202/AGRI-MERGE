import React from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowLeft, Search, Leaf } from 'lucide-react'
import Results from '../components/Results'

export default function ResultsPage({ results, error, loading }) {
  const { t } = useTranslation()

  return (
    <section className="py-20 lg:py-28 section-padding min-h-screen">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-sm font-medium rounded-full w-fit">
            <Leaf className="w-4 h-4" />
            {t('app.aiPrediction')}
          </span>
          <Link
            to="/predict"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-white dark:bg-neutral-800 border border-gray-200 text-sm font-semibold text-gray-700 dark:text-gray-200 rounded-xl shadow-sm hover:bg-gray-50 hover:border-gray-300 transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            {t('navbar.predict')}
          </Link>
        </motion.div>

        {!results && !error && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-neutral-800 rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100 p-12 flex flex-col items-center justify-center text-center min-h-[360px]"
          >
            <div className="p-5 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-2xl mb-6">
              <Leaf className="w-14 h-14 text-green-500" />
            </div>
            <h3 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">{t('results.readyTitle')}</h3>
            <p className="text-gray-500 dark:text-gray-400 max-w-sm mb-8">
              {t('results.readySub')}
            </p>
            <Link
              to="/predict"
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-semibold rounded-xl shadow-lg shadow-green-500/30 hover:shadow-xl hover:shadow-green-500/40 transition-all"
            >
              <Search className="w-5 h-5" />
              {t('predictionForm.submit.getRecommendation')}
            </Link>
          </motion.div>
        )}

        {(results || error || loading) && (
          <Results results={results} error={error} loading={loading} />
        )}
      </div>
    </section>
  )
}
