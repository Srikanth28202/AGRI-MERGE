import React from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles, TrendingUp, Brain, Leaf } from 'lucide-react'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.22, 1, 0.36, 1]
    }
  }
}

const floatingIcons = [
  { Icon: Leaf, color: 'text-green-500', delay: 0 },
  { Icon: Brain, color: 'text-purple-500', delay: 0.2 },
  { Icon: TrendingUp, color: 'text-orange-500', delay: 0.4 },
  { Icon: Sparkles, color: 'text-blue-500', delay: 0.6 }
]

export default function Hero({ onGetStarted }) {
  const { t } = useTranslation()
  return (
    <section id="home" className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Floating background icons */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {floatingIcons.map(({ Icon, color, delay }, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ 
              opacity: 0.1, 
              scale: 1,
              y: [0, -30, 0]
            }}
            transition={{ 
              opacity: { delay: delay + 0.5, duration: 0.5 },
              scale: { delay: delay + 0.5, duration: 0.5 },
              y: { delay: delay + 1, duration: 4, repeat: Infinity, ease: "easeInOut" }
            }}
            className={`absolute ${
              index === 0 ? 'top-1/4 left-1/4' :
              index === 1 ? 'top-1/3 right-1/4' :
              index === 2 ? 'bottom-1/3 left-1/3' :
              'bottom-1/4 right-1/3'
            }`}
          >
            <Icon className={`w-16 h-16 ${color}`} strokeWidth={1} />
          </motion.div>
        ))}
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="text-center max-w-4xl mx-auto"
        >
          {/* Badge */}
          <motion.div variants={itemVariants} className="mb-6">
            <span className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 
                           text-primary-700 dark:text-primary-300 text-sm font-medium rounded-full">
              <Sparkles className="w-4 h-4" />
              {t('hero.badge')}
            </span>
          </motion.div>

          {/* Main headline */}
          <motion.h1 
            variants={itemVariants}
            className="text-5xl sm:text-6xl lg:text-7xl font-bold text-neutral-900 dark:text-white mb-6 leading-tight"
          >
            {t('hero.headline')}
            <br />
            <span className="gradient-text">{t('hero.headlineHighlight')}</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p 
            variants={itemVariants}
            className="text-xl text-neutral-600 dark:text-neutral-400 mb-10 max-w-2xl mx-auto leading-relaxed"
          >
            {t('hero.subheadline')}
          </motion.p>

          {/* CTA Buttons */}
          <motion.div 
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <motion.button
              whileHover={{ scale: 1.05, boxShadow: '0 20px 40px -10px rgba(16, 185, 129, 0.4)' }}
              whileTap={{ scale: 0.95 }}
              onClick={onGetStarted}
              className="group flex items-center gap-2 btn-primary text-lg px-8 py-4"
            >
              {t('hero.startPrediction')}
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn-secondary text-lg px-8 py-4"
              onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
            >
              {t('hero.learnMore')}
            </motion.button>
          </motion.div>

          {/* Stats */}
          <motion.div 
            variants={itemVariants}
            className="mt-16 grid grid-cols-3 gap-8 max-w-lg mx-auto"
          >
            {[
              { value: '22+', label: t('hero.crops') },
              { value: '99%', label: t('hero.accuracy') },
              { value: '24/7', label: t('hero.aiSupport') }
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 + index * 0.1 }}
                className="text-center"
              >
                <div className="text-3xl sm:text-4xl font-bold gradient-text mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-neutral-500 dark:text-neutral-400">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-6 h-10 border-2 border-neutral-300 dark:border-neutral-600 rounded-full flex justify-center pt-2"
        >
          <motion.div
            animate={{ y: [0, 12, 0], opacity: [1, 0.3, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-1.5 h-1.5 bg-primary-500 rounded-full"
          />
        </motion.div>
      </motion.div>
    </section>
  )
}
