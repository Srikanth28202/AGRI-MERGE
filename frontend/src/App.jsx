import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import HomePage from './pages/HomePage'
import PredictPage from './pages/PredictPage'
import ResultsPage from './pages/ResultsPage'
import ChatPage from './pages/ChatPage'
import { Loader2, MessageCircle } from 'lucide-react'
import API from './api'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function AppContent() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [darkMode, setDarkMode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [locations, setLocations] = useState({})

  // Toggle dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  // Fetch locations on mount
  useEffect(() => {
    fetchLocations()
  }, [])

  const fetchLocations = async () => {
    try {
      const response = await API.get('/locations', {
        timeout: 5000
      })
      setLocations(response.data.state_districts || {})
    } catch (err) {
      console.error('Failed to fetch locations:', err)
      setLocations({})
    }
  }

  const handlePredict = async (formData) => {
    setLoading(true)
    setError(null)
    setResults(null)
    navigate('/results')

    try {
      const response = await API.post('/predict', formData)
      setResults(response.data)
    } catch (err) {
      let errorMessage = t('results.predictionError')
      if (err.response?.data) {
        if (err.response.data.detail) {
          if (typeof err.response.data.detail === 'string') {
            errorMessage = err.response.data.detail
          }
          else if (Array.isArray(err.response.data.detail)) {
            errorMessage = err.response.data.detail[0]?.msg || t('results.invalidInput')
          }
          else if (typeof err.response.data.detail === 'object') {
            errorMessage = err.response.data.detail.msg || err.response.data.detail.detail || t('results.invalidInput')
          }
        } else {
          errorMessage = t('results.serverError')
        }
      } else if (err.message) {
        errorMessage = err.message
      }
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`min-h-screen transition-colors duration-300 ${darkMode ? 'dark' : ''}`}>
      <div className="relative min-h-screen bg-white dark:bg-neutral-900 transition-colors duration-300">
        {/* Animated background gradient */}
        <div className="fixed inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-br from-primary-50/50 via-white to-accent-50/50 dark:from-neutral-900 dark:via-neutral-900 dark:to-neutral-800 opacity-60" />
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-400/20 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-400/20 rounded-full blur-3xl animate-float animation-delay-200" />
        </div>

        {/* Navigation */}
        <Navbar darkMode={darkMode} onToggleDark={() => setDarkMode(!darkMode)} />

        <ScrollToTop />

        {/* Main content */}
        <main className="relative z-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
            >
              <Routes location={location}>
                <Route
                  path="/"
                  element={<HomePage onGetStarted={() => navigate('/predict')} />}
                />
                <Route
                  path="/predict"
                  element={
                    <PredictPage
                      onSubmit={handlePredict}
                      loading={loading}
                      locations={locations}
                    />
                  }
                />
                <Route
                  path="/results"
                  element={
                    <ResultsPage
                      results={results}
                      error={error}
                      loading={loading}
                    />
                  }
                />
                <Route path="/chat" element={<ChatPage />} />
                <Route
                  path="*"
                  element={<HomePage onGetStarted={() => navigate('/predict')} />}
                />
              </Routes>
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Footer */}
        <Footer />

        {/* Floating chat shortcut */}
        {location.pathname !== '/chat' && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => navigate('/chat')}
            title={t('chatbot.fabLabel')}
            className="fixed bottom-6 right-6 z-40 p-4 rounded-full bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg shadow-green-500/30 hover:shadow-xl hover:shadow-green-500/40 transition-all duration-300"
          >
            <MessageCircle className="w-6 h-6" />
          </motion.button>
        )}

        {/* Global loading overlay */}
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="glass p-8 rounded-2xl flex flex-col items-center"
              >
                <Loader2 className="w-12 h-12 text-primary-500 animate-spin mb-4" />
                <p className="text-neutral-700 dark:text-neutral-300 font-medium">
                  {t('app.loading')}
                </p>
                <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-2">
                  {t('app.loadingSub')}
                </p>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}
