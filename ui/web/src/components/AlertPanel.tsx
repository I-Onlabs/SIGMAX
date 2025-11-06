import { useState, useEffect } from 'react'
import { AlertTriangle, Info, AlertCircle, XCircle, X, Bell, BellOff } from 'lucide-react'

interface Alert {
  id: string
  level: 'info' | 'warning' | 'critical' | 'emergency'
  title: string
  message: string
  timestamp: string
  tags: string[]
}

export default function AlertPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [muted, setMuted] = useState(false)

  useEffect(() => {
    // Fetch recent alerts
    fetchAlerts()

    // Poll for new alerts
    const interval = setInterval(fetchAlerts, 5000)

    return () => clearInterval(interval)
  }, [])

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/alerts')
      const data = await response.json()
      setAlerts(data.alerts || [])
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
    }
  }

  const dismissAlert = (id: string) => {
    setAlerts(alerts.filter(a => a.id !== id))
  }

  const clearAll = () => {
    setAlerts([])
  }

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <Info className="w-5 h-5 text-blue-400" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />
      case 'critical':
        return <AlertCircle className="w-5 h-5 text-orange-400" />
      case 'emergency':
        return <XCircle className="w-5 h-5 text-red-400" />
      default:
        return <Info className="w-5 h-5 text-gray-400" />
    }
  }

  const getAlertStyle = (level: string) => {
    switch (level) {
      case 'info':
        return 'border-blue-500/30 bg-blue-500/10'
      case 'warning':
        return 'border-yellow-500/30 bg-yellow-500/10'
      case 'critical':
        return 'border-orange-500/30 bg-orange-500/10'
      case 'emergency':
        return 'border-red-500/30 bg-red-500/10 animate-pulse'
      default:
        return 'border-gray-500/30 bg-gray-500/10'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
    return date.toLocaleDateString()
  }

  const filteredAlerts = filter === 'all'
    ? alerts
    : alerts.filter(a => a.level === filter)

  const alertCounts = {
    all: alerts.length,
    info: alerts.filter(a => a.level === 'info').length,
    warning: alerts.filter(a => a.level === 'warning').length,
    critical: alerts.filter(a => a.level === 'critical').length,
    emergency: alerts.filter(a => a.level === 'emergency').length
  }

  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Bell className="w-5 h-5 text-cyan-400" />
            <h3 className="text-lg font-semibold">System Alerts</h3>
            {alerts.length > 0 && (
              <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">
                {alerts.length}
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setMuted(!muted)}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
            >
              {muted ? (
                <BellOff className="w-4 h-4 text-gray-400" />
              ) : (
                <Bell className="w-4 h-4 text-cyan-400" />
              )}
            </button>

            {alerts.length > 0 && (
              <button
                onClick={clearAll}
                className="px-3 py-1 text-sm rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
              >
                Clear All
              </button>
            )}
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center space-x-2 overflow-x-auto">
          {[
            { key: 'all', label: 'All' },
            { key: 'emergency', label: 'Emergency' },
            { key: 'critical', label: 'Critical' },
            { key: 'warning', label: 'Warning' },
            { key: 'info', label: 'Info' }
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-3 py-1 text-sm rounded-lg transition-colors whitespace-nowrap ${
                filter === key
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                  : 'bg-white/5 text-gray-400 hover:bg-white/10'
              }`}
            >
              {label}
              {alertCounts[key as keyof typeof alertCounts] > 0 && (
                <span className="ml-1">({alertCounts[key as keyof typeof alertCounts]})</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Alert List */}
      <div className="max-h-96 overflow-y-auto">
        {filteredAlerts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No alerts</p>
            <p className="text-sm mt-1">System operating normally</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 ${getAlertStyle(alert.level)} border-l-4 hover:bg-white/5 transition-colors`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className="mt-0.5">
                      {getAlertIcon(alert.level)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-semibold text-sm">{alert.title}</h4>
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(alert.timestamp)}
                        </span>
                      </div>

                      <p className="text-sm text-gray-300 mb-2">{alert.message}</p>

                      {alert.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {alert.tags.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 text-xs rounded bg-white/10 text-gray-400"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => dismissAlert(alert.id)}
                    className="ml-2 p-1 rounded hover:bg-white/10 transition-colors"
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Alert Stats */}
      {alerts.length > 0 && (
        <div className="p-4 border-t border-white/10 bg-white/5">
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-red-400">
                {alertCounts.emergency}
              </div>
              <div className="text-xs text-gray-400">Emergency</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-400">
                {alertCounts.critical}
              </div>
              <div className="text-xs text-gray-400">Critical</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-400">
                {alertCounts.warning}
              </div>
              <div className="text-xs text-gray-400">Warning</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-400">
                {alertCounts.info}
              </div>
              <div className="text-xs text-gray-400">Info</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
