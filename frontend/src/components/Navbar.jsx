import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, NavLink } from 'react-router-dom'
import { Leaf, Menu, X, ArrowRight, Sun, Moon } from 'lucide-react'
import LanguageSwitcher from './LanguageSwitcher'

const navLinkClass = ({ isActive }) =>
  `px-5 py-2.5 text-sm font-medium rounded-full transition-all duration-300 ${
    isActive
      ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-md shadow-green-500/25'
      : 'text-gray-600 hover:text-green-700 hover:bg-white hover:shadow-sm'
  }`

export default function Navbar({ darkMode, onToggleDark }) {
  const { t } = useTranslation()
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const links = [
    { to: '/', label: t('navbar.home'), end: true },
    { to: '/#features', label: t('navbar.features') },
    { to: '/predict', label: t('navbar.predict') },
    { to: '/chat', label: t('navbar.chat') },
    { to: '/alerts', label: t('navbar.alerts') },
  ]

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-white/90 backdrop-blur-md shadow-lg py-3'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Premium Agriculture Logo */}
          <Link to="/" className="flex items-center gap-3 cursor-pointer group">
            <div className="relative">
              <div className="absolute inset-0 bg-green-500 rounded-2xl blur-md opacity-40 group-hover:opacity-60 transition-opacity" />
              <div className="relative p-2.5 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl shadow-lg">
                <Leaf className="w-7 h-7 text-white" strokeWidth={2} />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight">
                <span className="text-gray-800 dark:text-white">{t('navbar.brand')}</span>
                <span className="bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">{t('navbar.brandHighlight')}</span>
              </span>
              <span className="text-[10px] text-green-600 font-medium tracking-widest uppercase">{t('navbar.aiPowered')}</span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1 bg-gray-100/80 backdrop-blur-sm rounded-full p-1.5">
            {links.map((link, index) => (
              <motion.div
                key={link.to}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <NavLink to={link.to} end={link.end} className={navLinkClass}>
                  {link.label}
                </NavLink>
              </motion.div>
            ))}
          </div>

          {/* Right Controls */}
          <div className="hidden md:flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={onToggleDark}
              className="p-3 bg-gray-100/80 backdrop-blur-sm rounded-full shadow-sm hover:shadow transition-all duration-300"
              aria-label="Toggle theme"
            >
              <AnimatePresence mode="wait">
                {darkMode ? (
                  <motion.div
                    key="sun"
                    initial={{ rotate: -90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: 90, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Sun className="w-5 h-5 text-amber-500" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="moon"
                    initial={{ rotate: 90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: -90, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Moon className="w-5 h-5 text-gray-600" />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>

            <LanguageSwitcher />

            <Link
              to="/predict"
              onClick={() => setIsMobileMenuOpen(false)}
              className="group flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white text-sm font-semibold rounded-full shadow-lg shadow-green-500/25 hover:shadow-xl hover:shadow-green-500/30 hover:-translate-x-0.5 transition-all duration-300"
            >
              <span>{t('navbar.getStarted')}</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2.5 text-gray-700 bg-gray-100 rounded-xl"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </motion.button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden bg-white border-t border-gray-100 shadow-xl"
          >
            <div className="px-4 py-6 space-y-3">
              {links.map((link, index) => (
                <motion.div
                  key={link.to}
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <NavLink
                    to={link.to}
                    end={link.end}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `block w-full px-5 py-3.5 font-medium rounded-xl transition-colors duration-200 ${
                        isActive
                          ? 'bg-green-50 text-green-700'
                          : 'text-gray-700 hover:bg-green-50 hover:text-green-700'
                      }`
                    }
                  >
                    {link.label}
                  </NavLink>
                </motion.div>
              ))}

              <div className="flex items-center justify-between px-5 pt-2">
                <button
                  onClick={onToggleDark}
                  className="flex items-center gap-2 px-4 py-2.5 text-gray-700 bg-gray-100 rounded-xl"
                >
                  {darkMode ? <Sun className="w-5 h-5 text-amber-500" /> : <Moon className="w-5 h-5" />}
                  <span className="text-sm font-medium">{darkMode ? 'Light' : 'Dark'}</span>
                </button>
                <LanguageSwitcher />
              </div>

              <Link
                to="/predict"
                onClick={() => setIsMobileMenuOpen(false)}
                className="w-full mt-2 flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-semibold rounded-xl shadow-lg"
              >
                <span>{t('navbar.getStarted')}</span>
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  )
}
