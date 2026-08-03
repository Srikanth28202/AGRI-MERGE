import React, { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  MessageCircle, 
  X, 
  Send, 
  Bot, 
  User, 
  Loader2,
  Sprout,
  Leaf,
  Droplets,
  AlertCircle,
  Sparkles
} from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8081'

export default function Chatbot({ isOpen: externalIsOpen, setIsOpen: externalSetIsOpen, fullPage = false, onClose = () => {} }) {
  const { t } = useTranslation()

  const quickQuestions = [
    { icon: Sprout, text: t('chatbot.quickQuestionsList.bestCrop') },
    { icon: Leaf, text: t('chatbot.quickQuestionsList.increaseFertility') },
    { icon: Droplets, text: t('chatbot.quickQuestionsList.fertilizerRice') },
    { icon: Bot, text: t('chatbot.quickQuestionsList.explainResults') },
  ]

  // Use external state if provided, otherwise use internal state
  const [internalIsOpen, setInternalIsOpen] = useState(false)
  const isOpen = externalIsOpen !== undefined ? externalIsOpen : internalIsOpen
  const setIsOpen = externalSetIsOpen || setInternalIsOpen

  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: t('chatbot.welcome')
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [apiStatus, setApiStatus] = useState(null)
  const messagesEndRef = useRef(null)

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check API status when chat opens
  useEffect(() => {
    if (isOpen) {
      checkApiStatus()
    }
  }, [isOpen])

  const checkApiStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/chat/status`)
      setApiStatus(response.data)
    } catch (error) {
      setApiStatus({ available: false, mode: 'error', error: t('chatbot.cannotConnect') })
    }
  }

  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return

    // Add user message
    const userMessage = { role: 'user', content: messageText }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Call backend API
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: messageText,
        context: ''
      })

      if (response.data.success) {
        // Add AI response
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response.data.response 
        }])
      } else {
        // Add error message
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `⚠️ ${response.data.error || t('chatbot.requestError')}` 
        }])
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `⚠️ ${t('chatbot.connectionError')}` 
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleQuickQuestion = (question) => {
    sendMessage(question)
  }

  // Determine status indicator color and message
  const getStatusIndicator = () => {
    if (!apiStatus) return { color: 'bg-gray-400', tooltip: t('chatbot.checking') }
    if (apiStatus.mode === 'ai') return { color: 'bg-green-400', tooltip: t('chatbot.aiReady') }
    if (apiStatus.mode === 'fallback') return { color: 'bg-yellow-400', tooltip: t('chatbot.usingFallback') }
    return { color: 'bg-red-400', tooltip: t('chatbot.serviceUnavailable') }
  }

  const statusIndicator = getStatusIndicator()

  const panelClasses = fullPage
    ? 'bg-white rounded-3xl shadow-2xl shadow-gray-300/40 border border-gray-200 overflow-hidden'
    : 'fixed bottom-24 right-6 z-50 w-96 max-w-[calc(100vw-3rem)] bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden'

  const messagesAreaClasses = fullPage ? 'h-[55vh] min-h-80' : 'h-80'

  return (
    <>
      {!fullPage && (
        <motion.button
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setIsOpen(!isOpen)}
          className={`fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-lg transition-all duration-300 ${
            isOpen
              ? 'bg-red-500 hover:bg-red-600 shadow-red-500/30'
              : 'bg-gradient-to-r from-green-600 to-emerald-600 hover:shadow-green-500/40'
          }`}
        >
          {isOpen ? (
            <X className="w-6 h-6 text-white" />
          ) : (
            <MessageCircle className="w-6 h-6 text-white" />
          )}
        </motion.button>
      )}

      <AnimatePresence>
        {fullPage ? (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.98 }}
            transition={{ duration: 0.3 }}
            className={panelClasses}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-4 flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-white">{t('chatbot.headerTitle')}</h3>
                <p className="text-green-100 text-xs flex items-center gap-1">
                  {apiStatus?.mode === 'ai' && (
                    <><Sparkles className="w-3 h-3" /> {t('chatbot.aiMode')}</>
                  )}
                  {apiStatus?.mode === 'fallback' && t('chatbot.fallbackMode')}
                  {!apiStatus && t('chatbot.connecting')}
                </p>
              </div>
              <div className={`w-3 h-3 rounded-full ${statusIndicator.color}`}
                   title={statusIndicator.tooltip} />
              {fullPage && (
                <button
                  onClick={onClose}
                  className="p-2 bg-white/10 hover:bg-white/20 rounded-xl text-white transition-colors"
                  aria-label={t('chatbot.closeLabel')}
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {/* API Status Warning - Only show in fallback mode */}
            {apiStatus?.mode === 'fallback' && (
              <div className="bg-amber-50 border-b border-amber-100 p-3 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                <div className="text-xs text-amber-700">
                  <p className="font-medium mb-1">{t('chatbot.fallbackTitle')}</p>
                  <p>{t('chatbot.fallbackDesc')}</p>
                  <ol className="list-decimal ml-4 mt-1 space-y-0.5">
                    <li>{t('chatbot.fallbackStep1')} <a href="https://openrouter.ai/keys" target="_blank" rel="noopener" className="underline hover:text-amber-800">openrouter.ai/keys</a></li>
                    <li>{t('chatbot.fallbackStep2')} <code className="bg-amber-100 px-1 rounded">OPENROUTER_API_KEY=your_key</code></li>
                    <li>{t('chatbot.fallbackStep3')}</li>
                  </ol>
                </div>
              </div>
            )}

            {/* Messages */}
            <div className={`${messagesAreaClasses} overflow-y-auto p-4 space-y-4 bg-gray-50`}>
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user'
                      ? 'bg-green-600'
                      : 'bg-gray-200'
                  }`}>
                    {message.role === 'user' ? (
                      <User className="w-4 h-4 text-white" />
                    ) : (
                      <Bot className="w-4 h-4 text-gray-600" />
                    )}
                  </div>
                  <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                    message.role === 'user'
                      ? 'bg-green-600 text-white rounded-br-md'
                      : 'bg-white text-gray-800 rounded-bl-md shadow-sm border border-gray-100'
                  }`}>
                    {message.content}
                  </div>
                </motion.div>
              ))}

              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3"
                >
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-gray-100">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Questions */}
            {messages.length < 3 && (
              <div className="px-4 py-3 bg-white border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-2">{t('chatbot.quickQuestions')}</p>
                <div className="flex flex-wrap gap-2">
                  {quickQuestions.map((q, idx) => (
                    <motion.button
                      key={idx}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleQuickQuestion(q.text)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-xs font-medium hover:bg-green-100 transition-colors"
                    >
                      <q.icon className="w-3 h-3" />
                      {q.text}
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 bg-white border-t border-gray-100">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={t('chatbot.placeholder')}
                  disabled={isLoading}
                  className="flex-1 px-4 py-2.5 bg-gray-100 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all disabled:opacity-50"
                />
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="p-2.5 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-green-500/30 transition-all"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </motion.button>
              </div>
            </form>
          </motion.div>
        ) : (
          isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className={panelClasses}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-4 flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-white">{t('chatbot.headerTitle')}</h3>
                <p className="text-green-100 text-xs flex items-center gap-1">
                  {apiStatus?.mode === 'ai' && (
                    <><Sparkles className="w-3 h-3" /> {t('chatbot.aiMode')}</>
                  )}
                  {apiStatus?.mode === 'fallback' && t('chatbot.fallbackMode')}
                  {!apiStatus && t('chatbot.connecting')}
                </p>
              </div>
              <div className={`w-3 h-3 rounded-full ${statusIndicator.color}`}
                   title={statusIndicator.tooltip} />
            </div>

            {/* API Status Warning - Only show in fallback mode */}
            {apiStatus?.mode === 'fallback' && (
              <div className="bg-amber-50 border-b border-amber-100 p-3 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                <div className="text-xs text-amber-700">
                  <p className="font-medium mb-1">{t('chatbot.fallbackTitle')}</p>
                  <p>{t('chatbot.fallbackDesc')}</p>
                  <ol className="list-decimal ml-4 mt-1 space-y-0.5">
                    <li>{t('chatbot.fallbackStep1')} <a href="https://openrouter.ai/keys" target="_blank" rel="noopener" className="underline hover:text-amber-800">openrouter.ai/keys</a></li>
                    <li>{t('chatbot.fallbackStep2')} <code className="bg-amber-100 px-1 rounded">OPENROUTER_API_KEY=your_key</code></li>
                    <li>{t('chatbot.fallbackStep3')}</li>
                  </ol>
                </div>
              </div>
            )}

            {/* Messages */}
            <div className={`${messagesAreaClasses} overflow-y-auto p-4 space-y-4 bg-gray-50`}>
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user'
                      ? 'bg-green-600'
                      : 'bg-gray-200'
                  }`}>
                    {message.role === 'user' ? (
                      <User className="w-4 h-4 text-white" />
                    ) : (
                      <Bot className="w-4 h-4 text-gray-600" />
                    )}
                  </div>
                  <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                    message.role === 'user'
                      ? 'bg-green-600 text-white rounded-br-md'
                      : 'bg-white text-gray-800 rounded-bl-md shadow-sm border border-gray-100'
                  }`}>
                    {message.content}
                  </div>
                </motion.div>
              ))}

              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3"
                >
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-gray-100">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Questions */}
            {messages.length < 3 && (
              <div className="px-4 py-3 bg-white border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-2">{t('chatbot.quickQuestions')}</p>
                <div className="flex flex-wrap gap-2">
                  {quickQuestions.map((q, idx) => (
                    <motion.button
                      key={idx}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleQuickQuestion(q.text)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-xs font-medium hover:bg-green-100 transition-colors"
                    >
                      <q.icon className="w-3 h-3" />
                      {q.text}
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 bg-white border-t border-gray-100">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={t('chatbot.placeholder')}
                  disabled={isLoading}
                  className="flex-1 px-4 py-2.5 bg-gray-100 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all disabled:opacity-50"
                />
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="p-2.5 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-green-500/30 transition-all"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </motion.button>
              </div>
            </form>
          </motion.div>
          )
        )}
      </AnimatePresence>
    </>
  )
}

