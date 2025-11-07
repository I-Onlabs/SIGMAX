import { Activity, TrendingUp, DollarSign, AlertCircle, Cpu, HardDrive } from 'lucide-react'

interface StatusPanelProps {
  status: any
  health?: {
    cpu_percent?: number
    memory_percent?: number
    disk_percent?: number
    process_count?: number
  } | null
}

export default function StatusPanel({ status, health }: StatusPanelProps) {
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

      {/* System Health */}
      {health && (
        <div className="pt-4 border-t border-white/10">
          <h4 className="text-sm font-semibold mb-3">System Health</h4>
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-3 h-3 text-cyan-400" />
                  <span className="text-xs text-gray-400">CPU</span>
                </div>
                <span className="text-xs font-semibold">{health.cpu_percent?.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-700/50 rounded-full h-1.5">
                <div
                  className={`h-full rounded-full transition-all ${
                    (health.cpu_percent || 0) > 80 ? 'bg-red-500' :
                    (health.cpu_percent || 0) > 50 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${health.cpu_percent || 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-2">
                  <HardDrive className="w-3 h-3 text-purple-400" />
                  <span className="text-xs text-gray-400">Memory</span>
                </div>
                <span className="text-xs font-semibold">{health.memory_percent?.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-700/50 rounded-full h-1.5">
                <div
                  className={`h-full rounded-full transition-all ${
                    (health.memory_percent || 0) > 80 ? 'bg-red-500' :
                    (health.memory_percent || 0) > 50 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${health.memory_percent || 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-2">
                  <HardDrive className="w-3 h-3 text-blue-400" />
                  <span className="text-xs text-gray-400">Disk</span>
                </div>
                <span className="text-xs font-semibold">{health.disk_percent?.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-700/50 rounded-full h-1.5">
                <div
                  className={`h-full rounded-full transition-all ${
                    (health.disk_percent || 0) > 80 ? 'bg-red-500' :
                    (health.disk_percent || 0) > 50 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${health.disk_percent || 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
