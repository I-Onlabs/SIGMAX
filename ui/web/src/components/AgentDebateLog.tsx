import { MessageSquare, TrendingUp, TrendingDown, Search, Shield } from 'lucide-react'

interface AgentDebateLogProps {
  decisions?: Array<{
    symbol: string
    decision: string
    confidence: number
    bull_score: string
    bear_score: string
    reasoning: string
  }>
}

export default function AgentDebateLog({ decisions }: AgentDebateLogProps) {
  // Convert agent decisions to debate format
  const debates = decisions?.map((d, i) => [
    { agent: 'researcher', text: `Analyzing ${d.symbol}...`, time: `${i * 2 + 2} min ago` },
    { agent: 'bull', text: d.bull_score || 'Analyzing bullish indicators...', time: `${i * 2 + 1} min ago` },
    { agent: 'bear', text: d.bear_score || 'Analyzing bearish indicators...', time: `${i * 2 + 1} min ago` },
    { agent: 'risk', text: d.reasoning || `Decision: ${d.decision.toUpperCase()} (${(d.confidence * 100).toFixed(0)}% confidence)`, time: `${i * 2} min ago` },
  ]).flat() || []

  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
        <MessageSquare className="w-5 h-5 text-purple-400" />
        <span>Agent Debate Log</span>
      </h3>

      <div className="space-y-3 max-h-80 overflow-y-auto">
        {debates.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No agent decisions yet</p>
            <p className="text-sm mt-1">Analyze a symbol to see agent debate</p>
          </div>
        ) : (
          debates.map((item, i) => (
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
                  {item.agent === 'risk' && <Shield className="w-4 h-4 text-blue-400" />}
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
          ))
        )}
      </div>
    </div>
  )
}
