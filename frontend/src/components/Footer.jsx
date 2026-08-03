import React from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Sprout, Github, Twitter, Mail, Heart } from 'lucide-react'

export default function Footer() {
  const { t } = useTranslation()

  const socialLinks = [
    { icon: Github, href: '#', label: t('footer.social.github') },
    { icon: Twitter, href: '#', label: t('footer.social.twitter') },
    { icon: Mail, href: '#', label: t('footer.social.email') }
  ]
  return (
    <footer className="relative py-16 lg:py-20 section-padding border-t border-neutral-200 dark:border-neutral-800">
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-5 gap-12 lg:gap-8">
          {/* Brand */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="flex items-center gap-2 mb-4"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-primary-500 to-accent-500 rounded-xl blur-sm opacity-60" />
                <div className="relative p-2 bg-gradient-to-r from-primary-500 to-accent-500 rounded-xl">
                  <Sprout className="w-5 h-5 text-white" />
                </div>
              </div>
              <span className="text-xl font-bold text-neutral-800 dark:text-white">
                {t('footer.brand')}<span className="gradient-text">{t('footer.brandHighlight')}</span>
              </span>
            </motion.div>
            <p className="text-neutral-600 dark:text-neutral-400 mb-6 max-w-sm leading-relaxed">
              {t('footer.description')}
            </p>
            <div className="flex items-center gap-3">
              {socialLinks.map((social, index) => (
                <motion.a
                  key={index}
                  href={social.href}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-2.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 
                           rounded-xl hover:bg-primary-50 dark:hover:bg-primary-900/30 
                           hover:text-primary-600 dark:hover:text-primary-400 transition-all"
                  aria-label={social.label}
                >
                  <social.icon className="w-5 h-5" />
                </motion.a>
              ))}
            </div>
          </div>

          {/* Links */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-8 lg:col-span-3">
            {Object.entries({
              product: [
                { name: t('footer.features'), to: '/#features' },
                { name: t('footer.prediction'), to: '/predict' },
                { name: t('footer.aiChatbot'), to: '/chat' },
                { name: t('footer.apiDocs'), href: 'http://127.0.0.1:8081/docs' }
              ],
              company: [
                { name: t('footer.about'), href: '#' },
                { name: t('footer.blog'), href: '#' },
                { name: t('footer.careers'), href: '#' },
                { name: t('footer.contact'), href: '#' }
              ],
              resources: [
                { name: t('footer.documentation'), href: 'http://127.0.0.1:8081/docs' },
                { name: t('footer.helpCenter'), href: '#' },
                { name: t('footer.community'), href: '#' },
                { name: t('footer.privacyPolicy'), href: '#' }
              ]
            }).map(([category, links], categoryIndex) => (
              <motion.div
                key={category}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: categoryIndex * 0.1 }}
              >
                <h4 className="font-semibold text-neutral-900 dark:text-white capitalize mb-4">
                  {t('footer.' + category)}
                </h4>
                <ul className="space-y-3">
                  {links.map((link, index) => (
                    <li key={index}>
                      {link.to ? (
                        <Link
                          to={link.to}
                          className="text-neutral-600 dark:text-neutral-400 hover:text-primary-600 
                                   dark:hover:text-primary-400 transition-colors text-sm"
                        >
                          {link.name}
                        </Link>
                      ) : (
                        <a
                          href={link.href}
                          className="text-neutral-600 dark:text-neutral-400 hover:text-primary-600 
                                   dark:hover:text-primary-400 transition-colors text-sm"
                        >
                          {link.name}
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Bottom bar */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-16 pt-8 border-t border-neutral-200 dark:border-neutral-800 
                    flex flex-col sm:flex-row items-center justify-between gap-4"
        >
          <p className="text-sm text-neutral-500 dark:text-neutral-400 text-center sm:text-left">
            {t('footer.copyright', { year: new Date().getFullYear() })}
          </p>
          <p className="flex items-center gap-1 text-sm text-neutral-500 dark:text-neutral-400">
            {t('footer.madeWith')} <Heart className="w-4 h-4 text-red-500 fill-red-500" /> {t('footer.forFarmers')}
          </p>
        </motion.div>
      </div>
    </footer>
  )
}
