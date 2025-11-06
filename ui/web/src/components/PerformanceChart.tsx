import { useState, useEffect } from 'react'
import { LineChart, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react'

interface PerformanceData {
  timestamp: string
  pnl: number
  cumulative_pnl: number
  trades: number
  win_rate: number
}

interface TradingMetrics {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  total_pnl: number
  sharpe_ratio: number
  max_drawdown: number
  profit_factor: number
  current_streak: number
}

export default function PerformanceChart() {
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([])
  const [metrics, setMetrics] = useState<TradingMetrics | null>(null)
  const [timeframe, setTimeframe] = useState<string>('24h')

  useEffect(() => {
    fetchPerformanceData()
    const interval = setInterval(fetchPerformanceData, 10000)
    return () => clearInterval(interval)
  }, [timeframe])

  const fetchPerformanceData = async () => {
    try {
      const response = await fetch(`/api/performance?timeframe=${timeframe}`)
      const data = await response.json()

      setPerformanceData(data.history || [])
      setMetrics(data.metrics || null)
    } catch (error) {
      console.error('Failed to fetch performance data:', error)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`
  }

  const getStreakDisplay = (streak: number) => {
    if (streak === 0) return { text: 'No streak', color: 'text-gray-400', icon: Activity }
    if (streak > 0) return { text: `${streak} wins`, color: 'text-green-400', icon: TrendingUp }
    return { text: `${Math.abs(streak)} losses`, color: 'text-red-400', icon: TrendingDown }
  }

  const maxPnl = performanceData.length > 0
    ? Math.max(...performanceData.map(d => d.cumulative_pnl))
    : 0
  const minPnl = performanceData.length > 0
    ? Math.min(...performanceData.map(d => d.cumulative_pnl))
    : 0
  const range = maxPnl - minPnl || 1

  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <LineChart className="w-5 h-5 text-cyan-400" />
            <h3 className="text-lg font-semibold">Performance</h3>
          </div>

          {/* Timeframe Selector */}
          <div className="flex items-center space-x-1 bg-white/5 rounded-lg p-1">
            {['1h', '24h', '7d', '30d'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  timeframe === tf
                    ? 'bg-cyan-500/20 text-cyan-400'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Key Metrics */}
        {metrics && (
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Total PnL</div>
              <div className={`text-xl font-bold ${
                metrics.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatCurrency(metrics.total_pnl)}
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Win Rate</div>
              <div className="text-xl font-bold text-cyan-400">
                {formatPercent(metrics.win_rate)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {metrics.winning_trades}W / {metrics.losing_trades}L
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Sharpe Ratio</div>
              <div className={`text-xl font-bold ${
                metrics.sharpe_ratio >= 1 ? 'text-green-400' :
                metrics.sharpe_ratio >= 0 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {metrics.sharpe_ratio.toFixed(2)}
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Profit Factor</div>
              <div className={`text-xl font-bold ${
                metrics.profit_factor >= 1.5 ? 'text-green-400' :
                metrics.profit_factor >= 1 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {metrics.profit_factor.toFixed(2)}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="p-6">
        {performanceData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <LineChart className="w-16 h-16 mx-auto mb-3 opacity-30" />
              <p>No performance data yet</p>
              <p className="text-sm mt-1">Start trading to see your performance</p>
            </div>
          </div>
        ) : (
          <div className="relative h-64">
            {/* Simple line chart visualization */}
            <svg className="w-full h-full" viewBox="0 0 800 200" preserveAspectRatio="none">
              {/* Grid lines */}
              {[0, 25, 50, 75, 100].map((y) => (
                <line
                  key={y}
                  x1="0"
                  y1={y * 2}
                  x2="800"
                  y2={y * 2}
                  stroke="rgba(255,255,255,0.05)"
                  strokeWidth="1"
                />
              ))}

              {/* Zero line */}
              {minPnl < 0 && maxPnl > 0 && (
                <line
                  x1="0"
                  y1={200 - ((0 - minPnl) / range) * 200}
                  x2="800"
                  y2={200 - ((0 - minPnl) / range) * 200}
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                />
              )}

              {/* Performance line */}
              <polyline
                points={performanceData.map((d, i) => {
                  const x = (i / (performanceData.length - 1)) * 800
                  const y = 200 - ((d.cumulative_pnl - minPnl) / range) * 200
                  return `${x},${y}`
                }).join(' ')}
                fill="none"
                stroke="url(#gradient)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Gradient fill */}
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity="1" />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity="1" />
                </linearGradient>
                <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
                </linearGradient>
              </defs>

              {/* Area fill */}
              <polygon
                points={[
                  ...performanceData.map((d, i) => {
                    const x = (i / (performanceData.length - 1)) * 800
                    const y = 200 - ((d.cumulative_pnl - minPnl) / range) * 200
                    return `${x},${y}`
                  }),
                  '800,200',
                  '0,200'
                ].join(' ')}
                fill="url(#areaGradient)"
              />
            </svg>

            {/* Y-axis labels */}
            <div className="absolute top-0 left-0 h-full flex flex-col justify-between text-xs text-gray-500">
              <span>{formatCurrency(maxPnl)}</span>
              <span>{formatCurrency((maxPnl + minPnl) / 2)}</span>
              <span>{formatCurrency(minPnl)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Additional Metrics */}
      {metrics && (
        <div className="p-4 border-t border-white/10 bg-white/5">
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center space-x-3">
              <DollarSign className="w-5 h-5 text-cyan-400" />
              <div>
                <div className="text-sm text-gray-400">Max Drawdown</div>
                <div className="text-lg font-semibold text-red-400">
                  {formatCurrency(metrics.max_drawdown)}
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Activity className="w-5 h-5 text-cyan-400" />
              <div>
                <div className="text-sm text-gray-400">Total Trades</div>
                <div className="text-lg font-semibold">
                  {metrics.total_trades}
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {(() => {
                const streak = getStreakDisplay(metrics.current_streak)
                const Icon = streak.icon
                return (
                  <>
                    <Icon className={`w-5 h-5 ${streak.color}`} />
                    <div>
                      <div className="text-sm text-gray-400">Current Streak</div>
                      <div className={`text-lg font-semibold ${streak.color}`}>
                        {streak.text}
                      </div>
                    </div>
                  </>
                )
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
