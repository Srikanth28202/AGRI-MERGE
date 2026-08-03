import React from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  CheckCircle2, 
  AlertCircle, 
  TrendingUp, 
  Leaf, 
  Sprout,
  Droplets,
  Thermometer,
  Wind,
  Info,
  ChevronRight,
  Award,
  MapPin,
  Calendar,
  Sparkles,
  Target,
  Beaker,
  Gauge,
  ThumbsUp,
  ThumbsDown,
  Lightbulb,
  BarChart3
} from 'lucide-react'
import CropComparison from './CropComparison'
import PriceChart from './PriceChart'
import ProfitCalculator from './ProfitCalculator'
import { useTranslateBackend } from '../utils/resultsTranslations'

const factorMeta = {
  nitrogen: { label: 'results.nitrogen', icon: 'Beaker', color: 'bg-green-500' },
  phosphorous: { label: 'results.phosphorus', icon: 'Beaker', color: 'bg-blue-500' },
  potassium: { label: 'results.potassium', icon: 'Beaker', color: 'bg-orange-500' },
  ph: { label: 'predictionForm.soil.phLevel', icon: 'Beaker', color: 'bg-purple-500' },
  temperature: { label: 'results.temperature', icon: 'Thermometer', color: 'bg-red-500' },
  rainfall: { label: 'results.rainfall', icon: 'Droplets', color: 'bg-cyan-500' },
}

const getScoreColor = (score) => {
  if (score >= 70) return 'text-green-600 bg-green-50 border-green-200'
  if (score >= 50) return 'text-amber-600 bg-amber-50 border-amber-200'
  return 'text-orange-600 bg-orange-50 border-orange-200'
}

const getBarColor = (score) => {
  if (score >= 70) return 'bg-gradient-to-r from-green-400 to-green-500'
  if (score >= 50) return 'bg-gradient-to-r from-amber-400 to-amber-500'
  return 'bg-gradient-to-r from-orange-400 to-orange-500'
}

// Crop icon mapping
const getCropIcon = (crop) => {
  const icons = {
    'wheat': '🌾',
    'rice': '🍚',
    'maize': '🌽',
    'cotton': '🧶',
    'groundnut': '🥜',
    'sugarcane': '🎋',
    'gram': '🫘',
    'moong': '🌱',
    'bajra': '🌾',
    'jute': '🧵',
    'ragi': '🌾',
    'default': '🌱'
  }
  return icons[crop?.toLowerCase()] || icons.default
}

// Confidence color helper
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.7) return 'text-green-600 bg-green-50 border-green-200'
  if (confidence >= 0.5) return 'text-amber-600 bg-amber-50 border-amber-200'
  return 'text-orange-600 bg-orange-50 border-orange-200'
}

// Tag color helper
const getTagColor = (rank) => {
  if (rank === 0) return 'bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg shadow-green-500/30'
  if (rank <= 2) return 'bg-blue-50 text-blue-700 border-blue-200'
  return 'bg-gray-50 text-gray-600 border-gray-200'
}

export default function Results({ results, error, loading }) {
  const { t } = useTranslation()
  const { tSoilCategory, tSoilSummary, tGrowthStage, tXaiRecommendation, tExplanation, tCropName } = useTranslateBackend()
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100 p-8 flex flex-col items-center justify-center min-h-[400px]"
      >
        <div className="relative mb-6">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="absolute -top-1 -right-1"
          >
            <Sparkles className="w-5 h-5 text-amber-500" />
          </motion.div>
        </div>
        <h3 className="text-xl font-bold text-gray-800 mb-2">{t('results.analyzingTitle')}</h3>
        <p className="text-gray-500 text-center max-w-xs">
          {t('results.analyzingSub')}
        </p>
      </motion.div>
    )
  }

  if (error) {
    const errorMessage = typeof error === 'string' ? error : error?.message || t('results.defaultError')
    
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-3xl shadow-xl shadow-gray-200/50 border border-red-100 p-8"
      >
        <div className="flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-2">{t('results.predictionFailed')}</h3>
          <p className="text-gray-600">{errorMessage}</p>
        </div>
      </motion.div>
    )
  }

  if (!results) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100 p-8 flex flex-col items-center justify-center min-h-[400px] text-center"
      >
        <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl mb-4">
          <Leaf className="w-12 h-12 text-green-500" />
        </div>
        <h3 className="text-xl font-bold text-gray-800 mb-2">{t('results.readyTitle')}</h3>
        <p className="text-gray-500 max-w-xs">
          {t('results.readySub')}
        </p>
      </motion.div>
    )
  }

  const { recommended_crop, confidence, predicted_price, price_available, explanation, soil_analysis, growth_advice, details, xai_breakdown, price_history } = results
  const top5 = details?.top_5_recommendations || []
  const recommendedShap = top5[0]?.price_shap || null

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="text-center mb-2">
        <h3 className="text-2xl font-bold text-gray-800">
          {t('results.intelligenceTitle')} <span className="bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">{t('results.intelligenceHighlight')}</span>
        </h3>
        <p className="text-gray-500 mt-1">{t('results.intelligenceSub')}</p>
      </div>

      {/* Top 5 Crops Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {top5.map((crop, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            className={`relative bg-white rounded-2xl p-5 shadow-lg shadow-gray-200/50 border-2 transition-all duration-300 cursor-pointer ${
              index === 0 
                ? 'border-green-500 shadow-green-500/20' 
                : 'border-gray-100 hover:border-green-200'
            }`}
          >
            {/* Rank Badge */}
            <div className={`absolute -top-3 -right-3 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shadow-lg ${
              index === 0 
                ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white' 
                : 'bg-white text-gray-500 border border-gray-200'
            }`}>
              #{index + 1}
            </div>

            {/* Crop Icon & Name */}
            <div className="flex items-center gap-4 mb-4">
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl ${
                index === 0 ? 'bg-green-100' : 'bg-gray-100'
              }`}>
                {getCropIcon(crop.crop)}
              </div>
              <div>
                <h4 className="text-lg font-bold text-gray-800">{tCropName(crop.crop)}</h4>
                <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${getTagColor(index)}`}>
                  {index === 0 && <Award className="w-3 h-3" />}
                  <span>{t(index === 0 ? 'results.bestChoice' : index <= 2 ? 'results.alternative' : 'results.option')}</span>
                </div>
              </div>
            </div>

            {/* Confidence Bar */}
            <div className="mb-3">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-gray-500">{t('results.confidence')}</span>
                <span className="text-sm font-semibold text-gray-700">{Math.round(crop.confidence * 100)}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${crop.confidence * 100}%` }}
                  transition={{ duration: 0.8, delay: index * 0.1 }}
                  className={`h-full rounded-full ${
                    index === 0 
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500' 
                      : 'bg-gradient-to-r from-gray-300 to-gray-400'
                  }`}
                />
              </div>
            </div>

            {/* Price */}
            {crop.price_available && crop.predicted_price && (
              <div className="flex items-center gap-2 mt-1">
                <TrendingUp className={`w-4 h-4 ${index === 0 ? 'text-green-500' : 'text-gray-400'}`} />
                <span className="text-sm text-gray-600">{t('results.expectedPrice')}</span>
                <span className="text-sm font-bold text-gray-800">₹{crop.predicted_price.toLocaleString()}{t('units.perQuintal')}</span>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Why This Crop Section */}
      {explanation && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-100 rounded-xl">
              <Sparkles className="w-5 h-5 text-blue-600" />
            </div>
            <h4 className="font-bold text-gray-800">{t('results.whyTitle')} {tCropName(recommended_crop)}?</h4>
          </div>
          <div className="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
            {tExplanation(explanation)}
          </div>
        </motion.div>
      )}

      {/* Price Trend + SHAP */}
      {price_history && (
        <PriceChart
          history={price_history}
          shap={recommendedShap}
          cropName={tCropName(recommended_crop)}
        />
      )}

      {/* Profit Calculator */}
      <ProfitCalculator
        crop={recommended_crop}
        price={predicted_price}
        priceAvailable={price_available}
      />

      {/* XAI Breakdown */}
      {xai_breakdown && (() => {
        const { factor_scores, category_scores, overall_match, strengths, weaknesses, recommendations } = xai_breakdown
        const factorEntries = factor_scores ? Object.entries(factor_scores) : []
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="bg-white rounded-2xl p-6 shadow-lg shadow-gray-200/50 border border-gray-100"
          >
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2 bg-indigo-100 rounded-xl">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
              </div>
              <h4 className="font-bold text-gray-800">{t('xai.breakdownTitle')}</h4>
            </div>

            {/* Overall Match Ring */}
            {overall_match != null && (
              <div className="flex flex-col items-center mb-6">
                <div className="relative w-24 h-24 mb-2">
                  <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#e5e7eb" strokeWidth="8" />
                    <circle cx="50" cy="50" r="42" fill="none"
                      stroke="url(#grad)" strokeWidth="8" strokeDasharray={`${overall_match * 2.64} 264`}
                      strokeLinecap="round" />
                    <defs>
                      <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#22c55e" />
                        <stop offset="100%" stopColor="#16a34a" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-gray-800">{overall_match}<span className="text-sm">%</span></span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 font-medium">{t('xai.overallMatch')} {tCropName(recommended_crop)}</p>
              </div>
            )}

            {/* Category Scores */}
            {category_scores && (
              <div className="grid grid-cols-3 gap-3 mb-5">
                {[
                  { key: 'soil', label: t('xai.soilHealth'), score: category_scores.soil?.score },
                  { key: 'climate', label: t('xai.climateSuitability'), score: category_scores.climate?.score },
                  { key: 'location_overall', label: t('xai.overallFit'), score: category_scores.location_overall },
                ].map(cat => (
                  <div key={cat.key} className={`rounded-xl p-3 text-center border ${getScoreColor(cat.score || 0)}`}>
                    <p className="text-xs font-medium mb-1">{cat.label}</p>
                    <p className="text-lg font-bold">{cat.score != null ? cat.score : '-'}%</p>
                  </div>
                ))}
              </div>
            )}

            {/* Per-Factor Bars */}
            {factorEntries.length > 0 && (
              <div className="mb-5">
                <p className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <Gauge className="w-4 h-4" /> {t('xai.factorContribution')}
                </p>
                <div className="space-y-2.5">
                  {factorEntries.map(([key, val]) => {
                    const meta = factorMeta[key] || { label: key, color: 'bg-gray-500' }
                    return (
                      <div key={key}>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-gray-600 font-medium">{t(meta.label)}</span>
                          <span className={`font-semibold ${val >= 70 ? 'text-green-600' : val >= 50 ? 'text-amber-600' : 'text-orange-600'}`}>
                            {val}%
                          </span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${val}%` }}
                            transition={{ duration: 0.6, delay: 0.4 }}
                            className={`h-full rounded-full ${getBarColor(val)}`}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Strengths & Weaknesses */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              {strengths && strengths.length > 0 && (
                <div className="p-3 bg-green-50 rounded-xl border border-green-100">
                  <div className="flex items-center gap-1.5 mb-2">
                    <ThumbsUp className="w-3.5 h-3.5 text-green-600" />
                    <p className="text-xs font-semibold text-green-700">{t('xai.strengths')}</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {strengths.map(s => {
                      const meta = factorMeta[s] || { label: s }
                      return (
                        <span key={s} className="text-xs bg-white text-green-700 px-2 py-0.5 rounded-full border border-green-200">
                          {t(meta.label)}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}
              {weaknesses && weaknesses.length > 0 && (
                <div className="p-3 bg-orange-50 rounded-xl border border-orange-100">
                  <div className="flex items-center gap-1.5 mb-2">
                    <ThumbsDown className="w-3.5 h-3.5 text-orange-600" />
                    <p className="text-xs font-semibold text-orange-700">{t('xai.needsImprovement')}</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {weaknesses.map(s => {
                      const meta = factorMeta[s] || { label: s }
                      return (
                        <span key={s} className="text-xs bg-white text-orange-700 px-2 py-0.5 rounded-full border border-orange-200">
                          {t(meta.label)}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Recommendations */}
            {recommendations && recommendations.length > 0 && (
              <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                <div className="flex items-center gap-1.5 mb-2">
                  <Lightbulb className="w-4 h-4 text-blue-600" />
                  <p className="text-xs font-semibold text-blue-700">{t('xai.recommendations')}</p>
                </div>
                <ul className="space-y-1.5">
                  {recommendations.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-blue-800">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                      {tXaiRecommendation(r)}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )
      })()}

      {/* Soil Analysis */}
      {soil_analysis && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-2xl p-6 shadow-lg shadow-gray-200/50 border border-gray-100"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-green-100 rounded-xl">
              <Target className="w-5 h-5 text-green-600" />
            </div>
            <h4 className="font-bold text-gray-800">{t('results.soilAnalysis')}</h4>
          </div>
          
          <div className="grid grid-cols-2 gap-3 mb-4">
            {Object.entries(soil_analysis).filter(([key]) => key !== 'summary').map(([key, value]) => (
              <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                <span className="text-sm text-gray-600 capitalize">{key}</span>
                <span className="text-sm font-semibold text-gray-800">{tSoilCategory(value)}</span>
              </div>
            ))}
          </div>
          
          {soil_analysis.summary?.length > 0 && (
            <div className="p-3 bg-green-50 rounded-xl border border-green-100 space-y-1">
              {soil_analysis.summary.map((item, i) => (
                <p key={i} className="text-sm text-green-800">{tSoilSummary(item)}</p>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Growth Guide */}
      {growth_advice?.stages && growth_advice.stages.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-2xl p-6 shadow-lg shadow-gray-200/50 border border-gray-100"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-amber-100 rounded-xl">
              <Sprout className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h4 className="font-bold text-gray-800">{t('results.growthGuide')}</h4>
              <p className="text-xs text-gray-500">{t('results.duration')} {growth_advice.duration}</p>
            </div>
          </div>
          
          {/* Fertilizer Requirements */}
          {growth_advice?.fertilizers && (
            <div className="mb-5 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-100">
              <div className="flex items-center gap-2 mb-3">
                <Beaker className="w-4 h-4 text-green-600" />
                <h5 className="font-semibold text-gray-800 text-sm">{t('results.fertilizerRequirements')}</h5>
              </div>
              
              {/* NPK Values */}
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="bg-white rounded-lg p-2 text-center border border-green-100">
                  <p className="text-xs text-gray-500">{t('results.nitrogen')}</p>
                  <p className="font-bold text-green-700">{growth_advice.fertilizers.npk?.N || 60}{t('units.kgPerAcre')}</p>
                </div>
                <div className="bg-white rounded-lg p-2 text-center border border-green-100">
                  <p className="text-xs text-gray-500">{t('results.phosphorus')}</p>
                  <p className="font-bold text-blue-700">{growth_advice.fertilizers.npk?.P || 30}{t('units.kgPerAcre')}</p>
                </div>
                <div className="bg-white rounded-lg p-2 text-center border border-green-100">
                  <p className="text-xs text-gray-500">{t('results.potassium')}</p>
                  <p className="font-bold text-orange-700">{growth_advice.fertilizers.npk?.K || 30}{t('units.kgPerAcre')}</p>
                </div>
              </div>
              
              {/* Recommended Fertilizers */}
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-gray-600">{t('results.recommended')}</p>
                {growth_advice.fertilizers.fertilizers?.map((fert, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs text-gray-700 bg-white/70 px-2 py-1.5 rounded">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                    {fert}
                  </div>
                ))}
              </div>
              
              {/* Organic Option */}
              {growth_advice.fertilizers.organic && (
                <div className="mt-3 pt-3 border-t border-green-200">
                  <p className="text-xs font-medium text-green-700 flex items-center gap-1">
                    <Leaf className="w-3 h-3" />
                    {t('results.organic')} {growth_advice.fertilizers.organic}
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="space-y-3">
            {growth_advice.stages.map((stage, index) => (
              <div key={index} className="flex gap-4 p-3 bg-gray-50 rounded-xl">
                <div className="flex-shrink-0 w-16 text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-lg text-center">
                  {stage.week}
                </div>
                <div>
                  <h5 className="font-semibold text-gray-800 text-sm">{tGrowthStage(stage.stage)}</h5>
                  <p className="text-xs text-gray-600 mt-0.5">{stage.action}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Environmental Data */}
      {details?.environmental_data && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="grid grid-cols-3 gap-3"
        >
          <div className="bg-orange-50 rounded-xl p-4 text-center border border-orange-100">
            <Thermometer className="w-5 h-5 text-orange-500 mx-auto mb-2" />
            <p className="text-xs text-gray-500 mb-1">{t('results.temperature')}</p>
            <p className="font-bold text-gray-800">{details.environmental_data.temperature_celsius}{t('units.celsius')}</p>
          </div>
          <div className="bg-blue-50 rounded-xl p-4 text-center border border-blue-100">
            <Droplets className="w-5 h-5 text-blue-500 mx-auto mb-2" />
            <p className="text-xs text-gray-500 mb-1">{t('results.humidity')}</p>
            <p className="font-bold text-gray-800">{details.environmental_data.humidity_percent}%</p>
          </div>
          <div className="bg-cyan-50 rounded-xl p-4 text-center border border-cyan-100">
            <Wind className="w-5 h-5 text-cyan-500 mx-auto mb-2" />
            <p className="text-xs text-gray-500 mb-1">{t('results.rainfall')}</p>
            <p className="font-bold text-gray-800">{details.environmental_data.rainfall_mm}{t('units.millimeters')}</p>
          </div>
        </motion.div>
      )}

      {/* Manual Crop Comparison */}
      <CropComparison 
        inputFeatures={details?.input_features}
        environmentalData={details?.environmental_data}
        topCrops={top5}
      />
    </motion.div>
  )
}
