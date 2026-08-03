import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Cell,
  ReferenceLine
} from 'recharts'
import { TrendingUp, Sparkles } from 'lucide-react'

const SHAP_COLORS = {
  positive: '#16a34a',
  negative: '#dc2626',
  base: '#9ca3af'
}

export default function PriceChart({ history, shap, cropName }) {
  const { t } = useTranslation()

  const yearly = useMemo(() => {
    if (!history?.points?.length) return []
    const byYear = {}
    for (const p of history.points) {
      if (!byYear[p.year]) byYear[p.year] = { year: p.year, historical: 0, projected: 0, hn: 0, pn: 0 }
      const key = p.projected ? 'projected' : 'historical'
      const nKey = p.projected ? 'pn' : 'hn'
      byYear[p.year][key] += p.wpi
      byYear[p.year][nKey] += 1
    }
    return Object.values(byYear)
      .map(y => ({
        year: String(y.year),
        historical: y.hn ? Math.round((y.historical / y.hn) * 100) / 100 : null,
        projected: y.pn ? Math.round((y.projected / y.pn) * 100) / 100 : null
      }))
      .sort((a, b) => Number(a.year) - Number(b.year))
  }, [history])

  const shapData = useMemo(() => {
    if (!shap?.values || !shap?.feature_names) return []
    const labels = {
      month: t('priceChart.month'),
      year: t('priceChart.year'),
      rainfall: t('priceChart.rainfall')
    }
    return shap.feature_names.map((name, i) => ({
      name: labels[name.toLowerCase()] || name,
      value: Math.round(shap.values[i] * 100) / 100
    }))
  }, [shap, t])

  if (!history?.points?.length) {
    return null
  }

  const maxAbs = Math.max(...shapData.map(d => Math.abs(d.value)), 1)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.45 }}
      className="bg-white rounded-2xl p-6 shadow-lg shadow-gray-200/50 border border-gray-100"
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="p-2 bg-emerald-100 rounded-xl">
          <TrendingUp className="w-5 h-5 text-emerald-600" />
        </div>
        <div>
          <h4 className="font-bold text-gray-800">{t('priceChart.title')}</h4>
          <p className="text-xs text-gray-500">
            {t('priceChart.subtitle', { crop: cropName })}
          </p>
        </div>
      </div>

      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={yearly} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="wpiGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="wpiGradientProj" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis
              dataKey="year"
              tick={{ fontSize: 12, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
              width={60}
            />
            <Tooltip
              formatter={(value, name) => [
                value == null ? '—' : `${value}`,
                name === 'historical' ? t('priceChart.legendHistorical') : t('priceChart.legendProjected')
              ]}
              labelFormatter={(label) => `${t('priceChart.year')}: ${label}`}
              contentStyle={{
                borderRadius: 12,
                border: '1px solid #e5e7eb',
                fontSize: 12
              }}
            />
            <Area
              type="monotone"
              dataKey="historical"
              stroke="#10b981"
              strokeWidth={2.5}
              fill="url(#wpiGradient)"
              dot={{ r: 3, fill: '#10b981', strokeWidth: 0 }}
              activeDot={{ r: 5 }}
            />
            <Area
              type="monotone"
              dataKey="projected"
              stroke="#f59e0b"
              strokeWidth={2.5}
              strokeDasharray="6 4"
              fill="url(#wpiGradientProj)"
              dot={{ r: 3, fill: '#f59e0b', strokeWidth: 0 }}
              activeDot={{ r: 5 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 rounded bg-emerald-500 inline-block" />
          {t('priceChart.legendHistorical')}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 rounded bg-amber-500 inline-block" style={{ borderTop: '2px dashed #f59e0b' }} />
          {t('priceChart.legendProjected')}
        </span>
      </div>

      {history.actual_through != null && Number(history.actual_through) < new Date().getFullYear() && (
        <p className="mt-1.5 text-[11px] text-gray-400">
          {t('priceChart.estNote', { year: history.actual_through })}
        </p>
      )}

      {shapData.length > 0 && (
        <div className="mt-6 pt-5 border-t border-gray-100">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <h5 className="font-semibold text-gray-800 text-sm">{t('priceChart.shapTitle')}</h5>
          </div>
          <p className="text-xs text-gray-500 mb-4">{t('priceChart.shapSubtitle')}</p>

          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={shapData}
                layout="vertical"
                margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
                <XAxis
                  type="number"
                  domain={[-maxAbs, maxAbs]}
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={70}
                  tick={{ fontSize: 12, fill: '#374151' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value) => [`${value} WPI`, t('priceChart.contribution')]}
                  contentStyle={{ borderRadius: 12, border: '1px solid #e5e7eb', fontSize: 12 }}
                />
                <ReferenceLine x={0} stroke="#9ca3af" />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={18}>
                  {shapData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.value >= 0 ? SHAP_COLORS.positive : SHAP_COLORS.negative}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {shap.expected_value != null && (
            <p className="text-xs text-gray-500 mt-2">
              {t('priceChart.baseValue')}: {shap.expected_value} WPI
              {shap.prediction != null && (
                <> · {t('priceChart.expectedPrediction')}: {shap.prediction} WPI</>
              )}
            </p>
          )}
        </div>
      )}
    </motion.div>
  )
}
