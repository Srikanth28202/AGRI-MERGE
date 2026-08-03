import React, { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Wallet, IndianRupee, TrendingUp, Info } from 'lucide-react'

// Average Indian yield (quintals/acre) and input cost (INR/acre) by crop.
// Used only when the backend price is available; figures are national averages.
const cropEconomics = {
  wheat: { yield: 28, costPerAcre: 9000 },
  rice: { yield: 22, costPerAcre: 11000 },
  paddy: { yield: 22, costPerAcre: 11000 },
  maize: { yield: 24, costPerAcre: 8500 },
  cotton: { yield: 8, costPerAcre: 14000 },
  groundnut: { yield: 12, costPerAcre: 10000 },
  sugarcane: { yield: 450, costPerAcre: 25000 },
  gram: { yield: 10, costPerAcre: 7000 },
  moong: { yield: 8, costPerAcre: 6500 },
  bajra: { yield: 12, costPerAcre: 6000 },
  jute: { yield: 18, costPerAcre: 9000 },
  arhar: { yield: 9, costPerAcre: 7000 },
  masoor: { yield: 8, costPerAcre: 6500 },
  urad: { yield: 7, costPerAcre: 6500 },
  ragi: { yield: 12, costPerAcre: 6000 },
  soybean: { yield: 12, costPerAcre: 8000 },
  soyabean: { yield: 12, costPerAcre: 8000 },
  sunflower: { yield: 8, costPerAcre: 7500 },
  sesamum: { yield: 4, costPerAcre: 6000 },
  safflower: { yield: 6, costPerAcre: 6500 },
  niger: { yield: 4, costPerAcre: 5500 },
  rape: { yield: 10, costPerAcre: 7500 },
  barley: { yield: 22, costPerAcre: 7000 },
  copra: { yield: 35, costPerAcre: 18000 },
  default: { yield: 15, costPerAcre: 8000 }
}

const money = (n) => Math.round(n).toLocaleString('en-IN')

export default function ProfitCalculator({ crop, price, priceAvailable }) {
  const { t } = useTranslation()
  const [acres, setAcres] = useState(1)

  const econ = cropEconomics[crop?.toLowerCase()] || cropEconomics.default

  const values = useMemo(() => {
    const pricePerQuintal = Number(price) || 0
    const totalYield = econ.yield * acres
    const revenue = totalYield * pricePerQuintal
    const totalCost = econ.costPerAcre * acres
    const net = revenue - totalCost
    return {
      pricePerQuintal,
      totalYield,
      revenue,
      totalCost,
      net,
      netPerAcre: net / Math.max(acres, 1),
      grossPerAcre: revenue / Math.max(acres, 1)
    }
  }, [price, acres, econ])

  if (!priceAvailable || !price) {
    return null
  }

  const netColor = values.net >= 0 ? 'text-green-600' : 'text-red-600'
  const netBg = values.net >= 0 ? 'bg-gradient-to-br from-green-500 to-emerald-600' : 'bg-gradient-to-br from-red-500 to-rose-600'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="bg-white rounded-2xl p-6 shadow-lg shadow-gray-200/50 border border-gray-100"
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="p-2 bg-amber-100 rounded-xl">
          <Wallet className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <h4 className="font-bold text-gray-800">{t('profitCalculator.title')}</h4>
          <p className="text-xs text-gray-500">
            {t('profitCalculator.subtitle', { crop })}
          </p>
        </div>
      </div>

      {/* Farm size input */}
      <div className="flex items-center gap-4 mb-5">
        <label className="text-sm font-medium text-gray-600 shrink-0">
          {t('profitCalculator.acresLabel')}
        </label>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setAcres(Math.max(0.5, Math.round((acres - 0.5) * 10) / 10))}
            className="w-9 h-9 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold transition-colors"
          >
            −
          </button>
          <input
            type="number"
            min="0.5"
            step="0.5"
            value={acres}
            onChange={(e) => {
              const v = parseFloat(e.target.value)
              if (!isNaN(v) && v > 0) setAcres(v)
            }}
            className="w-24 text-center text-lg font-bold text-gray-800 bg-gray-50 border border-gray-200 rounded-xl px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            type="button"
            onClick={() => setAcres(Math.round((acres + 0.5) * 10) / 10)}
            className="w-9 h-9 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold transition-colors"
          >
            +
          </button>
        </div>
      </div>

      {/* Assumptions */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="p-3 bg-gray-50 rounded-xl">
          <p className="text-xs text-gray-500 mb-0.5">{t('profitCalculator.yieldLabel')}</p>
          <p className="font-bold text-gray-800">
            {econ.yield} {t('profitCalculator.quintalsPerAcre')}
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded-xl">
          <p className="text-xs text-gray-500 mb-0.5">{t('profitCalculator.pricePerQuintal')}</p>
          <p className="font-bold text-gray-800 flex items-center">
            <IndianRupee className="w-3.5 h-3.5 mr-1" />{money(values.pricePerQuintal)}
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded-xl">
          <p className="text-xs text-gray-500 mb-0.5">{t('profitCalculator.inputCostPerAcre')}</p>
          <p className="font-bold text-gray-800 flex items-center">
            <IndianRupee className="w-3.5 h-3.5 mr-1" />{money(econ.costPerAcre)}
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded-xl">
          <p className="text-xs text-gray-500 mb-0.5">{t('profitCalculator.totalYield')}</p>
          <p className="font-bold text-gray-800">{Math.round(values.totalYield)} {t('profitCalculator.quintals')}</p>
        </div>
      </div>

      {/* Results */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
          <p className="text-xs text-emerald-700 mb-1 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" /> {t('profitCalculator.revenue')}
          </p>
          <p className="text-lg font-bold text-emerald-800 flex items-center">
            <IndianRupee className="w-4 h-4 mr-1" />{money(values.revenue)}
          </p>
          <p className="text-[11px] text-emerald-600">
            {money(values.grossPerAcre)} {t('profitCalculator.perAcre')}
          </p>
        </div>
        <div className="p-4 bg-orange-50 rounded-xl border border-orange-100">
          <p className="text-xs text-orange-700 mb-1">{t('profitCalculator.totalCost')}</p>
          <p className="text-lg font-bold text-orange-800 flex items-center">
            <IndianRupee className="w-4 h-4 mr-1" />{money(values.totalCost)}
          </p>
          <p className="text-[11px] text-orange-600">
            {money(econ.costPerAcre)} {t('profitCalculator.perAcre')}
          </p>
        </div>
        <div className={`p-4 rounded-xl text-white ${netBg}`}>
          <p className="text-xs text-white/80 mb-1">{t('profitCalculator.netProfit')}</p>
          <p className="text-lg font-bold flex items-center">
            <IndianRupee className="w-4 h-4 mr-1" />{money(values.net)}
          </p>
          <p className="text-[11px] text-white/80">
            {money(values.netPerAcre)} {t('profitCalculator.perAcre')}
          </p>
        </div>
      </div>

      <div className="flex items-start gap-2 p-3 bg-gray-50 rounded-xl">
        <Info className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
        <p className="text-xs text-gray-500">{t('profitCalculator.disclaimer')}</p>
      </div>
    </motion.div>
  )
}
