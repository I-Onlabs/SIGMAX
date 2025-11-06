import { Activity, TrendingUp, DollarSign, AlertCircle } from 'lucide-react'

export default function StatusPanel({ status }: { status: any }) {
  if (!status) {
    return (
      <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6">
        <p className="text-gray-400">Loading status...</p>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6 space-y-4">
      <h3 className="text-lg font-semibold mb-4">System Status</h3>

      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span className="text-sm">Mode</span>
          </div>
          <span className="text-sm font-semibold">{status.mode || 'Paper'}</span>
        </div>

        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-green-400" />
            <span className="text-sm">PnL Today</span>
          </div>
          <span className="text-sm font-semibold text-green-400">
            +${status.trading?.pnl_today?.toFixed(2) || '0.00'}
          </span>
        </div>

        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
          <div className="flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-blue-400" />
            <span className="text-sm">Open Positions</span>
          </div>
          <span className="text-sm font-semibold">{status.trading?.open_positions || 0}</span>
        </div>

        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-yellow-400" />
            <span className="text-sm">Trades Today</span>
          </div>
          <span className="text-sm font-semibold">{status.trading?.trades_today || 0}</span>
        </div>
      </div>

      <div className="pt-4 border-t border-white/10">
        <h4 className="text-sm font-semibold mb-2">Active Agents</h4>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(status.agents || {}).map(([name, state]) => (
            <div key={name} className="flex items-center space-x-2 text-xs">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span className="capitalize">{name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
