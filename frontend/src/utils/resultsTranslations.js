import { useTranslation } from 'react-i18next'

const soilCategoryMap = {
  'High': 'soilCategories.high',
  'Medium': 'soilCategories.medium',
  'Low': 'soilCategories.low',
  'Acidic': 'soilCategories.acidic',
  'Neutral-Slightly Acidic': 'soilCategories.neutralSlightlyAcidic',
  'Neutral': 'soilCategories.neutral',
  'Alkaline': 'soilCategories.alkaline',
}

const soilSummaryMap = {
  '✅ Your soil has good nitrogen for leafy crops': 'soilSummaries.nitrogenHigh',
  '⚠️ Nitrogen is low - add organic manure or urea': 'soilSummaries.nitrogenLow',
  '🧪 Soil is slightly acidic - good for rice, potato, coffee': 'soilSummaries.phAcidic',
  '🧪 Soil is alkaline - add gypsum if needed': 'soilSummaries.phAlkaline',
}

const recomFactorMap = {
  'nitrogen': 'xaiFactors.nitrogen',
  'phosphorous': 'xaiFactors.phosphorous',
  'potassium': 'xaiFactors.potassium',
  'ph': 'xaiFactors.ph',
  'temperature': 'xaiFactors.temperature',
  'rainfall': 'xaiFactors.rainfall',
}

const recomAdviceMap = {
  'Add nitrogen-rich fertilizer like Urea or compost': 'xaiAdvice.nitrogen',
  'Apply DAP, SSP, or bone meal': 'xaiAdvice.phosphorous',
  'Add MOP (Muriate of Potash) or wood ash': 'xaiAdvice.potassium',
  'Use lime to raise pH or sulfur/gypsum to lower it': 'xaiAdvice.ph',
  'Adjust planting time or use shade nets': 'xaiAdvice.temperature',
  'Plan irrigation schedule or install drainage': 'xaiAdvice.rainfall',
}

export function useTranslateBackend() {
  const { t } = useTranslation()

  const tSoilCategory = (val) => {
    const key = soilCategoryMap[val]
    return key ? t(key) : val
  }

  const tSoilSummary = (text) => {
    if (!text) return text
    for (const [eng, key] of Object.entries(soilSummaryMap)) {
      if (text.includes(eng)) {
        return text.replace(eng, t(key))
      }
    }
    const prefix = text.match(/^[✅⚠️🧪🎯💡✓]+/)?.[0] || ''
    const rest = text.slice(prefix.length).trim()
    if (rest) return prefix + ' ' + rest
    return text
  }

  const tGrowthStage = (stage) => {
    if (!stage) return stage
    const key = 'growthStageNames.' + stage
      .toLowerCase()
      .replace(/[\/\s-]+/g, '')
      .replace(/[']/g, '')
    const translated = t(key)
    return translated !== key ? translated : stage
  }

  const tXaiRecommendation = (rec) => {
    if (!rec) return rec
    const colonIdx = rec.indexOf(': ')
    if (colonIdx === -1) return rec
    const before = rec.slice(0, colonIdx)
    const after = rec.slice(colonIdx + 2)
    const factorMatch = before.match(/Improve\s+(.+)$/)
    let translatedBefore = before
    if (factorMatch) {
      const factorName = factorMatch[1].trim()
      const factorKey = recomFactorMap[factorName]
      if (factorKey) {
        translatedBefore = t('xaiPatterns.improve', { factor: t(factorKey) })
      }
    }
    const adviceKey = recomAdviceMap[after]
    const translatedAfter = adviceKey ? t(adviceKey) : after
    return translatedBefore + ': ' + translatedAfter
  }

  const tExplanation = (text) => {
    if (!text) return text
    text = text.replace(
      /✓ Your soil nitrogen \((\d+)\) is ideal for (\w+)/g,
      (_, val, crop) => t('xaiPatterns.nitrogenIdeal', { val, crop: t('crops.' + crop.toLowerCase()) || crop })
    )
    text = text.replace(
      /✓ Soil pH \(([\d.]+)\) matches (\w+) needs/g,
      (_, val, crop) => t('xaiPatterns.phMatch', { val, crop: t('crops.' + crop.toLowerCase()) || crop })
    )
    text = text.replace(
      /✓ Expected rainfall \(([\d.]+)mm\) suits (\w+) water needs/g,
      (_, val, water) => t('xaiPatterns.rainfallSuits', { val, water: water.toLowerCase() })
    )
    text = text.replace(
      /🎯 High confidence \(([\d.]+)%\) - This crop is a strong match!/g,
      (_, val) => t('xaiPatterns.highConfidence', { val })
    )
    return text
  }

  const tCropName = (name) => {
    if (!name) return name
    const key = 'crops.' + name.toLowerCase()
    const translated = t(key)
    return translated !== key ? translated : name
  }

  return { tSoilCategory, tSoilSummary, tGrowthStage, tXaiRecommendation, tExplanation, tCropName }
}
