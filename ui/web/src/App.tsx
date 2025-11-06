import { useState, useEffect } from 'react'
import { Activity, Brain, TrendingUp, Shield, Zap } from 'lucide-react'
import NeuralSwarm3D from './components/NeuralSwarm3D'
import StatusPanel from './components/StatusPanel'
import TradingPanel from './components/TradingPanel'
import AgentDebateLog from './components/AgentDebateLog'
import QuantumCircuit from './components/QuantumCircuit'
import RiskDashboard from './components/RiskDashboard'

function App() {
  const [status, setStatus] = useState<any>(null)
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    // Fetch initial status
    fetch('/api/status')
      .then(res => res.json())
      .then(data => setStatus(data))
      .catch(err => console.error('Failed to fetch status:', err))

    // Connect to WebSocket
    const websocket = new WebSocket('ws://localhost:8000/ws')

    websocket.onopen = () => {
      console.log('WebSocket connected')
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)

      if (data.type === 'status_update') {
        // Update status in real-time
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 text-white">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-lg bg-white/5">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                  SIGMAX
                </h1>
                <p className="text-xs text-gray-400">Neural Cockpit</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 backdrop-blur">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-sm">Operational</span>
              </div>

              <div className="flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 backdrop-blur">
                <Activity className="w-4 h-4 text-cyan-400" />
                <span className="text-sm">Paper Mode</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* 3D Agent Swarm */}
            <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 overflow-hidden">
              <div className="p-4 border-b border-white/10">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Zap className="w-5 h-5 text-cyan-400" />
                    <h2 className="text-lg font-semibold">Neural Agent Swarm</h2>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-400">
                    <span>6 agents active</span>
                  </div>
                </div>
              </div>
              <div className="h-96">
                <NeuralSwarm3D />
              </div>
            </div>

            {/* Trading Panel */}
            <TradingPanel />

            {/* Agent Debate Log */}
            <AgentDebateLog />
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Status Panel */}
            <StatusPanel status={status} />

            {/* Risk Dashboard */}
            <RiskDashboard />

            {/* Quantum Circuit */}
            <QuantumCircuit />

            {/* Quick Actions */}
            <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
                <Shield className="w-5 h-5 text-green-400" />
                <span>Quick Actions</span>
              </h3>
              <div className="space-y-3">
                <button className="w-full px-4 py-3 rounded-xl bg-green-500/20 border border-green-500/30 hover:bg-green-500/30 transition-colors">
                  <TrendingUp className="w-4 h-4 inline mr-2" />
                  Start Trading
                </button>
                <button className="w-full px-4 py-3 rounded-xl bg-yellow-500/20 border border-yellow-500/30 hover:bg-yellow-500/30 transition-colors">
                  Pause
                </button>
                <button className="w-full px-4 py-3 rounded-xl bg-red-500/20 border border-red-500/30 hover:bg-red-500/30 transition-colors">
                  Emergency Stop
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
