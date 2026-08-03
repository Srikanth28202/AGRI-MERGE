import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { Scale, ChevronDown, ChevronUp, Sprout, Droplets, ThermometerSun, DollarSign, Check } from 'lucide-react'

const allCrops = [
  { name: 'wheat', npk: { n: 80, p: 40, k: 40 }, water: 'Medium', temp: '15-25°C', price: 2000, duration: '120 days' },
  { name: 'rice', npk: { n: 100, p: 50, k: 60 }, water: 'High', temp: '20-35°C', price: 3500, duration: '90-150 days' },
  { name: 'maize', npk: { n: 100, p: 50, k: 60 }, water: 'Medium', temp: '20-30°C', price: 1800, duration: '90-110 days' },
  { name: 'cotton', npk: { n: 80, p: 40, k: 40 }, water: 'Medium-High', temp: '25-35°C', price: 5500, duration: '150-180 days' },
  { name: 'groundnut', npk: { n: 30, p: 50, k: 40 }, water: 'Medium', temp: '20-30°C', price: 5000, duration: '90-120 days' },
  { name: 'sugarcane', npk: { n: 120, p: 60, k: 80 }, water: 'High', temp: '25-35°C', price: 3000, duration: '12-18 months' },
  { name: 'gram', npk: { n: 20, p: 40, k: 30 }, water: 'Low', temp: '15-25°C', price: 4500, duration: '90-120 days' },
  { name: 'moong', npk: { n: 20, p: 30, k: 30 }, water: 'Low', temp: '25-35°C', price: 6500, duration: '60-90 days' },
  { name: 'bajra', npk: { n: 40, p: 30, k: 30 }, water: 'Low', temp: '25-35°C', price: 2000, duration: '60-90 days' },
  { name: 'jute', npk: { n: 60, p: 30, k: 40 }, water: 'High', temp: '25-35°C', price: 3500, duration: '120-150 days' },
]

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
    'default': '🌱'
  }
  return icons[crop?.toLowerCase()] || icons.default
}

export default function CropComparison({ inputFeatures, environmentalData, topCrops }) {
  const { t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const [selectedCrops, setSelectedCrops] = useState([])

  const toggleCrop = (cropName) => {
    if (selectedCrops.includes(cropName)) {
      setSelectedCrops(selectedCrops.filter(c => c !== cropName))
    } else if (selectedCrops.length < 3) {
      setSelectedCrops([...selectedCrops, cropName])
    }
  }

  const getSuitabilityScore = (crop) => {
    if (!inputFeatures) return '-'
    
    let score = 0
    const nDiff = Math.abs(crop.npk.n - inputFeatures.nitrogen)
    const pDiff = Math.abs(crop.npk.p - inputFeatures.phosphorous)
    const kDiff = Math.abs(crop.npk.k - inputFeatures.potassium)
    
    score = Math.max(0, 100 - (nDiff + pDiff + kDiff) / 3)
    return Math.round(score)
  }

  const getScoreColor = (score) => {
    if (score === '-') return 'text-gray-400'
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-amber-600'
    return 'text-orange-600'
  }

  const selectedCropData = allCrops.filter(c => selectedCrops.includes(c.name))

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.7 }}
      className="bg-white rounded-2xl shadow-lg shadow-gray-200/50 border border-gray-100 overflow-hidden"
    >
      <div 
        className="flex items-center justify-between p-5 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-amber-100 rounded-xl">
            <Scale className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h4 className="font-bold text-gray-800">{t('cropComparison.title')}</h4>
            <p className="text-xs text-gray-500">{t('cropComparison.subtitle')}</p>
          </div>
        </div>
        <div className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          {isOpen ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-gray-100"
          >
            <div className="p-5 space-y-5">
              {/* Crop Selection */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-3">
                  {t('cropComparison.selectCount')} ({selectedCrops.length}/3):
                </p>
                <div className="flex flex-wrap gap-2">
                  {allCrops.map((crop) => (
                    <motion.button
                      key={crop.name}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleCrop(crop.name)
                      }}
                      className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                        selectedCrops.includes(crop.name)
                          ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-md'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      <span>{getCropIcon(crop.name)}</span>
                      <span>{t('crops.' + crop.name)}</span>
                      {selectedCrops.includes(crop.name) && (
                        <Check className="w-3.5 h-3.5" />
                      )}
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Comparison Table */}
              {selectedCropData.length > 0 && (
                <div className="overflow-x-auto rounded-xl border border-gray-200">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">{t('cropComparison.table.crop')}</th>
                        <th className="text-center py-3 px-4 font-semibold text-gray-700">
                          <div className="flex items-center justify-center gap-1">
                            <Sprout className="w-4 h-4" /> {t('cropComparison.table.npk')}
                          </div>
                        </th>
                        <th className="text-center py-3 px-4 font-semibold text-gray-700">
                          <div className="flex items-center justify-center gap-1">
                            <Droplets className="w-4 h-4" /> {t('cropComparison.table.water')}
                          </div>
                        </th>
                        <th className="text-center py-3 px-4 font-semibold text-gray-700">
                          <div className="flex items-center justify-center gap-1">
                            <ThermometerSun className="w-4 h-4" /> {t('cropComparison.table.temp')}
                          </div>
                        </th>
                        <th className="text-center py-3 px-4 font-semibold text-gray-700">{t('cropComparison.table.duration')}</th>
                        <th className="text-center py-3 px-4 font-semibold text-gray-700">
                          <div className="flex items-center justify-center gap-1">
                            <DollarSign className="w-4 h-4" /> {t('cropComparison.table.price')}
                          </div>
                        </th>
                        <th className="text-center py-3 px-4 font-semibold text-gray-700">{t('cropComparison.table.match')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedCropData.map((crop) => {
                        const score = getSuitabilityScore(crop)
                        return (
                          <tr key={crop.name} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <span className="text-lg">{getCropIcon(crop.name)}</span>
                                <span className="font-semibold text-gray-800">{t('crops.' + crop.name)}</span>
                              </div>
                            </td>
                            <td className="text-center py-3 px-4 text-gray-600">
                              {t('cropComparison.table.nitrogen')}:{crop.npk.n} {t('cropComparison.table.phosphorus')}:{crop.npk.p} {t('cropComparison.table.potassium')}:{crop.npk.k}
                            </td>
                            <td className="text-center py-3 px-4 text-gray-600">{t('crops.waterLevels.' + crop.water.toLowerCase().replace(/-/g, ''))}</td>
                            <td className="text-center py-3 px-4 text-gray-600">{crop.temp}</td>
                            <td className="text-center py-3 px-4 text-gray-600">{crop.duration}</td>
                            <td className="text-center py-3 px-4">
                              <span className="font-semibold text-green-600">₹{crop.price}{t('units.perQuintal')}</span>
                            </td>
                            <td className="text-center py-3 px-4">
                              <span className={`text-lg font-bold ${getScoreColor(score)}`}>
                                {score}%
                              </span>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {selectedCropData.length === 0 && (
                <div className="text-center py-8 text-gray-400 bg-gray-50 rounded-xl">
                  <Scale className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">{t('cropComparison.clickToCompare')}</p>
                </div>
              )}

              {/* Current Conditions Reference */}
              {inputFeatures && (
                <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-100">
                  <h5 className="text-sm font-semibold text-green-800 mb-3 flex items-center gap-2">
                    <Sprout className="w-4 h-4" />
                    {t('cropComparison.yourSoilConditions')}
                  </h5>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div className="bg-white rounded-lg p-2.5">
                      <span className="text-gray-500 block text-xs mb-1">{t('results.nitrogen')}</span>
                      <span className="font-semibold text-gray-800">{inputFeatures.nitrogen}</span>
                    </div>
                    <div className="bg-white rounded-lg p-2.5">
                      <span className="text-gray-500 block text-xs mb-1">{t('predictionForm.soil.phosphorous')}</span>
                      <span className="font-semibold text-gray-800">{inputFeatures.phosphorous}</span>
                    </div>
                    <div className="bg-white rounded-lg p-2.5">
                      <span className="text-gray-500 block text-xs mb-1">{t('results.potassium')}</span>
                      <span className="font-semibold text-gray-800">{inputFeatures.potassium}</span>
                    </div>
                    <div className="bg-white rounded-lg p-2.5">
                      <span className="text-gray-500 block text-xs mb-1">{t('predictionForm.soil.phLevel')}</span>
                      <span className="font-semibold text-gray-800">{inputFeatures.ph}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
