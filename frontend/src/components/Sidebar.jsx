import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { 
  ExternalLink, 
  DollarSign, 
  Target, 
  Clock, 
  MessageSquare,
  Play,
  Sparkles,
  ArrowRight,
  AlertCircle
} from 'lucide-react'
import useNegotiationStore from '../hooks/useNegotiationStore'
import apiService from '../services/api'
import websocketService from '../services/websocket'
import toast from 'react-hot-toast'

const Sidebar = () => {
  const [activeTab, setActiveTab] = useState('negotiate')
  const { 
    isNegotiating, 
    connectionStatus,
    formData,
    updateFormData,
    reset,
    setProduct,
    setMarketAnalysis,
    setSession,
    clearMessages
  } = useNegotiationStore()
  
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset: resetForm } = useForm({
    defaultValues: formData
  })

  const onSubmit = async (data) => {
    try {
      updateFormData(data)
      clearMessages()
      
      const response = await apiService.startNegotiation({
        product_url: data.productUrl,
        target_price: parseInt(data.targetPrice),
        max_budget: parseInt(data.maxBudget),
        approach: data.approach,
        timeline: data.timeline,
        special_requirements: data.specialRequirements || undefined
      })

      if (response.success) {
        setSession(response.session.session_id)
        setProduct(response.product_info)
        setMarketAnalysis(response.market_analysis)
        websocketService.connect(response.session.session_id)
        toast.success('Negotiation started successfully!')
      } else {
        toast.error(response.message || 'Failed to start negotiation')
      }
    } catch (error) {
      console.error('Error starting negotiation:', error)
      toast.error(error.message || 'Failed to start negotiation')
    }
  }

  const startDemo = async () => {
    try {
      clearMessages()
      
      const demoData = {
        product_url: "https://demo.olx.in/laptop-macbook-pro",
        target_price: 75000,
        max_budget: 85000,
        approach: "diplomatic",
        timeline: "flexible",
        special_requirements: "Demo negotiation session"
      }

      const response = await apiService.startDemoNegotiation(demoData)

      if (response.success) {
        setSession(response.session.session_id)
        setProduct(response.product_info)
        setMarketAnalysis(response.market_analysis)
        websocketService.connect(response.session.session_id)
        toast.success('Demo negotiation started!')
      } else {
        toast.error('Failed to start demo')
      }
    } catch (error) {
      console.error('Error starting demo:', error)
      toast.error('Failed to start demo negotiation')
    }
  }

  const handleReset = () => {
    if (window.confirm('Are you sure you want to reset the current session?')) {
      websocketService.disconnect()
      reset()
      resetForm()
      toast.success('Session reset successfully')
    }
  }

  const tabs = [
    { id: 'negotiate', label: 'Start Negotiation', icon: Play },
    { id: 'demo', label: 'Try Demo', icon: Sparkles },
  ]

  return (
    <div className="w-96 bg-gradient-to-b from-dark-800 to-dark-900 text-white flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
            <Target className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-semibold text-lg">Control Panel</h2>
            <p className="text-gray-400 text-sm">Configure your negotiation</p>
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-2 text-sm">
          <div className={`w-2 h-2 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' :
            connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
            connectionStatus === 'error' ? 'bg-red-500' :
            'bg-gray-500'
          }`} />
          <span className="capitalize">{connectionStatus}</span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-700">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-primary-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-700'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </div>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        <AnimatePresence mode="wait">
          {activeTab === 'negotiate' && (
            <motion.div
              key="negotiate"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="p-6"
            >
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* Product URL */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                    <ExternalLink className="w-4 h-4" />
                    Product URL
                  </label>
                  <input
                    type="url"
                    {...register('productUrl', { 
                      required: 'Product URL is required',
                      pattern: {
                        value: /^https?:\/\/.+/,
                        message: 'Please enter a valid URL'
                      }
                    })}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-white placeholder-gray-400"
                    placeholder="https://www.olx.in/item/..."
                    disabled={isNegotiating}
                  />
                  {errors.productUrl && (
                    <p className="text-red-400 text-sm mt-1 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {errors.productUrl.message}
                    </p>
                  )}
                </div>

                {/* Price Inputs */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                      <Target className="w-4 h-4" />
                      Target Price
                    </label>
                    <input
                      type="number"
                      {...register('targetPrice', { 
                        required: 'Target price is required',
                        min: { value: 1, message: 'Price must be greater than 0' }
                      })}
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-white placeholder-gray-400"
                      placeholder="₹15,000"
                      disabled={isNegotiating}
                    />
                    {errors.targetPrice && (
                      <p className="text-red-400 text-xs mt-1">{errors.targetPrice.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                      <DollarSign className="w-4 h-4" />
                      Max Budget
                    </label>
                    <input
                      type="number"
                      {...register('maxBudget', { 
                        required: 'Max budget is required',
                        min: { value: 1, message: 'Budget must be greater than 0' }
                      })}
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-white placeholder-gray-400"
                      placeholder="₹20,000"
                      disabled={isNegotiating}
                    />
                    {errors.maxBudget && (
                      <p className="text-red-400 text-xs mt-1">{errors.maxBudget.message}</p>
                    )}
                  </div>
                </div>

                {/* Approach */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" />
                    Negotiation Approach
                  </label>
                  <select
                    {...register('approach')}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-white"
                    disabled={isNegotiating}
                  >
                    <option value="diplomatic">Diplomatic - Polite and professional</option>
                    <option value="assertive">Assertive - Direct and confident</option>
                    <option value="considerate">Considerate - Patient and understanding</option>
                  </select>
                </div>

                {/* Timeline */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Purchase Timeline
                  </label>
                  <select
                    {...register('timeline')}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-white"
                    disabled={isNegotiating}
                  >
                    <option value="flexible">Flexible - No rush</option>
                    <option value="week">Within a week</option>
                    <option value="urgent">Urgent - ASAP</option>
                  </select>
                </div>

                {/* Special Requirements */}
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Special Requirements (Optional)
                  </label>
                  <textarea
                    {...register('specialRequirements')}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-white placeholder-gray-400 resize-none"
                    rows={3}
                    placeholder="Any specific requirements or preferences..."
                    disabled={isNegotiating}
                  />
                </div>

                {/* Action Buttons */}
                <div className="space-y-3">
                  <motion.button
                    type="submit"
                    disabled={isSubmitting || isNegotiating}
                    className={`w-full btn-primary flex items-center justify-center gap-2 ${
                      (isSubmitting || isNegotiating) ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Starting...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        Start Negotiation
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </motion.button>

                  {isNegotiating && (
                    <motion.button
                      type="button"
                      onClick={handleReset}
                      className="w-full btn-secondary text-red-600 hover:text-red-700"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      Reset Session
                    </motion.button>
                  )}
                </div>
              </form>
            </motion.div>
          )}

          {activeTab === 'demo' && (
            <motion.div
              key="demo"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="p-6"
            >
              <div className="text-center space-y-6">
                <div className="w-20 h-20 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center mx-auto">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
                
                <div>
                  <h3 className="text-xl font-semibold mb-2">Try Demo Mode</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    Experience NegotiBot AI with a simulated negotiation session. 
                    Perfect for understanding how the system works without using real product URLs.
                  </p>
                </div>

                <div className="bg-gray-800 rounded-lg p-4 text-left">
                  <h4 className="font-medium text-primary-400 mb-3">Demo Features:</h4>
                  <ul className="text-sm text-gray-300 space-y-2">
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary-500 rounded-full" />
                      Realistic negotiation simulation
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary-500 rounded-full" />
                      AI-powered response generation
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary-500 rounded-full" />
                      Market analysis insights
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary-500 rounded-full" />
                      Real-time chat interface
                    </li>
                  </ul>
                </div>

                <motion.button
                  onClick={startDemo}
                  disabled={isNegotiating || isSubmitting}
                  className={`w-full btn-primary flex items-center justify-center gap-2 ${
                    (isNegotiating || isSubmitting) ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Sparkles className="w-4 h-4" />
                  Start Demo Negotiation
                  <ArrowRight className="w-4 h-4" />
                </motion.button>

                {isNegotiating && (
                  <motion.button
                    onClick={handleReset}
                    className="w-full btn-secondary text-red-400 hover:text-red-300"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    Stop Demo
                  </motion.button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default Sidebar