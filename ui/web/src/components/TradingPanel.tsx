import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, DollarSign, Zap } from 'lucide-react'
import api from '../services/api'

interface TradingPanelProps {
  marketData?: Array<{ symbol: string; price: number; change_24h: number }>;
  agentDecisions?: Array<any>;
}

export default function TradingPanel({ marketData, agentDecisions }: TradingPanelProps) {
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [analyzing, setAnalyzing] = useState(false)
  const [decision, setDecision] = useState<any>(null)

  // Update decision when agentDecisions changes
  useEffect(() => {
    if (agentDecisions && agentDecisions.length > 0) {
      const latestForSymbol = agentDecisions.find(d => d.symbol === symbol)
      if (latestForSymbol) {
        setDecision(latestForSymbol)
      }
    }
  }, [agentDecisions, symbol])

  const handleAnalyze = async () => {
    setAnalyzing(true)

    try {
      const data = await api.analyzeSymbol({ symbol, include_debate: false })
      setDecision(data)
    } catch (error) {
      console.error('Analysis failed:', error)
      alert('Analysis failed: ' + (error as Error).message)
    } finally {
      setAnalyzing(false)
    }
  }

  // Get current price from market data
  const currentPrice = marketData?.find(m => m.symbol === symbol)?.price
  const priceChange = marketData?.find(m => m.symbol === symbol)?.change_24h

  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-5 h-5 text-green-400" />
          <span>Trading Analysis</span>
        </div>
        {currentPrice && (
          <div className="text-right">
            <div className="text-2xl font-bold">${currentPrice.toLocaleString()}</div>
            {priceChange !== undefined && (
              <div className={`text-sm flex items-center justify-end ${priceChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {priceChange >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
              </div>
            )}
          </div>
        )}
      </h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Symbol</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 focus:border-cyan-500 focus:outline-none"
            placeholder="BTC/USDT"
          />
        </div>

        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="w-full px-4 py-3 rounded-xl bg-cyan-500/20 border border-cyan-500/30 hover:bg-cyan-500/30 transition-colors disabled:opacity-50"
        >
          {analyzing ? 'Analyzing...' : 'Analyze'}
        </button>

        {decision && (
          <div className="mt-4 p-4 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium">Decision</span>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                decision.decision === 'buy' ? 'bg-green-500/20 text-green-400' :
                decision.decision === 'sell' ? 'bg-red-500/20 text-red-400' :
                'bg-gray-500/20 text-gray-400'
              }`}>
                {decision.decision?.toUpperCase()}
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Confidence</span>
                <span className="font-semibold">{(decision.confidence * 100).toFixed(0)}%</span>
              </div>

              {decision.reasoning && (
                <div className="pt-3 border-t border-white/10">
                  <p className="text-xs text-gray-400 mb-2">Bull Case:</p>
                  <p className="text-xs">{decision.reasoning.bull}</p>

                  <p className="text-xs text-gray-400 mt-2 mb-2">Bear Case:</p>
                  <p className="text-xs">{decision.reasoning.bear}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
