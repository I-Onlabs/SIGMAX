import { useEffect, useMemo, useRef, useState } from 'react'
import { Bot, Loader2, CheckCircle2, XCircle, ShieldCheck, Play, ThumbsUp } from 'lucide-react'
import api from '../services/api'

type ChatStep = {
  ts: string
  step: string
}

type TradeProposal = {
  proposal_id: string
  symbol: string
  action: 'buy' | 'sell'
  size: number
  notional_usd: number
  mode: 'paper' | 'live'
  requires_manual_approval: boolean
  approved: boolean
  created_at: string
  rationale?: string | null
}

export default function AIChatPanel() {
  const [apiKey, setApiKey] = useState('')
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [message, setMessage] = useState('Analyze this symbol and propose a safe trade if actionable.')
  const [riskProfile, setRiskProfile] = useState<'conservative' | 'balanced' | 'aggressive'>('conservative')
  const [mode, setMode] = useState<'paper' | 'live'>('paper')
  const [requireManualApprovalLive, setRequireManualApprovalLive] = useState(true)

  const [running, setRunning] = useState(false)
  const [steps, setSteps] = useState<ChatStep[]>([])
  const [finalState, setFinalState] = useState<any>(null)
  const [decision, setDecision] = useState<any>(null)
  const [proposal, setProposal] = useState<TradeProposal | null>(null)
  const [error, setError] = useState<string | null>(null)

  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem('SIGMAX_API_KEY')
    if (saved) {
      setApiKey(saved)
      api.setApiKey(saved)
    }
  }, [])

  const canExecute = useMemo(() => {
    if (!proposal) return false
    if (proposal.requires_manual_approval && !proposal.approved) return false
    return true
  }, [proposal])

  const stop = () => {
    abortRef.current?.abort()
    abortRef.current = null
    setRunning(false)
  }

  const saveKey = () => {
    const trimmed = apiKey.trim()
    if (!trimmed) {
      localStorage.removeItem('SIGMAX_API_KEY')
      api.setApiKey('')
      return
    }
    localStorage.setItem('SIGMAX_API_KEY', trimmed)
    api.setApiKey(trimmed)
  }

  const parseFrames = (buffer: string) => {
    const frames = buffer.split('\n\n')
    return { frames: frames.slice(0, -1), rest: frames[frames.length - 1] ?? '' }
  }

  const handleFrame = (frame: string) => {
    const lines = frame.split('\n').filter(Boolean)
    const eventLine = lines.find(l => l.startsWith('event:'))
    const dataLine = lines.find(l => l.startsWith('data:'))
    const event = eventLine ? eventLine.replace('event:', '').trim() : 'message'
    const dataStr = dataLine ? dataLine.replace('data:', '').trim() : '{}'
    let data: any = {}
    try {
      data = JSON.parse(dataStr)
    } catch {
      data = { raw: dataStr }
    }

    if (event === 'step') {
      setSteps(prev => [...prev, { ts: data.timestamp || new Date().toISOString(), step: data.step || 'unknown' }])
    } else if (event === 'final') {
      setFinalState(data.state)
      setDecision(data.decision)
      setProposal(data.proposal || null)
    } else if (event === 'error') {
      setError(typeof data.error === 'string' ? data.error : JSON.stringify(data.error))
    }
  }

  const startStream = async () => {
    setError(null)
    setSteps([])
    setFinalState(null)
    setDecision(null)
    setProposal(null)

    setRunning(true)
    const controller = new AbortController()
    abortRef.current = controller

    try {
      const headers: HeadersInit = { 'Content-Type': 'application/json' }
      const key = localStorage.getItem('SIGMAX_API_KEY')
      if (key) headers['Authorization'] = `Bearer ${key}`

      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message,
          symbol,
          risk_profile: riskProfile,
          mode,
          require_manual_approval_live: requireManualApprovalLive,
        }),
        signal: controller.signal,
      })

      if (!res.ok || !res.body) {
        const text = await res.text().catch(() => '')
        throw new Error(text || `HTTP ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const { frames, rest } = parseFrames(buf)
        buf = rest
        frames.forEach(handleFrame)
      }
    } catch (e) {
      if ((e as any)?.name !== 'AbortError') {
        setError((e as Error).message)
      }
    } finally {
      setRunning(false)
      abortRef.current = null
    }
  }

  const approve = async () => {
    if (!proposal) return
    setError(null)
    try {
      const updated = await api.chatApproveProposal(proposal.proposal_id)
      setProposal(updated)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const execute = async () => {
    if (!proposal) return
    setError(null)
    try {
      await api.chatExecuteProposal(proposal.proposal_id)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
        <Bot className="w-5 h-5 text-cyan-400" />
        <span>AI Chat (Streaming)</span>
      </h3>

      <div className="space-y-3">
        <div className="grid grid-cols-1 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">API key (optional)</label>
            <div className="flex gap-2">
              <input
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Bearer token"
                className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 focus:border-cyan-500 focus:outline-none text-sm"
              />
              <button
                onClick={saveKey}
                className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-sm"
              >
                Save
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Symbol</label>
              <input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 focus:border-cyan-500 focus:outline-none text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Risk profile</label>
              <select
                value={riskProfile}
                onChange={(e) => setRiskProfile(e.target.value as any)}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 focus:border-cyan-500 focus:outline-none text-sm"
              >
                <option value="conservative">conservative</option>
                <option value="balanced">balanced</option>
                <option value="aggressive">aggressive</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Mode</label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as any)}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 focus:border-cyan-500 focus:outline-none text-sm"
              >
                <option value="paper">paper</option>
                <option value="live">live</option>
              </select>
            </div>
            <label className="flex items-center gap-2 text-xs text-gray-300 mt-6">
              <input
                type="checkbox"
                checked={requireManualApprovalLive}
                onChange={(e) => setRequireManualApprovalLive(e.target.checked)}
                className="accent-cyan-500"
                disabled={mode !== 'live'}
              />
              Require manual approval (live)
            </label>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Prompt</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 focus:border-cyan-500 focus:outline-none text-sm"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={startStream}
              disabled={running}
              className="flex-1 px-4 py-2 rounded-xl bg-cyan-500/20 border border-cyan-500/30 hover:bg-cyan-500/30 transition-colors disabled:opacity-50 text-sm"
            >
              {running ? (
                <span className="inline-flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" /> Streaming…
                </span>
              ) : (
                'Run analysis'
              )}
            </button>
            <button
              onClick={stop}
              disabled={!running}
              className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors disabled:opacity-50 text-sm"
            >
              Stop
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Step progress */}
        <div className="p-3 rounded-lg bg-white/5 border border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold">Progress</span>
            <span className="text-xs text-gray-400">{steps.length} steps</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {steps.slice(-10).map((s, i) => (
              <span key={`${s.ts}-${i}`} className="px-2 py-1 rounded-full bg-white/5 border border-white/10 text-xs">
                {s.step}
              </span>
            ))}
            {steps.length === 0 && <span className="text-xs text-gray-500">No steps yet.</span>}
          </div>
        </div>

        {/* Decision + Proposal */}
        {decision && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">Decision</span>
              <span className="text-xs text-gray-400">{decision.timestamp || ''}</span>
            </div>
            <div className="mt-2 flex items-center gap-3">
              <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm">
                {(decision.action || 'hold').toUpperCase()}
              </span>
              <span className="text-sm text-gray-300">
                Confidence: {Math.round(((decision.confidence || 0) * 100))}%
              </span>
            </div>
          </div>
        )}

        {proposal && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold inline-flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-green-400" />
                Trade proposal
              </span>
              <span className="text-xs text-gray-400">{proposal.mode}</span>
            </div>
            <div className="mt-2 text-sm text-gray-200">
              {proposal.action.toUpperCase()} {proposal.size.toFixed(6)} {proposal.symbol} (≈${proposal.notional_usd.toFixed(2)})
            </div>
            <div className="mt-2 text-xs text-gray-400 break-all">ID: {proposal.proposal_id}</div>
            <div className="mt-2 flex items-center gap-2 text-xs">
              {proposal.requires_manual_approval ? (
                proposal.approved ? (
                  <span className="inline-flex items-center gap-1 text-green-300">
                    <CheckCircle2 className="w-4 h-4" /> Approved
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-yellow-300">
                    <XCircle className="w-4 h-4" /> Approval required
                  </span>
                )
              ) : (
                <span className="inline-flex items-center gap-1 text-green-300">
                  <CheckCircle2 className="w-4 h-4" /> No approval required
                </span>
              )}
            </div>
            <div className="mt-3 flex gap-2">
              <button
                onClick={approve}
                disabled={proposal.approved || !proposal.requires_manual_approval}
                className="px-3 py-2 rounded-lg bg-green-500/15 border border-green-500/25 hover:bg-green-500/25 disabled:opacity-50 text-sm inline-flex items-center gap-2"
              >
                <ThumbsUp className="w-4 h-4" />
                Approve
              </button>
              <button
                onClick={execute}
                disabled={!canExecute}
                className="px-3 py-2 rounded-lg bg-cyan-500/20 border border-cyan-500/30 hover:bg-cyan-500/30 disabled:opacity-50 text-sm inline-flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Execute
              </button>
            </div>
          </div>
        )}

        {/* Key artifacts */}
        {finalState && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10 space-y-2">
            <div className="text-sm font-semibold">Artifacts (high-signal)</div>
            {finalState.research_summary && (
              <div>
                <div className="text-xs text-gray-400 mb-1">Research summary</div>
                <pre className="text-xs whitespace-pre-wrap text-gray-200 bg-black/20 p-2 rounded-lg border border-white/10">
                  {String(finalState.research_summary)}
                </pre>
              </div>
            )}
            {finalState.validation_score !== undefined && (
              <div className="text-xs text-gray-300">
                Validation: {finalState.validation_passed ? 'passed' : 'failed'} (score {finalState.validation_score})
              </div>
            )}
            {finalState.risk_assessment?.summary && (
              <div>
                <div className="text-xs text-gray-400 mb-1">Risk summary</div>
                <pre className="text-xs whitespace-pre-wrap text-gray-200 bg-black/20 p-2 rounded-lg border border-white/10">
                  {String(finalState.risk_assessment.summary)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

