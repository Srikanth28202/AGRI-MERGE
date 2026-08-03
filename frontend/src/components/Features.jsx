import React from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { 
  Brain, 
  TrendingUp, 
  Sun, 
  MessageCircle, 
  Zap,
  Globe,
  CheckCircle2
} from 'lucide-react'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.22, 1, 0.36, 1]
    }
  }
}

export default function Features() {
  const { t } = useTranslation()

  const features = [
    {
      icon: Brain,
      title: t('features.cards.cropPrediction.title'),
      description: t('features.cards.cropPrediction.description'),
      color: 'from-violet-500 to-purple-600',
      bgColor: 'bg-violet-50 dark:bg-violet-900/20'
    },
    {
      icon: TrendingUp,
      title: t('features.cards.priceForecasting.title'),
      description: t('features.cards.priceForecasting.description'),
      color: 'from-amber-500 to-orange-600',
      bgColor: 'bg-amber-50 dark:bg-amber-900/20'
    },
    {
      icon: Sun,
      title: t('features.cards.weatherIntegration.title'),
      description: t('features.cards.weatherIntegration.description'),
      color: 'from-yellow-500 to-amber-600',
      bgColor: 'bg-yellow-50 dark:bg-yellow-900/20'
    },
    {
      icon: MessageCircle,
      title: t('features.cards.aiChatbot.title'),
      description: t('features.cards.aiChatbot.description'),
      color: 'from-emerald-500 to-green-600',
      bgColor: 'bg-emerald-50 dark:bg-emerald-900/20'
    }
  ]
  return (
    <section id="features" className="py-20 lg:py-32 section-padding">
      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 bg-accent-100 dark:bg-accent-900/30 
                         text-accent-700 dark:text-accent-300 text-sm font-medium rounded-full mb-4">
            {t('features.badge')}
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-neutral-900 dark:text-white mb-4">
            {t('features.heading')}
            <br />
            <span className="gradient-text">{t('features.headingHighlight')}</span>
          </h2>
          <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
            {t('features.subheadline')}
          </p>
        </motion.div>

        {/* Feature cards */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              whileHover={{ y: -8, scale: 1.02 }}
              className="group relative glass-card p-8 overflow-hidden cursor-pointer"
            >
              {/* Hover gradient background */}
              <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 
                            group-hover:opacity-5 transition-opacity duration-500`} />
              
              {/* Icon */}
              <div className={`inline-flex p-3 rounded-xl ${feature.bgColor} mb-4 
                            group-hover:scale-110 transition-transform duration-300`}>
                <feature.icon className={`w-6 h-6 bg-gradient-to-r ${feature.color} 
                                        bg-clip-text text-transparent`} 
                             style={{ color: feature.color.includes('violet') ? '#8b5cf6' : 
                                     feature.color.includes('amber') ? '#f59e0b' :
                                     feature.color.includes('cyan') ? '#06b6d4' :
                                     feature.color.includes('yellow') ? '#eab308' :
                                     feature.color.includes('emerald') ? '#10b981' : '#f43f5e' }} />
              </div>

              {/* Content */}
              <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-2 
                           group-hover:text-primary-600 dark:group-hover:text-primary-400 
                           transition-colors duration-300">
                {feature.title}
              </h3>
              <p className="text-neutral-600 dark:text-neutral-400 leading-relaxed">
                {feature.description}
              </p>

              {/* Animated border on hover */}
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r 
                            from-primary-500 to-accent-500 transform scale-x-0 
                            group-hover:scale-x-100 transition-transform duration-300 origin-left" />
            </motion.div>
          ))}
        </motion.div>

        {/* Bottom stats */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="mt-20 glass-card p-8 lg:p-12"
        >
          <div className="grid md:grid-cols-4 gap-8 text-center">
            {[
              { icon: Brain, value: t('features.stats.neuralNetwork'), label: t('features.stats.aiPowered') },
              { icon: Zap, value: t('features.stats.responseTime'), label: t('features.stats.responseTimeLabel') },
              { icon: Globe, value: t('features.stats.languages'), label: t('features.stats.multilingual') },
              { icon: CheckCircle2, value: t('features.stats.uptime'), label: t('features.stats.uptimeLabel') }
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="flex flex-col items-center"
              >
                <div className="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-xl mb-3">
                  <stat.icon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                </div>
                <div className="text-2xl font-bold text-neutral-900 dark:text-white mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-neutral-500 dark:text-neutral-400">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
