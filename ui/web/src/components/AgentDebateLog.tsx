import { MessageSquare, TrendingUp, TrendingDown, Search } from 'lucide-react'

const mockDebate = [
  { agent: 'researcher', text: 'Analyzing BTC market data...', time: '2 min ago' },
  { agent: 'bull', text: 'Strong momentum indicators, RSI at 65', time: '1 min ago' },
  { agent: 'bear', text: 'Resistance at $96k, potential pullback', time: '1 min ago' },
  { agent: 'risk', text: 'Position size approved, stop loss at -1.5%', time: '30 sec ago' },
]

export default function AgentDebateLog() {
  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
        <MessageSquare className="w-5 h-5 text-purple-400" />
        <span>Agent Debate Log</span>
      </h3>

      <div className="space-y-3 max-h-80 overflow-y-auto">
        {mockDebate.map((item, i) => (
          <div key={i} className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-start space-x-3">
              <div className={`p-2 rounded-lg ${
                item.agent === 'bull' ? 'bg-green-500/20' :
                item.agent === 'bear' ? 'bg-red-500/20' :
                item.agent === 'researcher' ? 'bg-purple-500/20' :
                'bg-blue-500/20'
              }`}>
                {item.agent === 'bull' && <TrendingUp className="w-4 h-4 text-green-400" />}
                {item.agent === 'bear' && <TrendingDown className="w-4 h-4 text-red-400" />}
                {item.agent === 'researcher' && <Search className="w-4 h-4 text-purple-400" />}
                {item.agent === 'risk' && <MessageSquare className="w-4 h-4 text-blue-400" />}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold capitalize">{item.agent}</span>
                  <span className="text-xs text-gray-400">{item.time}</span>
                </div>
                <p className="text-sm text-gray-300">{item.text}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
