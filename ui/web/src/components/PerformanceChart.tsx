import { useState, useEffect } from 'react'
import { LineChart, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react'

interface PortfolioUpdate {
  total_value?: number
  cash?: number
  invested?: number
  positions?: Array<any>
  performance?: {
    total_return?: number
    daily_return?: number
    sharpe_ratio?: number
    max_drawdown?: number
  }
  timestamp?: string
}

interface PerformanceChartProps {
  portfolio: PortfolioUpdate | null
}

export default function PerformanceChart({ portfolio }: PerformanceChartProps) {
  const [timeframe, setTimeframe] = useState<string>('24h')
  const [performanceHistory, setPerformanceHistory] = useState<Array<{ timestamp: string, value: number }>>([])

  // Track portfolio value over time
  useEffect(() => {
    if (portfolio && portfolio.total_value) {
      setPerformanceHistory(prev => {
        const newHistory = [
          ...prev,
          {
            timestamp: portfolio.timestamp || new Date().toISOString(),
            value: portfolio.total_value || 0
          }
        ]
        // Keep only last 100 data points
        return newHistory.slice(-100)
      })
    }
  }, [portfolio])

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

  // Calculate metrics from portfolio
  const totalPnl = portfolio ? (portfolio.total_value || 50) - 50 : 0 // Assume $50 starting capital
  const sharpeRatio = portfolio?.performance?.sharpe_ratio || 0
  const maxDrawdown = portfolio?.performance?.max_drawdown || 0

  const maxVal = performanceHistory.length > 0
    ? Math.max(...performanceHistory.map(d => d.value))
    : 50
  const minVal = performanceHistory.length > 0
    ? Math.min(...performanceHistory.map(d => d.value))
    : 50
  const range = maxVal - minVal || 1

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
        {portfolio && (
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Total PnL</div>
              <div className={`text-xl font-bold ${
                totalPnl >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatCurrency(totalPnl)}
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Total Value</div>
              <div className="text-xl font-bold text-cyan-400">
                {formatCurrency(portfolio.total_value || 50)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Cash: {formatCurrency(portfolio.cash || 0)}
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Sharpe Ratio</div>
              <div className={`text-xl font-bold ${
                sharpeRatio >= 1 ? 'text-green-400' :
                sharpeRatio >= 0 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {sharpeRatio.toFixed(2)}
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Daily Return</div>
              <div className={`text-xl font-bold ${
                (portfolio.performance?.daily_return || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatPercent(portfolio.performance?.daily_return || 0)}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="p-6">
        {performanceHistory.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <LineChart className="w-16 h-16 mx-auto mb-3 opacity-30" />
              <p>No performance data yet</p>
              <p className="text-sm mt-1">Tracking portfolio value in real-time</p>
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

              {/* Starting capital line */}
              <line
                x1="0"
                y1={200 - ((50 - minVal) / range) * 200}
                x2="800"
                y2={200 - ((50 - minVal) / range) * 200}
                stroke="rgba(255,255,255,0.2)"
                strokeWidth="2"
                strokeDasharray="5,5"
              />

              {/* Performance line */}
              <polyline
                points={performanceHistory.map((d, i) => {
                  const x = (i / (performanceHistory.length - 1)) * 800
                  const y = 200 - ((d.value - minVal) / range) * 200
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
                  ...performanceHistory.map((d, i) => {
                    const x = (i / (performanceHistory.length - 1)) * 800
                    const y = 200 - ((d.value - minVal) / range) * 200
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
              <span>{formatCurrency(maxVal)}</span>
              <span>{formatCurrency((maxVal + minVal) / 2)}</span>
              <span>{formatCurrency(minVal)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Additional Metrics */}
      {portfolio && (
        <div className="p-4 border-t border-white/10 bg-white/5">
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center space-x-3">
              <DollarSign className="w-5 h-5 text-cyan-400" />
              <div>
                <div className="text-sm text-gray-400">Max Drawdown</div>
                <div className="text-lg font-semibold text-red-400">
                  {maxDrawdown.toFixed(2)}%
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Activity className="w-5 h-5 text-cyan-400" />
              <div>
                <div className="text-sm text-gray-400">Positions</div>
                <div className="text-lg font-semibold">
                  {portfolio.positions?.length || 0}
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {totalPnl >= 0 ? (
                <TrendingUp className="w-5 h-5 text-green-400" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-400" />
              )}
              <div>
                <div className="text-sm text-gray-400">Total Return</div>
                <div className={`text-lg font-semibold ${totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {formatPercent((portfolio.performance?.total_return || 0))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
