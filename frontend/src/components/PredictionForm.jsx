import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { 
  MapPin, 
  Calendar, 
  Sun, 
  Droplets, 
  FlaskConical,
  Sprout,
  Send,
  Loader2,
  ChevronDown,
  Leaf,
  ThermometerSun
} from 'lucide-react'
import { locationData } from '../data/locationData'

const currentYear = new Date().getFullYear()
const years = Array.from({ length: 3 }, (_, i) => currentYear + i)

// Helper for section headers
const SectionHeader = ({ icon: Icon, title, subtitle, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600'
  }
  
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className={`p-2.5 rounded-xl ${colorClasses[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <h3 className="font-semibold text-gray-800">{title}</h3>
        <p className="text-xs text-gray-500">{subtitle}</p>
      </div>
    </div>
  )
}

// Helper for input fields
const InputField = ({ label, name, value, onChange, type = "text", placeholder, icon: Icon, min, max, step }) => (
  <div className="relative group">
    <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
    <div className="relative">
      {Icon && (
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-green-600 transition-colors">
          <Icon className="w-4 h-4" />
        </div>
      )}
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        className={`w-full bg-white border border-gray-200 rounded-xl px-4 py-3 text-gray-800 placeholder:text-gray-400
          focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500
          hover:border-gray-300 transition-all duration-200 ${Icon ? 'pl-10' : ''}`}
      />
    </div>
  </div>
)

// Helper for select fields
const SelectField = ({ label, name, value, onChange, options, placeholder, icon: Icon, disabled = false }) => (
  <div className="relative group">
    <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
    <div className="relative">
      {Icon && (
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-green-600 transition-colors">
          <Icon className="w-4 h-4" />
        </div>
      )}
      <select
        name={name}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={`w-full bg-white border border-gray-200 rounded-xl px-4 py-3 text-gray-800
          focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500
          hover:border-gray-300 transition-all duration-200 appearance-none cursor-pointer
          disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed ${Icon ? 'pl-10' : ''}`}
      >
        <option value="">{placeholder}</option>
        {options.map(opt => (
          <option key={opt.value || opt} value={opt.value || opt}>
            {opt.label || opt}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
    </div>
  </div>
)

export default function PredictionForm({ onSubmit, loading, locations: apiLocations }) {
  const { t } = useTranslation()

  const formSections = {
    location: {
      icon: MapPin,
      title: t('predictionForm.location.title'),
      subtitle: t('predictionForm.location.subtitle'),
      color: 'blue'
    },
    time: {
      icon: Calendar,
      title: t('predictionForm.timePeriod.title'),
      subtitle: t('predictionForm.timePeriod.subtitle'),
      color: 'amber'
    },
    soil: {
      icon: FlaskConical,
      title: t('predictionForm.soil.title'),
      subtitle: t('predictionForm.soil.subtitle'),
      color: 'green'
    },
    climate: {
      icon: Sun,
      title: t('predictionForm.climate.title'),
      subtitle: t('predictionForm.climate.subtitle'),
      color: 'orange'
    }
  }

  const months = [
    { name: t('predictionForm.months.january'), code: 'JAN' },
    { name: t('predictionForm.months.february'), code: 'FEB' },
    { name: t('predictionForm.months.march'), code: 'MAR' },
    { name: t('predictionForm.months.april'), code: 'APR' },
    { name: t('predictionForm.months.may'), code: 'MAY' },
    { name: t('predictionForm.months.june'), code: 'JUN' },
    { name: t('predictionForm.months.july'), code: 'JUL' },
    { name: t('predictionForm.months.august'), code: 'AUG' },
    { name: t('predictionForm.months.september'), code: 'SEP' },
    { name: t('predictionForm.months.october'), code: 'OCT' },
    { name: t('predictionForm.months.november'), code: 'NOV' },
    { name: t('predictionForm.months.december'), code: 'DEC' }
  ]

  const [formData, setFormData] = useState({
    state: '',
    district: '',
    month: '',
    year: currentYear,
    nitrogen: '',
    phosphorous: '',
    potassium: '',
    ph: '',
    temperature: '',
    humidity: ''
  })
  
  const [effectiveLocations, setEffectiveLocations] = useState(locationData)
  
  useEffect(() => {
    if (apiLocations && Object.keys(apiLocations).length > 0) {
      setEffectiveLocations(apiLocations)
    }
  }, [apiLocations])
  
  useEffect(() => {
    if (formData.state && !effectiveLocations[formData.state]?.includes(formData.district)) {
      setFormData(prev => ({ ...prev, district: '' }))
    }
  }, [formData.state, effectiveLocations])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!formData.state || !formData.district || !formData.month || !formData.year) {
      return
    }
    
    if (!formData.nitrogen || !formData.phosphorous || !formData.potassium || !formData.ph) {
      return
    }
    
    const submitData = {
      state: formData.state,
      district: formData.district,
      month: formData.month,
      year: parseInt(formData.year),
      nitrogen: parseFloat(formData.nitrogen),
      phosphorous: parseFloat(formData.phosphorous),
      potassium: parseFloat(formData.potassium),
      ph: parseFloat(formData.ph),
      temperature: formData.temperature ? parseFloat(formData.temperature) : undefined,
      humidity: formData.humidity ? parseFloat(formData.humidity) : undefined
    }
    
    onSubmit(submitData)
  }

  const states = Object.keys(effectiveLocations || {}).sort()
  const districts = formData.state ? effectiveLocations[formData.state] || [] : []


  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-white rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100 overflow-hidden"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-white/20 rounded-xl">
            <Sprout className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{t('predictionForm.headerTitle')}</h2>
            <p className="text-green-100 text-sm">{t('predictionForm.headerSubtitle')}</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-8">
        {/* Location Section */}
        <div>
          <SectionHeader {...formSections.location} />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <SelectField
              label={t('predictionForm.location.state')}
              name="state"
              value={formData.state}
              onChange={handleChange}
              options={states}
              placeholder={t('predictionForm.location.selectState')}
              icon={MapPin}
            />
            <SelectField
              label={t('predictionForm.location.district')}
              name="district"
              value={formData.district}
              onChange={handleChange}
              options={districts}
              placeholder={formData.state ? t('predictionForm.location.selectDistrict') : t('predictionForm.location.selectStateFirst')}
              icon={MapPin}
              disabled={!formData.state}
            />
          </div>
        </div>

        {/* Time Period Section */}
        <div>
          <SectionHeader {...formSections.time} />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <SelectField
              label={t('predictionForm.timePeriod.month')}
              name="month"
              value={formData.month}
              onChange={handleChange}
              options={months.map(m => ({ value: m.code, label: m.name }))}
              placeholder={t('predictionForm.timePeriod.selectMonth')}
              icon={Calendar}
            />
            <SelectField
              label={t('predictionForm.timePeriod.year')}
              name="year"
              value={formData.year}
              onChange={handleChange}
              options={years}
              placeholder={t('predictionForm.timePeriod.selectYear')}
              icon={Calendar}
            />
          </div>
        </div>

        {/* Soil Analysis Section */}
        <div>
          <SectionHeader {...formSections.soil} />
          <div className="grid grid-cols-2 gap-4">
            <InputField
              label={t('predictionForm.soil.nitrogen')}
              name="nitrogen"
              type="number"
              value={formData.nitrogen}
              onChange={handleChange}
              placeholder={t('predictionForm.soil.placeholderRange')}
              icon={Leaf}
              min="0"
              max="200"
            />
            <InputField
              label={t('predictionForm.soil.phosphorous')}
              name="phosphorous"
              type="number"
              value={formData.phosphorous}
              onChange={handleChange}
              placeholder={t('predictionForm.soil.placeholderRange')}
              icon={Leaf}
              min="0"
              max="200"
            />
            <InputField
              label={t('predictionForm.soil.potassium')}
              name="potassium"
              type="number"
              value={formData.potassium}
              onChange={handleChange}
              placeholder={t('predictionForm.soil.placeholderRange')}
              icon={Leaf}
              min="0"
              max="200"
            />
            <InputField
              label={t('predictionForm.soil.phLevel')}
              name="ph"
              type="number"
              step="0.1"
              value={formData.ph}
              onChange={handleChange}
              placeholder={t('predictionForm.soil.placeholderPh')}
              icon={FlaskConical}
              min="0"
              max="14"
            />
          </div>
        </div>

        {/* Climate Section (Optional) */}
        <div>
          <SectionHeader {...formSections.climate} />
          <div className="bg-amber-50 rounded-xl p-4 mb-4">
            <p className="text-sm text-amber-700 flex items-center gap-2">
              <Sun className="w-4 h-4" />
              {t('predictionForm.climate.note')}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <InputField
              label={t('predictionForm.climate.temperature')}
              name="temperature"
              type="number"
              value={formData.temperature}
              onChange={handleChange}
              placeholder={t('predictionForm.climate.optional')}
              icon={ThermometerSun}
            />
            <InputField
              label={t('predictionForm.climate.humidity')}
              name="humidity"
              type="number"
              value={formData.humidity}
              onChange={handleChange}
              placeholder={t('predictionForm.climate.optional')}
              icon={Droplets}
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={loading}
            className="w-full group flex items-center justify-center gap-3 py-4 bg-gradient-to-r from-green-600 to-emerald-600 
              text-white font-semibold rounded-xl shadow-lg shadow-green-500/30 
              hover:shadow-xl hover:shadow-green-500/40 transition-all duration-300
              disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>{t('predictionForm.submit.analyzing')}</span>
              </>
            ) : (
              <>
                <Send className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                <span>{t('predictionForm.submit.getRecommendation')}</span>
              </>
            )}
          </motion.button>
        </div>
      </form>
    </motion.div>
  )
}
