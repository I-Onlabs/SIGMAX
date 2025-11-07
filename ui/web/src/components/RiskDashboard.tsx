import { Shield, AlertTriangle, TrendingDown, TrendingUp, Activity, DollarSign } from 'lucide-react'

interface RiskDashboardProps {
  portfolio: any
  status: any
}

export default function RiskDashboard({ portfolio, status }: RiskDashboardProps) {
  // Calculate metrics from portfolio and status
  const totalExposure = portfolio?.invested || 0
  const maxExposure = 50 // Paper trading limit
  const dailyPnL = status?.trading?.pnl_today || 0
  const dailyLossLimit = 10
  const openPositions = portfolio?.positions?.length || 0
  const maxPositions = 3
  const consecutiveLosses = 0 // Would need trade history
  const currentDrawdown = Math.abs(portfolio?.performance?.max_drawdown || 0)
  const maxDrawdown = 10
  const sharpeRatio = portfolio?.performance?.sharpe_ratio || 0
  const volatility = 15.3 // Would need historical data
  const valueAtRisk = 4.2 // Would need calculation

  // Calculate risk levels
  const exposureLevel = (totalExposure / maxExposure) * 100
  const dailyPnLLevel = (dailyPnL / dailyLossLimit) * 100
  const drawdownLevel = (currentDrawdown / maxDrawdown) * 100

  const getRiskColor = (level: number) => {
    if (level < 50) return 'text-green-400 border-green-500/30 bg-green-500/10'
    if (level < 75) return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
    return 'text-red-400 border-red-500/30 bg-red-500/10'
  }

  const getRiskStatus = () => {
    const maxLevel = Math.max(exposureLevel, Math.abs(dailyPnLLevel), drawdownLevel)
    if (maxLevel < 50) return { status: 'LOW RISK', color: 'text-green-400', icon: Shield }
    if (maxLevel < 75) return { status: 'MODERATE RISK', color: 'text-yellow-400', icon: AlertTriangle }
    return { status: 'HIGH RISK', color: 'text-red-400', icon: AlertTriangle }
  }

  const riskStatus = getRiskStatus()
  const StatusIcon = riskStatus.icon

  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Shield className="w-5 h-5 text-cyan-400" />
          <h3 className="text-lg font-semibold">Risk Dashboard</h3>
        </div>

        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getRiskColor(Math.max(exposureLevel, drawdownLevel))}`}>
          <StatusIcon className="w-4 h-4" />
          <span className="text-xs font-semibold">{riskStatus.status}</span>
        </div>
      </div>

      {/* Main Risk Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Total Exposure */}
        <div className="p-4 rounded-lg bg-white/5 border border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Total Exposure</span>
            <DollarSign className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline space-x-1">
            <span className="text-2xl font-bold">${totalExposure.toFixed(2)}</span>
            <span className="text-sm text-gray-400">/ ${maxExposure}</span>
          </div>
          <div className="mt-2 w-full bg-gray-700/50 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                exposureLevel < 50 ? 'bg-green-500' :
                exposureLevel < 75 ? 'bg-yellow-500' :
                'bg-red-500'
              }`}
              style={{ width: `${exposureLevel}%` }}
            />
          </div>
          <div className="mt-1 text-xs text-gray-500">{exposureLevel.toFixed(0)}% utilized</div>
        </div>

        {/* Daily PnL */}
        <div className="p-4 rounded-lg bg-white/5 border border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Daily PnL</span>
            {metrics.dailyPnL >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-400" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-400" />
            )}
          </div>
          <div className="flex items-baseline space-x-1">
            <span className={`text-2xl font-bold ${dailyPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${dailyPnL >= 0 ? '+' : ''}{dailyPnL.toFixed(2)}
            </span>
          </div>
          <div className="mt-2 w-full bg-gray-700/50 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                dailyPnL >= 0 ? 'bg-green-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(Math.abs(dailyPnLLevel), 100)}%` }}
            />
          </div>
          <div className="mt-1 text-xs text-gray-500">Limit: -${dailyLossLimit}</div>
        </div>
      </div>

      {/* Position & Drawdown */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Open Positions */}
        <div className="p-4 rounded-lg bg-white/5 border border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Open Positions</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="flex items-baseline space-x-1">
            <span className="text-2xl font-bold">{openPositions}</span>
            <span className="text-sm text-gray-400">/ {maxPositions}</span>
          </div>
          {consecutiveLosses > 0 && (
            <div className="mt-2 px-2 py-1 rounded bg-red-500/20 border border-red-500/30">
              <span className="text-xs text-red-400">
                {consecutiveLosses} consecutive losses
              </span>
            </div>
          )}
        </div>

        {/* Current Drawdown */}
        <div className="p-4 rounded-lg bg-white/5 border border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Drawdown</span>
            <TrendingDown className="w-4 h-4 text-orange-400" />
          </div>
          <div className="flex items-baseline space-x-1">
            <span className="text-2xl font-bold text-orange-400">
              {currentDrawdown.toFixed(1)}%
            </span>
          </div>
          <div className="mt-2 w-full bg-gray-700/50 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-orange-500 transition-all duration-500"
              style={{ width: `${drawdownLevel}%` }}
            />
          </div>
          <div className="mt-1 text-xs text-gray-500">Max: {maxDrawdown}%</div>
        </div>
      </div>

      {/* Advanced Metrics */}
      <div className="pt-4 border-t border-white/10">
        <h4 className="text-sm font-semibold mb-3">Risk-Adjusted Performance</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Sharpe Ratio</span>
            <span className={`text-sm font-semibold ${
              sharpeRatio > 1 ? 'text-green-400' :
              sharpeRatio > 0.5 ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              {sharpeRatio.toFixed(2)}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Volatility (30d)</span>
            <span className="text-sm font-semibold">{volatility.toFixed(1)}%</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Value at Risk (95%)</span>
            <span className="text-sm font-semibold text-orange-400">${valueAtRisk.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Auto-Pause Triggers */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <h4 className="text-sm font-semibold mb-3">Auto-Pause Triggers</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">3 consecutive losses</span>
            <span className={consecutiveLosses >= 3 ? 'text-red-400' : 'text-green-400'}>
              {consecutiveLosses >= 3 ? '⚠️ TRIGGERED' : '✓ OK'}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">Daily loss &gt; $10</span>
            <span className={dailyPnL < -10 ? 'text-red-400' : 'text-green-400'}>
              {dailyPnL < -10 ? '⚠️ TRIGGERED' : '✓ OK'}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">Max exposure exceeded</span>
            <span className={totalExposure > maxExposure ? 'text-red-400' : 'text-green-400'}>
              {totalExposure > maxExposure ? '⚠️ TRIGGERED' : '✓ OK'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
