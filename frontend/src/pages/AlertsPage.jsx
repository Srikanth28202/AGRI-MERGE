import React, { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bell,
  CloudSun,
  TrendingUp,
  Sprout,
  Send,
  Loader2,
  RefreshCw,
  Check,
  ChevronDown,
  Phone,
  User,
  MapPin,
  Globe,
  Info,
  AlertTriangle,
  CheckCircle2,
  MessageSquare
} from 'lucide-react'
import API from '../api'
import { locationData } from '../data/locationData'

const languages = [
  'en', 'hi', 'kn', 'te', 'ta', 'ml', 'mr', 'gu', 'bn', 'pa'
]

const categoryMeta = {
  weather: { icon: CloudSun, color: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300' },
  market: { icon: TrendingUp, color: 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-300' },
  farming: { icon: Sprout, color: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-300' },
}

const severityStyle = {
  warning: 'border-l-4 border-amber-500',
  info: 'border-l-4 border-blue-400',
  critical: 'border-l-4 border-red-500',
}

function timeAgo(iso, t) {
  const then = new Date(iso)
  const diffS = Math.max(0, (Date.now() - then.getTime()) / 1000)
  const mins = Math.floor(diffS / 60)
  if (mins < 1) return t('alerts.timeAgo.now')
  if (mins < 60) return `${mins} ${t('alerts.timeAgo.min')}`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} ${t('alerts.timeAgo.hr')}`
  const days = Math.floor(hrs / 24)
  return `${days} ${t('alerts.timeAgo.day')}`
}

const Toggle = ({ checked, onChange, label }) => (
  <button
    type="button"
    onClick={onChange}
    className={`flex items-center justify-between w-full px-4 py-2.5 rounded-xl border text-sm font-medium transition-all duration-200 ${
      checked
        ? 'bg-green-50 dark:bg-green-900/30 border-green-300 dark:border-green-700 text-green-700 dark:text-green-300'
        : 'bg-white dark:bg-neutral-800 border-gray-200 dark:border-neutral-700 text-gray-500 dark:text-gray-400'
    }`}
  >
    <span>{label}</span>
    <span className={`relative w-9 h-5 rounded-full transition-colors duration-200 ${checked ? 'bg-green-500' : 'bg-gray-300 dark:bg-neutral-600'}`}>
      <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all duration-200 ${checked ? 'left-4' : 'left-0.5'}`} />
    </span>
  </button>
)

const InputField = ({ icon: Icon, label, ...props }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{label}</label>
    <div className="relative">
      {Icon && (
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
          <Icon className="w-4 h-4" />
        </div>
      )}
      <input
        {...props}
        className={`w-full bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-3 text-gray-800 dark:text-gray-100 placeholder:text-gray-400
          focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all duration-200 ${Icon ? 'pl-10' : ''}`}
      />
    </div>
  </div>
)

const SelectField = ({ icon: Icon, label, children, ...props }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{label}</label>
    <div className="relative">
      {Icon && (
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
          <Icon className="w-4 h-4" />
        </div>
      )}
      <select
        {...props}
        className={`w-full bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-3 text-gray-800 dark:text-gray-100
          focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 appearance-none cursor-pointer ${Icon ? 'pl-10' : ''}`}
      >
        {children}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
    </div>
  </div>
)

export default function AlertsPage() {
  const { t, i18n } = useTranslation()
  const [locations, setLocations] = useState(locationData)
  const [crops, setCrops] = useState([])
  const [status, setStatus] = useState(null)
  const [farmer, setFarmer] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [registering, setRegistering] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [sending, setSending] = useState(false)
  const [toast, setToast] = useState(null)
  const [form, setForm] = useState({
    name: '',
    phone: '',
    language: 'en',
    state: '',
    district: '',
    crops: [],
    prefs: { weather: true, market: true, farming: true }
  })

  const notify = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 4000)
  }

  const fetchStatus = useCallback(async () => {
    try {
      const res = await API.get('/alerts/status', { timeout: 5000 })
      setStatus(res.data)
    } catch (err) {
      console.error('Failed to fetch alert status:', err)
      setStatus(null)
    }
  }, [])

  const loadFarmer = useCallback(async (id) => {
    try {
      const res = await API.get(`/alerts/farmers/${id}/alerts`, { timeout: 5000 })
      setAlerts(res.data.alerts || [])
      setFarmer(res.data.farmer_id ? (await API.get(`/alerts/farmers/${id}`, { timeout: 5000 })).data.farmer : null)
    } catch (err) {
      localStorage.removeItem('agri_alert_farmer_id')
      setFarmer(null)
      setAlerts([])
    }
  }, [])

  useEffect(() => {
    (async () => {
      try {
        const [locRes, cropRes] = await Promise.all([
          API.get('/locations', { timeout: 5000 }),
          API.get('/alerts/crops', { timeout: 5000 }),
        ])
        if (locRes.data.state_districts && Object.keys(locRes.data.state_districts).length) {
          setLocations(locRes.data.state_districts)
        }
        setCrops((cropRes.data.crops || []).map(c => c.name))
      } catch (err) {
        console.error('Failed to load alerts setup:', err)
      }
      const saved = localStorage.getItem('agri_alert_farmer_id')
      if (saved) await loadFarmer(saved)
      await fetchStatus()
      setLoading(false)
    })()
  }, [loadFarmer, fetchStatus])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (name === 'state') setForm((prev) => ({ ...prev, district: '' }))
  }

  const toggleCrop = (crop) => {
    setForm((prev) => ({
      ...prev,
      crops: prev.crops.includes(crop)
        ? prev.crops.filter((c) => c !== crop)
        : [...prev.crops, crop],
    }))
  }

  const togglePref = (key) => {
    setForm((prev) => ({ ...prev, prefs: { ...prev.prefs, [key]: !prev.prefs[key] } }))
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    if (!form.name || !form.phone || !form.state || !form.district) {
      notify(t('alerts.toast.fillForm'))
      return
    }
    setRegistering(true)
    try {
      const res = await API.post('/alerts/register', {
        name: form.name,
        phone: form.phone,
        language: form.language,
        state: form.state,
        district: form.district,
        crops: form.crops,
        alert_preferences: form.prefs,
      }, { timeout: 8000 })
      const f = res.data.farmer
      localStorage.setItem('agri_alert_farmer_id', f.id)
      setFarmer(f)
      await loadFarmer(f.id)
      await fetchStatus()
      notify(t('alerts.toast.registered'))
    } catch (err) {
      console.error(err)
      notify(t('alerts.toast.error'))
    } finally {
      setRegistering(false)
    }
  }

  const handleGenerate = async () => {
    if (!farmer) {
      notify(t('alerts.toast.registerFirst'))
      return
    }
    setGenerating(true)
    try {
      await API.post('/alerts/generate', { farmer_id: farmer.id }, { timeout: 20000 })
      await loadFarmer(farmer.id)
      notify(t('alerts.toast.generated'))
    } catch (err) {
      console.error(err)
      notify(t('alerts.toast.error'))
    } finally {
      setGenerating(false)
    }
  }

  const handleTestSms = async () => {
    if (!farmer) {
      notify(t('alerts.toast.registerFirst'))
      return
    }
    setSending(true)
    try {
      const res = await API.post('/alerts/send-test', { phone: farmer.phone, language: farmer.language }, { timeout: 10000 })
      notify(res.data.delivered ? t('alerts.toast.testSent') : t('alerts.toast.error'))
    } catch (err) {
      console.error(err)
      notify(t('alerts.toast.error'))
    } finally {
      setSending(false)
    }
  }

  const markRead = async (alert) => {
    try {
      await API.post(`/alerts/alerts/${alert.id}/read`, {}, { timeout: 5000 })
      setAlerts((prev) => prev.map((a) => (a.id === alert.id ? { ...a, read: true } : a)))
      if (farmer) setFarmer((f) => (f ? { ...f, unread_count: Math.max(0, (f.unread_count || 1) - 1) } : f))
    } catch (err) {
      console.error(err)
    }
  }

  const resetSubscription = () => {
    localStorage.removeItem('agri_alert_farmer_id')
    setFarmer(null)
    setAlerts([])
    setForm({ name: '', phone: '', language: i18n.language || 'en', state: '', district: '', crops: [], prefs: { weather: true, market: true, farming: true } })
  }

  const districts = form.state ? (locations[form.state] || []) : []
  const unreadCount = alerts.filter((a) => !a.read).length

  if (loading) {
    return (
      <section className="py-20 lg:py-28 section-padding min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center">
          <Loader2 className="w-10 h-10 text-green-600 animate-spin mb-4" />
          <p className="text-gray-600 dark:text-gray-300">{t('app.loading')}</p>
        </div>
      </section>
    )
  }

  return (
    <section className="py-20 lg:py-28 section-padding min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-sm font-medium rounded-full mb-4">
            <Bell className="w-4 h-4" />
            {t('alerts.badge')}
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-neutral-900 dark:text-white mb-4">
            {t('alerts.title')}
          </h2>
          <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
            {t('alerts.subtitle')}
          </p>
        </motion.div>

        {/* Toast */}
        <AnimatePresence>
          {toast && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="fixed top-24 left-1/2 -translate-x-1/2 z-50 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 px-5 py-3 rounded-2xl shadow-xl text-sm font-medium"
            >
              {toast}
            </motion.div>
          )}
        </AnimatePresence>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="grid lg:grid-cols-5 gap-8"
        >
          {/* Left column: registration / subscription + status */}
          <div className="lg:col-span-2 space-y-6">
            {/* Registration card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.5 }}
              className="glass-card p-6 lg:p-7"
            >
              {farmer ? (
                <>
                  <div className="flex items-center justify-between mb-5">
                    <h3 className="text-xl font-bold text-neutral-900 dark:text-white flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                      {t('alerts.subscription')}
                    </h3>
                    <button
                      onClick={resetSubscription}
                      className="text-xs font-medium text-gray-400 hover:text-red-500 transition-colors"
                    >
                      {t('alerts.edit')}
                    </button>
                  </div>
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center gap-2 text-gray-700 dark:text-gray-200">
                      <User className="w-4 h-4 text-green-600" />
                      <span>{farmer.name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-700 dark:text-gray-200">
                      <Phone className="w-4 h-4 text-green-600" />
                      <span>{farmer.phone}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-700 dark:text-gray-200">
                      <MapPin className="w-4 h-4 text-green-600" />
                      <span>{farmer.district}, {farmer.state}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-700 dark:text-gray-200">
                      <Globe className="w-4 h-4 text-green-600" />
                      <span>{farmer.language}</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {(farmer.crops || []).map((crop) => (
                        <span key={crop} className="px-2.5 py-1 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-lg text-xs font-medium uppercase">
                          {crop}
                        </span>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <form onSubmit={handleRegister}>
                  <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-1">{t('alerts.registerCard.title')}</h3>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-5">{t('alerts.registerCard.subtitle')}</p>

                  <div className="space-y-4">
                    <InputField
                      icon={User}
                      label={t('alerts.name')}
                      name="name"
                      value={form.name}
                      onChange={handleChange}
                      placeholder={t('alerts.namePlaceholder')}
                    />
                    <InputField
                      icon={Phone}
                      label={t('alerts.phone')}
                      name="phone"
                      value={form.phone}
                      onChange={handleChange}
                      placeholder={t('alerts.phonePlaceholder')}
                    />

                    <div className="grid grid-cols-2 gap-4">
                      <SelectField
                        icon={Globe}
                        label={t('alerts.language')}
                        name="language"
                        value={form.language}
                        onChange={handleChange}
                      >
                        <option value="">{t('alerts.selectLanguage')}</option>
                        {languages.map((code) => (
                          <option key={code} value={code}>{t('languageSwitcher.' + code)}</option>
                        ))}
                      </SelectField>
                      <SelectField
                        icon={MapPin}
                        label={t('alerts.state')}
                        name="state"
                        value={form.state}
                        onChange={handleChange}
                      >
                        <option value="">{t('alerts.selectState')}</option>
                        {Object.keys(locations).map((state) => (
                          <option key={state} value={state}>{state}</option>
                        ))}
                      </SelectField>
                    </div>

                    <SelectField
                      icon={MapPin}
                      label={t('alerts.district')}
                      name="district"
                      value={form.district}
                      onChange={handleChange}
                      disabled={!form.state}
                    >
                      <option value="">{form.state ? t('alerts.selectDistrict') : t('alerts.stateFirst')}</option>
                      {districts.map((d) => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </SelectField>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{t('alerts.crops')}</label>
                      <div className="flex flex-wrap gap-2">
                        {crops.map((crop) => (
                          <button
                            type="button"
                            key={crop}
                            onClick={() => toggleCrop(crop)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium uppercase border transition-all duration-200 ${
                              form.crops.includes(crop)
                                ? 'bg-green-600 text-white border-green-600'
                                : 'bg-white dark:bg-neutral-800 border-gray-200 dark:border-neutral-700 text-gray-600 dark:text-gray-300 hover:border-green-400'
                            }`}
                          >
                            {crop}
                          </button>
                        ))}
                      </div>
                      <p className="text-xs text-gray-400 mt-1.5">{t('alerts.cropsHint')}</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('alerts.prefs')}</label>
                      <div className="space-y-2">
                        <Toggle checked={form.prefs.weather} onChange={() => togglePref('weather')} label={t('alerts.prefWeather')} />
                        <Toggle checked={form.prefs.market} onChange={() => togglePref('market')} label={t('alerts.prefMarket')} />
                        <Toggle checked={form.prefs.farming} onChange={() => togglePref('farming')} label={t('alerts.prefFarming')} />
                      </div>
                    </div>

                    <motion.button
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.98 }}
                      type="submit"
                      disabled={registering}
                      className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-semibold rounded-xl shadow-lg shadow-green-500/25 hover:shadow-xl disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      {registering ? <Loader2 className="w-5 h-5 animate-spin" /> : <Bell className="w-5 h-5" />}
                      {registering ? t('alerts.registering') : t('alerts.registerBtn')}
                    </motion.button>
                  </div>
                </form>
              )}
            </motion.div>

            {/* Status card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25, duration: 0.5 }}
              className="glass-card p-6"
            >
              <h3 className="text-lg font-bold text-neutral-900 dark:text-white flex items-center gap-2 mb-4">
                <Info className="w-5 h-5 text-blue-500" />
                {t('alerts.statusCard.title')}
              </h3>
              {status ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">{status.farmers_registered}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('alerts.statusFarmers')}</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{status.supported_crops.length}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('alerts.statusCrops')}</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-neutral-700 dark:text-neutral-200 truncate">{status.provider}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('alerts.statusProvider')}</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-neutral-700 dark:text-neutral-200">{status.generation_interval_hours}h</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('alerts.statusInterval')}</div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-500">{t('alerts.inboxEmpty')}</p>
              )}

              {/* Demo actions */}
              <div className="grid grid-cols-2 gap-3 mt-6">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleGenerate}
                  disabled={generating || !farmer}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                  {t('alerts.generateBtn')}
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleTestSms}
                  disabled={sending || !farmer}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 text-white text-sm font-semibold rounded-xl hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {t('alerts.testSmsBtn')}
                </motion.button>
              </div>
              <p className="text-xs text-gray-400 mt-3">
                {status ? status.provider_description : ''}
              </p>
            </motion.div>
          </div>

          {/* Right column: inbox */}
          <div className="lg:col-span-3">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35, duration: 0.5 }}
              className="glass-card p-6 lg:p-7 h-full"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-neutral-900 dark:text-white flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-green-600" />
                  {t('alerts.inboxTitle')}
                  {farmer && (
                    <span className={`ml-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${unreadCount > 0 ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-500'}`}>
                      {unreadCount}
                    </span>
                  )}
                </h3>
              </div>

              {!farmer ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <Bell className="w-12 h-12 text-gray-300 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400 max-w-xs">{t('alerts.inboxRegisterHint')}</p>
                </div>
              ) : alerts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <Bell className="w-12 h-12 text-gray-300 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400 max-w-xs">{t('alerts.inboxEmpty')}</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
                  <AnimatePresence>
                    {alerts.map((alert) => {
                      const Cat = categoryMeta[alert.category] || categoryMeta.weather
                      return (
                        <motion.div
                          key={alert.id}
                          initial={{ opacity: 0, y: 16 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.98 }}
                          className={`glass-card p-4 ${severityStyle[alert.severity] || severityStyle.info} ${
                            alert.read ? 'opacity-60' : ''
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`p-2.5 rounded-xl shrink-0 ${Cat.color}`}>
                              <Cat.icon className="w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm font-bold text-neutral-900 dark:text-white">{alert.title}</span>
                                <span className="text-[10px] px-2 py-0.5 rounded-full uppercase font-semibold bg-gray-100 dark:bg-neutral-700 text-gray-500 dark:text-gray-300">
                                  {alert.category}
                                </span>
                                {alert.severity === 'warning' && (
                                  <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-600 font-semibold uppercase">
                                    <AlertTriangle className="w-3 h-3" />
                                    {t('alerts.severity.warning')}
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1.5 leading-relaxed">
                                {alert.message}
                              </p>
                              <div className="flex items-center justify-between mt-2.5">
                                <span className="text-xs text-gray-400">{timeAgo(alert.created_at, t)}</span>
                                {!alert.read && (
                                  <motion.button
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => markRead(alert)}
                                    className="flex items-center gap-1 text-xs font-medium text-green-600 hover:text-green-700 transition-colors"
                                  >
                                    <Check className="w-3.5 h-3.5" />
                                    {t('alerts.markRead')}
                                  </motion.button>
                                )}
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )
                    })}
                  </AnimatePresence>
                </div>
              )}
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}